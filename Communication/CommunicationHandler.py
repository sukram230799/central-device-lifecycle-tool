import os.path
import typing

from pyfiglet import figlet_format


class CommunicationHandler():

    def __init__(self) -> None:
        pass

    async def print_clear(self):
        print('\n' * 10)

    async def print_status(self, message,
                           color: typing.Literal['red', 'green', 'orange',
                                                 'grey']):
        print(figlet_format(message, font='banner'))

    async def print_log(self, message=None):
        if message is None:
            print()
        else:
            print(message)

    async def print_serial(self, serial: str):
        print(serial)

    async def print_excel(self, prefix: str | None, filename: str | None):
        if prefix and filename:
            print(f'Excel: {os.path.join(prefix, filename)}')
        if filename:
            print(f'Excel: {filename}')
