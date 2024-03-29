import json
import typing
from uuid import uuid4

from aiohttp import web, web_ws
from Communication.CommunicationHandler import CommunicationHandler
from Communication.WebsocketCommunicationHandler import \
    WebsocketCommunicationHandler

from Decomission.CentralDecomission import CentralDecomission
from Decomission.DecomissionExcelHandler import DecomissionExcelHandler
from Decomission.DecomissionHandler import DecomissionHandler


class DecomissionWSHandler():

    def __init__(self,
                 cen_dec: CentralDecomission,
                 excel_dir: typing.Union[str, None] = None,
                 download_url: typing.Union[str, None] = None,
                 excel_persist: bool = False) -> None:
        self.cen_dec = cen_dec
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
            excel_handler = DecomissionExcelHandler(self.excel_dir)
            session_parameters['excel_dir'] = '/out'
            session_parameters['excel_filename'] = excel_handler.get_filename()

        client_handler = DecomissionHandler(self.cen_dec,
                                            comm_handler=comm_handler,
                                            excel_handler=excel_handler)

        async for msg in ws:
            print('DEC', msg)
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
                              client_handler: DecomissionHandler,
                              comm_handler: CommunicationHandler,
                              session_parameters: dict):
    message_parsed = json.loads(message)
    print(
        WebsocketCommunicationHandler.format_address(
            websocket.remote_address),  # type: ignore
        message_parsed)
    if message_parsed['type'] == 'serial':
        serial = message_parsed['value']
        unlicense = False
        if 'unlicense' in message_parsed.keys():
            unlicense = message_parsed['unlicense'] == True
        await client_handler.handle_input(serial=serial,
                                          options={'unlicense': unlicense})
    elif message_parsed['type'] == 'status':
        if message_parsed['value'] == 'connected':
            await comm_handler.print_clear()
            await client_handler.cen_dec.refresh_devices(
                comm_handler=comm_handler)
            print(
                f"{session_parameters['id']} connected from {WebsocketCommunicationHandler.format_address(session_parameters['remote_address'])}"
            )

            await comm_handler.print_excel(
                session_parameters['download_url'],
                session_parameters['excel_filename'])
            await comm_handler.print_clear()
    elif message_parsed['type'] == 'excel':  # type: ignore
        if message_parsed['value'] == 'path':  # type: ignore
            await comm_handler.print_excel(
                session_parameters['download_url'],
                session_parameters['excel_filename'])
