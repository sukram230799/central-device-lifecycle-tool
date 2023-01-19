import asyncio
import re
from datetime import datetime
from typing import TypedDict
import typing

from aiohttp import web
from Communication.CommunicationHandler import CommunicationHandler
from Helper.ArubaSerial import validate_sn

from Decomission.CentralDecomission import CentralDecomission
from Decomission.DecomissionExcelHandler import DecomissionExcelHandler


class DecomissionHandler():

    def __init__(
        self,
        cen_dec: CentralDecomission,
        comm_handler: CommunicationHandler,
        excel_handler: typing.Union[DecomissionExcelHandler,
                                    None] = None) -> None:
        self.cen_dec = cen_dec
        self.comm_handler = comm_handler
        self.excel_handler = excel_handler
        self.last_serial = ''

    class OptionsDict(TypedDict):
        unlicense: bool

    async def handle_input(self, serial: str, options: OptionsDict):

        serial = serial.upper()

        await self.comm_handler.print_clear()

        if not validate_sn(serial=serial):

            await self.comm_handler.print_status('Serial?', color='red')

            self.last_serial = serial
            return

        second_scan = serial == self.last_serial

        if second_scan and self.in_central:
            # 2nd run
            if options['unlicense']:
                await self.comm_handler.print_log(
                    _('{serial} - Unasign license option activated. Device will also be deleted'
                      ).format(serial=serial))
                await self.unasign_device(serial)
            else:
                await self.comm_handler.print_log(
                    _('{serial} - Delete device option activated. License will be kept'
                      ).format(serial=serial))
                await self.delete_device(serial)

        else:
            # 1st run
            await self.comm_handler.print_log(
                _('{serial} - Check Central').format(serial=serial))
            self.in_central = await self.check_central(serial)

        # Save last serial
        self.last_serial = serial
        return

    async def check_central(self, serial):
        in_central = await self.cen_dec.is_device_in_central(
            comm_handler=self.comm_handler, serial=serial)
        if in_central:
            # Device found
            await self.notify_device_is_in_central(serial)

        # else: Refreshing is taking too long...
        #     # Device not found
        #     # Refresh the local cache to look again
        #     await self.cen_dec.refresh_devices(comm_handler=self.comm_handler)

        #     in_central = await self.cen_dec.is_device_in_central(
        #         comm_handler=self.comm_handler, serial=serial)
        #     if in_central:
        #         # Device found
        #         await self.notify_device_is_in_central(serial)
        #     else:
        #         # Device not found. Even though we refreshed
        #         await self.notify_device_not_in_central(serial)

        return in_central

    async def delete_device(self, serial):
        success = await self.cen_dec.delete_device(
            comm_handler=self.comm_handler, serial=serial)

        if success:
            await self.notify_device_deleted(serial)
        else:
            await self.notify_device_not_deleted(serial)

    async def unasign_device(self, serial):
        success, out = await self.cen_dec.unassign_subscription(
            comm_handler=self.comm_handler, serial=serial)
        await self.comm_handler.print_log(
            _('{serial} unsubscribed {success}, {out}').format(serial=serial,
                                                               success=success,
                                                               out=out))
        if success:
            await self.comm_handler.print_status(message=_('Unsubscribed'),
                                                 color='green')
            if self.excel_handler:
                self.excel_handler.update_status(
                    serial=serial, state={'unsubscribed_on': datetime.now()})
        else:
            await self.comm_handler.print_status(
                message=_('Subscription Error'), color='red')
            if self.excel_handler:
                self.excel_handler.update_status(
                    serial=serial, state={'unsubscribed_on': 'ERROR'})

    # State notification and logging handler

    async def notify_device_is_in_central(self, serial):
        """
        Device is found in Central.

        Notify client and log to excel.
        """
        await self.comm_handler.print_status(message='In Central',
                                             color='orange')
        if self.excel_handler:
            self.excel_handler.update_status(serial=serial,
                                             state={'status': 'In Central'})

    async def notify_device_not_in_central(self, serial):
        """
        Device is not found in Central.

        Notify client and log to excel.
        """
        await self.comm_handler.print_status(message=_('Not in Central'),
                                             color='red')
        if self.excel_handler:
            self.excel_handler.update_status(
                serial=serial, state={'status': 'Not in Central'})

    async def notify_device_deleted(self, serial):
        """
        Device was successfully deleted.

        Notify client and log date to excel
        """
        await self.comm_handler.print_status(message=_('Deleted'),
                                             color='green')
        if self.excel_handler:
            self.excel_handler.update_status(
                serial=serial, state={'deleted_on': datetime.now()})

    async def notify_device_not_deleted(self, serial):
        """
        Device was not deleted.

        Notify client and log ERROR to excel
        """
        await self.comm_handler.print_status(message=_('Deletion aborted'),
                                             color='red')
        if self.excel_handler:
            self.excel_handler.update_status(serial=serial,
                                             state={'deleted_on': 'ERROR'})


async def redir_handler(request):
    raise web.HTTPFound('/app/decomission/decomission.html')
