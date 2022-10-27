from typing import Dict
import typing

from CentralAPI.CentralAPI import Central
from Communication.CommunicationHandler import CommunicationHandler


class CentralFirmwareUpgrade:

    def __init__(self,
                 central_client: Central,
                 group,
                 target_firmware: typing.Union[str, None] = None):
        self.gateway_dict = {}  # List with all gateways and state

        self.central_client = central_client  # Central API Provider
        self.group = group  # Selected group
        self.target_firmware = target_firmware  # Firmware to which the devices should be upgraded

        if self.target_firmware == None:
            # No firmware override provided by CLI - Loading from central
            self.target_firmware = self.get_firmware_compliance_version()

    def get_firmware_compliance_version(self) -> str:
        fw_report = self.central_client.get_firmware_compliance(
            self.group, 'CONTROLLER')
        return fw_report[
            'firmware_compliance_version']  # f.e. '8.7.0.0-2.3.0.8_84688'

    def gateways_to_dict(self, gateway_dict: Dict, gateways):
        for gateway in gateways:
            gateway_dict[gateway['serial']] = gateway

        return gateway_dict

    async def get_gateways(self):
        """
        Pagination aware loading of gateways to a dictionary
        """
        step = 1000
        offset = 0
        total = None

        gateway_dict = {}

        while total == None or (offset < total and len(gateway_dict) < total):
            gateways_c = await self.central_client.get_gateways(
                limit=step, offset=offset, calculate_total=True)

            offset = offset + step
            total = gateways_c['total']

            gateway_dict = self.gateways_to_dict(gateway_dict,
                                                 gateways_c['gateways'])

        return gateway_dict

    async def refresh_gateways(self,
                               *,
                               comm_handler: typing.Union[CommunicationHandler,
                                                          None] = None):
        """
        Refresh local gateway list in `self.gateway_dict` from central
        """
        if comm_handler:
            await comm_handler.print_log(_('Refreshing gateway list'))
        self.gateway_dict = await self.get_gateways()

    async def is_device_in_central(self, *, comm_handler: CommunicationHandler,
                                   serial: str):
        """
        Local check if device is in `self.gateway_dict`.

        Retruns `true` if `serial` found in central.
        """
        await comm_handler.print_log(_('{serial} - device in central?').format(serial=serial))
        return serial in self.gateway_dict

    async def is_device_in_group(self, *, comm_handler: CommunicationHandler,
                                 serial: str):
        """
        Local check if device is correct group in `self.gateway_dict`.
        
        Returns `true` if `serial` has the correct group associated.
        """
        await comm_handler.print_log(_('{serial} - device in group?').format(serial=serial))
        if serial not in self.gateway_dict: return None
        return self.gateway_dict[serial]['group_name'] == self.group

    async def is_device_version_knwon(self, *,
                                      comm_handler: CommunicationHandler,
                                      serial: str):
        """
        Local check if device firmware is knwon.

        Returns `true` if firmware is known.
        """
        await comm_handler.print_log(_('{serial} - is firmware known?').format(serial=serial))
        if serial in self.gateway_dict:
            return not self.gateway_dict[serial][
                'firmware_version'] == 'Unknown'

    async def is_device_online(self, *, comm_handler: CommunicationHandler,
                               serial: str):
        """
        Local check if device is online.

        Returns `true` if device is online.
        """
        await comm_handler.print_log(_('{serial} - online?').format(serial=serial))
        if serial in self.gateway_dict:
            return not self.gateway_dict[serial]['status'] == 'Down'

    async def move_device_to_group(self, *, comm_handler: CommunicationHandler,
                                   serial: str):
        """
        Move a device to the configured group in `self.group` using the central api.

        Returns `true` if move has been initiated.
        """
        await comm_handler.print_log(
            _('{serial} - Move device to group {group}').format(serial=serial, group=self.group))
        result = await self.central_client.move_to_group({
            'group':
            self.group,
            "serials": [f"{serial}"]
        })
        '\nController/Gateway group move has been initiated, please check audit trail for details '

        await comm_handler.print_log(result)
        if not 'description' in result: return False
        return 'initiated' in result['description']

    async def get_device_firmware(self, *, comm_handler: CommunicationHandler,
                                  serial: str):
        """
        Local return of the device firmware version found in `self.gateway_dict`.
        """
        await comm_handler.print_log(_('{serial} - get fw version local').format(serial=serial))
        if serial not in self.gateway_dict: return None
        return self.gateway_dict[serial]['firmware_version']

    async def check_device_firmware(self, *,
                                    comm_handler: CommunicationHandler,
                                    serial: str):
        """
        Check if device firmware in `self.gateway_dict` matches the `self.target_firmware`.
        Reloads `self.gateway_dict` from central if version doesn't match.

        Returns `true` if the device has the correct firmware version.
        """
        await comm_handler.print_log(_('{serial} - Check fw version').format(serial=serial))
        if self.target_firmware == await self.get_device_firmware(
                comm_handler=comm_handler, serial=serial):
            return True

        # Not currently up to date -> refreshing from central
        await self.refresh_gateways(comm_handler=comm_handler)

        await comm_handler.print_log(_('{serial} - Check fw version again!').format(serial=serial))
        return self.target_firmware == await self.get_device_firmware(
            comm_handler=comm_handler, serial=serial)

    async def escalate_firmware_status(self, *,
                                       comm_handler: CommunicationHandler,
                                       serial: str):
        """
        Escalates the firmware status by querying the status directly from central for a more verbose feedback.

        Returns the reason retruned from central.
        
        - Rebooting the device
        - Queued request to upgrade firmware
        - No Update from the device. Please check the status after sometime
        """
        await comm_handler.print_log(_('{serial} - Escalate fw status').format(serial=serial))

        return (await self.central_client.get_firmware_status(serial=serial
                                                              ))['reason']
