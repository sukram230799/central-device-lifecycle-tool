import json
from uuid import uuid4

from aiohttp import web, web_ws
from Communication.CommunicationHandler import CommunicationHandler
from Communication.WebsocketCommunicationHandler import \
    WebsocketCommunicationHandler

from Firmware.CentralFirmwareUpgrade import CentralFirmwareUpgrade
from Firmware.FirmwareExcelHandler import FirmwareExcelHandler
from Firmware.FirmwareUpgradeHandler import FirmwareUpgradeHandler


class FWWebsocketHandler():

    def __init__(self,
                 cfu: CentralFirmwareUpgrade,
                 excel_dir: str | None = None,
                 download_url: str | None = None,
                 excel_persist: bool = False) -> None:
        self.cfu = cfu
        self.excel_dir = excel_dir
        self.download_url = download_url
        self.excel_persist = excel_persist
        pass

    async def websocket_handler(self, request):
        id = uuid4()
        print(f'{id} Websocket connection starting')
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        print(f'{id} Websocket connection ready')

        ws.remote_address = request._transport_peername  # type: ignore
        ws.id = id  # type: ignore

        session_parameters = {
            'remote_address': request._transport_peername,
            'id': id,
            'excel_filename': None,
            'download_url': self.download_url
        }

        comm_handler = WebsocketCommunicationHandler(websocket=ws)
        excel_handler = None
        if self.excel_dir:
            excel_handler = FirmwareExcelHandler(self.excel_dir)
            session_parameters['excel_dir'] = '/out'
            session_parameters['excel_filename'] = excel_handler.get_filename()

        client_handler = FirmwareUpgradeHandler(self.cfu,
                                                comm_handler=comm_handler,
                                                excel_handler=excel_handler)

        async for msg in ws:
            # print(msg)
            if msg.type == web_ws.WSMsgType.TEXT:
                # print(msg.data)
                if msg.data == 'close':
                    await ws.close()
                else:
                    await handle_fw_websocket(
                        websocket=ws,
                        message=msg.data,
                        client_handler=client_handler,
                        comm_handler=comm_handler,
                        session_parameters=session_parameters)

        if excel_handler:
            excel_handler.close()
            if self.excel_persist:
                excel_handler.delete()
        print(f'{id} Websocket connection closed')
        return ws


async def handle_fw_websocket(websocket: web.WebSocketResponse, message: str,
                              client_handler: FirmwareUpgradeHandler,
                              comm_handler: CommunicationHandler,
                              session_parameters: dict):
    message = json.loads(message)
    print(
        WebsocketCommunicationHandler.format_address(
            websocket.remote_address),  # type: ignore
        message)
    if message['type'] == 'serial':  # type: ignore
        serial = message['value']  # type: ignore
        await client_handler.handle_input(serial=serial)
    elif message['type'] == 'status':  # type: ignore
        if message['value'] == 'connected':  # type: ignore
            await comm_handler.print_clear()
            await client_handler.cfu.refresh_gateways(comm_handler=comm_handler
                                                      )
            print(
                f"{session_parameters['id']} connected from {WebsocketCommunicationHandler.format_address(session_parameters['remote_address'])}"
            )

            await comm_handler.print_excel(
                session_parameters['download_url'],
                session_parameters['excel_filename'])
            await comm_handler.print_clear()
    elif message['type'] == 'excel':  # type: ignore
        if message['value'] == 'path':  # type: ignore
            await comm_handler.print_excel(
                session_parameters['download_url'],
                session_parameters['excel_filename'])
