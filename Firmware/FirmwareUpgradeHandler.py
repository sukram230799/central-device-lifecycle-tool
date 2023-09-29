import asyncio
import re
import typing

from aiohttp import web, web_ws
from Communication.CommunicationHandler import CommunicationHandler
from Helper.ArubaSerial import validate_sn

from Firmware.CentralFirmwareUpgrade import CentralFirmwareUpgrade
from Firmware.FirmwareExcelHandler import FirmwareExcelHandler


class FirmwareUpgradeHandler():

    def __init__(
        self,
        cfu: CentralFirmwareUpgrade,
        comm_handler: CommunicationHandler,
        excel_handler: typing.Union[FirmwareExcelHandler,
                                    None] = None) -> None:
        self.cfu = cfu
        self.comm_handler = comm_handler
        self.excel_handler = excel_handler
        self.last_serial = ''

    async def handle_input(self, serial: str):

        serial = serial.upper()

        await self.comm_handler.print_clear()

        await self.comm_handler.print_serial(serial=serial)

        if not validate_sn(serial=serial):

            await self.comm_handler.print_status('Serial?', color='red')

            self.last_serial = serial
            return

        escalate = serial == self.last_serial

        await self.check(serial=serial, escalate=escalate)
        self.last_serial = serial
        return

    async def check(self, serial: str, escalate: bool):
        # Check if in local DB or refresh from Central
        if await self.cfu.is_device_in_central(comm_handler=self.comm_handler,
                                               serial=serial):
            # Device found locally. Continue
            await self.comm_handler.print_log(
                _('{serial} is in Central').format(serial=serial))
        elif escalate:
            # Device not found locally. BUT force escalation
            # Refresh gateway list
            await self.cfu.refresh_gateways(comm_handler=self.comm_handler)
            await self.cfu.refresh_switches(comm_handler=self.comm_handler)
            await self.cfu.refresh_aps(comm_handler=self.comm_handler)
            # Check again if device is in central
            if await self.cfu.is_device_in_central(
                    comm_handler=self.comm_handler, serial=serial):
                # Device found in central continue
                await self.comm_handler.print_log(
                    _('{serial} is in Central').format(serial=serial))
            else:
                # Device not found in Central. Abort
                await self.comm_handler.print_log(
                    _('{serial} currently not known in Central').format(
                        serial=serial))

                await self.comm_handler.print_log()
                if self.excel_handler:
                    self.excel_handler.update_status(serial=serial,
                                                     status='Not in central')
                await self.comm_handler.print_status(_('Not in Central'),
                                                     color='orange')
                return  # ABORT

        else:
            # Locally not found. Notify user. Abort for now
            await self.comm_handler.print_log(
                _('{serial} currently not known in Central').format(
                    serial=serial))

            await self.comm_handler.print_log()
            if self.excel_handler:
                self.excel_handler.update_status(serial=serial,
                                                 status='Not in central')
            await self.comm_handler.print_status(_('Not in Central'),
                                                 color='orange')
            return  # ABORT

        # Device is in Central. DONE

        # Check if the firmware version is known
        if await self.cfu.is_device_version_knwon(
                comm_handler=self.comm_handler, serial=serial):
            # Known. Continue
            await self.comm_handler.print_log(
                _('{serial} version is known').format(serial=serial))
        else:
            # Unknown. Abort
            await self.comm_handler.print_log(
                _('{serial} version could not be determined. Is device online?'
                  ).format(serial=serial))
            await self.comm_handler.print_status('Version Unknown',
                                                 color='red')

            if not await self.cfu.is_device_online(
                    comm_handler=self.comm_handler, serial=serial):
                await self.comm_handler.print_status('Device Offline',
                                                     color='red')
                await self.comm_handler.print_log(
                    _('{serial} is offline. Please connect and wait...').
                    format(serial=serial))
            else:
                await self.comm_handler.print_log(
                    _('{serial} is online. But version unknown ¯\\_(ツ)_/¯').
                    format(serial=serial))

            return  # ABORT

        # Check if device is in the correct group
        if await self.cfu.is_device_in_group(comm_handler=self.comm_handler,
                                             serial=serial):
            # Device in correct group. Continue
            await self.comm_handler.print_log(
                _('{serial} is in correct group').format(serial=serial))
        else:
            # Device not in correct group. Move and abort further action
            await self.comm_handler.print_log(
                _('{serial} is in wrong group').format(serial=serial))

            await self.comm_handler.print_log()
            if self.excel_handler:
                self.excel_handler.update_status(serial=serial,
                                                 status='Moving')
            await self.comm_handler.print_status('Moving', color='grey')

            # Move gateway to desired group
            await self.cfu.move_device_to_group(comm_handler=self.comm_handler,
                                                serial=serial)

            # Sleep so that central has a chance to settle the move.
            await self.comm_handler.print_log('Sleep')
            await asyncio.sleep(2)

            # Now refresh the gateway list.
            # So that we can see the device with hopefully the correct group
            await self.cfu.refresh_gateways(comm_handler=self.comm_handler)
            await self.cfu.refresh_switches(comm_handler=self.comm_handler)
            await self.cfu.refresh_aps(comm_handler=self.comm_handler)
            return  # ABORT for now

        # Device is in Central. DONE
        # Device is in correct Group. DONE

        # Check if device has correct fw
        if await self.cfu.check_device_firmware(comm_handler=self.comm_handler,
                                                serial=serial):
            # Device on target firmware
            await self.comm_handler.print_log(
                _('{serial} is up-to-date').format(serial=serial))
            await self.comm_handler.print_log()
            if self.excel_handler:
                # Save current firmware to excel
                self.excel_handler.update_status(
                    serial=serial,
                    status=await self.cfu.get_device_firmware(
                        comm_handler=self.comm_handler, serial=serial))
            await self.comm_handler.print_status('Ok', color='green')

        elif escalate:  # Escalate look at the central fw status info
            await self.comm_handler.print_log(
                _('{serial} - Escalating').format(serial=serial))
            await self.comm_handler.print_log(
                await self.cfu.escalate_firmware_status(
                    comm_handler=self.comm_handler, serial=serial))
            return
        else:
            # Device not on target_firmware
            await self.comm_handler.print_log()
            if self.excel_handler:
                # Save current firmware to excel
                self.excel_handler.update_status(
                    serial=serial,
                    status=await self.cfu.get_device_firmware(
                        comm_handler=self.comm_handler, serial=serial))
            # User has to wait for upgrade
            await self.comm_handler.print_status('Wait', color='orange')
            await self.comm_handler.print_log()
            await self.comm_handler.print_log(
                _('{serial} not up-to-date. Check later or escalate by scanning again!'
                  ).format(serial=serial))

        return


async def redir_handler(request):
    raise web.HTTPFound('/app/firmware/firmware.html')


async def static():
    return
