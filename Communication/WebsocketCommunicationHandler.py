import os.path
import typing

from aiohttp import web, web_ws

from Communication.CommunicationHandler import CommunicationHandler


class WebsocketCommunicationHandler(CommunicationHandler):

    def __init__(self, websocket: web.WebSocketResponse) -> None:
        self.websocket = websocket

    async def print_clear(self):
        await self.send_clear()

    async def print_status(self, message,
                           color: typing.Literal['red', 'green', 'orange',
                                                 'grey']):
        await self.send_status(status=message, color=color)
        self.print('Status', message)

    async def print_log(self, message=None):
        if message is None:
            await self.send_log(message='')
        else:
            await self.send_log(message=message)
            self.print('Log', message)

    async def print_serial(self, serial: str):
        await self.send_serial(serial)
        self.print('Serial', serial)

    async def print_excel(self, prefix: str | None, filename: str | None):
        if filename and prefix:
            path = '/'.join(os.path.split(prefix)) + '/' + filename
            path = path.replace('//', '/')
            return await self.send_excel(path)
        if filename:
            return await self.send_excel(filename)

    async def send_status(self, status, color):
        #   additional_data: typing.Mapping | None = None):
        data = {
            'type': 'status',
            'value': status,
            'color': color,
        }
        # if additional_data is typing.Mapping:
        #     data = {**data, **additional_data}  # type: ignore
        return await self.websocket.send_json(data)

    async def send_log(self, message):
        return await self.websocket.send_json({
            'type': 'log',
            'value': message
        })

    async def send_serial(self, serial):
        return await self.websocket.send_json({
            'type': 'serial',
            'value': serial
        })

    async def send_clear(self):
        return await self.websocket.send_json({'type': 'clear'})

    async def send_excel(self, filename: str):
        return await self.websocket.send_json({
            'type': 'excel',
            'value': filename
        })

    def print(self, type: typing.Literal['Log', 'Status', 'Serial'], message):
        WebsocketCommunicationHandler.format_address(
            self.websocket.remote_address  # type: ignore
        ), '-', type, '-', message

    @staticmethod
    def format_address(address):
        return f'{address[0]}:{address[1]}'
