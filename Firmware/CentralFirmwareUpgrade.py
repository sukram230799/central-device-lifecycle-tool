from typing import Dict
import typing

from CentralAPI.CentralAPI import Central, DeviceDetailsSkeleton
from Communication.CommunicationHandler import CommunicationHandler


class CentralFirmwareUpgrade:

    def __init__(self,
                 central_client: Central,
                 group,
                 target_firmware: typing.Union[str, None] = None):
        self.gateway_dict = {}  # List with all gateways and state
        self.switch_dict = {}  # List with all switches and state
        self.ap_dict = {}  # List with all aps and state

        self.central_client = central_client  # Central API Provider
        self.group = group  # Selected group
        self.target_firmware_gateway = target_firmware  # Firmware to which the devices should be upgraded
        self.target_firmware_cx = None
        self.target_firmware_ap = None
        self.target_firmware_hp = None

        if self.target_firmware_gateway is None:
            # No firmware override provided by CLI - Loading from central
            self.target_firmware_gateway = \
                self.get_firmware_compliance_version('CONTROLLER')

        if self.target_firmware_cx is None:
            # No firmware override provided by CLI - Loading from central
            self.target_firmware_cx = \
                self.get_firmware_compliance_version('CX')

        if self.target_firmware_ap is None:
            self.target_firmware_ap = \
                self.get_firmware_compliance_version('IAP')

        if self.target_firmware_hp is None:
            self.target_firmware_hp = \
                self.get_firmware_compliance_version('HP')

    def get_device(self, serial) -> typing.Union[DeviceDetailsSkeleton, None]:
        if serial in self.gateway_dict:
            return self.gateway_dict[serial]
        if serial in self.switch_dict:
            return self.switch_dict[serial]
        if serial in self.ap_dict:
            return self.ap_dict[serial]
        return None

    def get_firmware_compliance_version(
            self, device_type: Central.FIRMWARE_DEVICE_TYPE) -> str:
        fw_report = self.central_client.get_firmware_compliance(
            self.group, device_type)
        return fw_report[
            'firmware_compliance_version']  # f.e. '8.7.0.0-2.3.0.8_84688'

    def gateways_to_dict(self, gateway_dict: Dict, gateways):
        for gateway in gateways:
            gateway_dict[gateway['serial']] = gateway

        return gateway_dict

    def switches_to_dict(self, switch_dict: Dict, switches):
        for switch in switches:
            switch_dict[switch['serial']] = switch

        return switch_dict

    def aps_to_dict(self, ap_dict: Dict, aps):
        for ap in aps:
            ap_dict[ap['serial']] = ap

        return ap_dict

    async def get_gateways(self):
        """
        Pagination aware loading of gateways to a dictionary
        """
        step = 1000
        offset = 0

        gateway_dict = {}

        while True:
            gateways_c = await self.central_client.get_gateways(
                limit=step, offset=offset, calculate_total=False)

            if not len(gateways_c['gateways']):
                return gateway_dict

            gateway_dict = self.gateways_to_dict(gateway_dict,
                                                 gateways_c['gateways'])

            offset = offset + step

    async def get_switches(self):
        """
        Pagination aware loading of switches to a dictionary
        """
        step = 1000
        offset = 0

        switches_dict = {}

        while True:
            switches_c = await self.central_client.get_switches(limit=step,
                                                                offset=offset)

            if not len(switches_c['switches']):
                return switches_dict

            switches_dict = self.switches_to_dict(switches_dict,
                                                  switches_c['switches'])

            offset = offset + step

    async def get_aps(self):
        """
        Pagination aware loading of switches to a dictionary
        """
        step = 1000
        offset = 0

        ap_dict = {}

        while True:
            aps_c = await self.central_client.get_aps(limit=step,
                                                      offset=offset)

            if not len(aps_c['aps']):
                return ap_dict

            ap_dict = self.aps_to_dict(ap_dict, aps_c['aps'])

            offset = offset + step

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

    async def refresh_switches(self,
                               *,
                               comm_handler: typing.Union[CommunicationHandler,
                                                          None] = None):
        """
        Refresh local switch list in `self.switch_dict` from central
        """
        if comm_handler:
            await comm_handler.print_log(_('Refreshing switch list'))
        self.switch_dict = await self.get_switches()

    async def refresh_aps(self,
                          *,
                          comm_handler: typing.Union[CommunicationHandler,
                                                     None] = None):
        """
        Refresh local ap list in `self.ap_dict` from central
        """
        if comm_handler:
            await comm_handler.print_log(_('Refreshing ap list'))
        self.ap_dict = await self.get_aps()

    async def is_device_in_central(self, *, comm_handler: CommunicationHandler,
                                   serial: str):
        """
        Local check if device is in `self.gateway_dict`.

        Retruns `true` if `serial` found in central.
        """
        await comm_handler.print_log(
            _('{serial} - device in central?').format(serial=serial))
        return \
            serial in self.gateway_dict or \
            serial in self.switch_dict or \
            serial in self.ap_dict

    def get_device_type(self, *, serial: str):
        """
        Returns device type for device or None if not known
        """
        if serial in self.gateway_dict:
            return 'CONTROLLER'
        elif serial in self.switch_dict:
            if self.switch_dict[serial]['switch_type'] == 'AOS-S':
                return 'HP'
            else:
                return 'CX'
        elif serial in self.ap_dict:
            return 'IAP'
        return None

    async def is_device_in_group(self, *, comm_handler: CommunicationHandler,
                                 serial: str):
        """
        Local check if device is correct group in `self.gateway_dict`.
        
        Returns `true` if `serial` has the correct group associated.
        """
        await comm_handler.print_log(
            _('{serial} - device in group?').format(serial=serial))

        device = self.get_device(serial=serial)
        if device is None:
            return None
        else:
            return device['group_name'] == self.group

    async def is_device_version_knwon(self, *,
                                      comm_handler: CommunicationHandler,
                                      serial: str):
        """
        Local check if device firmware is knwon.

        Returns `true` if firmware is known.
        """
        await comm_handler.print_log(
            _('{serial} - is firmware known?').format(serial=serial))
        device = self.get_device(serial=serial)
        if device is not None:
            return not device['firmware_version'] == 'Unknown'

    async def is_device_online(self, *, comm_handler: CommunicationHandler,
                               serial: str):
        """
        Local check if device is online.

        Returns `true` if device is online.
        """
        await comm_handler.print_log(
            _('{serial} - online?').format(serial=serial))
        device = self.get_device(serial=serial)
        if device is not None:
            return not device['status'] == 'Down'

    async def move_device_to_group(self, *, comm_handler: CommunicationHandler,
                                   serial: str):
        """
        Move a device to the configured group in `self.group` using the central api.

        Returns `true` if move has been initiated.
        """
        await comm_handler.print_log(
            _('{serial} - Move device to group {group}').format(
                serial=serial, group=self.group))
        result = await self.central_client.move_to_group({
            'group':
            self.group,
            'serials': [f'{serial}'],
        })
        '\nController/Gateway group move has been initiated, please check audit trail for details '

        await comm_handler.print_log(result)
        if not 'description' in result: return False
        return 'initiated' in result['description']

    async def get_device_firmware(self, *, comm_handler: CommunicationHandler,
                                  serial: str):
        """
        Local return of the device firmware version found in
        `self.gateway_dict`.
        """
        await comm_handler.print_log(
            _('{serial} - get fw version local').format(serial=serial))
        device = self.get_device(serial=serial)
        if device is not None:
            return device['firmware_version']

    async def check_device_firmware(self, *,
                                    comm_handler: CommunicationHandler,
                                    serial: str):
        """
        Check if device firmware in `self.gateway_dict` matches
        the `self.target_firmware`.
        Reloads `self.gateway_dict` from central if version doesn't match.

        Returns `true` if the device has the correct firmware version.
        """
        await comm_handler.print_log(
            _('{serial} - Check fw version').format(serial=serial))

        device_type = self.get_device_type(serial=serial)
        firmware = await self.get_device_firmware(comm_handler=comm_handler,
                                                  serial=serial)

        if device_type == 'CONTROLLER' and \
                self.target_firmware_gateway == firmware:
            return True
        elif device_type == 'HP' and \
                self.target_firmware_hp == firmware:
            return True
        elif device_type == 'CX' and \
                self.target_firmware_cx == firmware:
            return True
        elif device_type == 'AP' and \
                self.target_firmware_ap == firmware:
            return True

        # Not currently up to date -> refreshing from central
        await self.refresh_gateways(comm_handler=comm_handler)
        await self.refresh_switches(comm_handler=comm_handler)
        await self.refresh_aps(comm_handler=comm_handler)

        await comm_handler.print_log(
            _('{serial} - Check fw version again!').format(serial=serial))
        if device_type == 'CONTROLLER':
            return self.target_firmware_gateway == firmware
        elif device_type == 'HP':
            return self.target_firmware_hp == firmware

        elif device_type == 'CX':
            return self.target_firmware_cx == firmware

        elif device_type == 'AP':
            return self.target_firmware_ap == firmware
        return False

    async def escalate_firmware_status(self, *,
                                       comm_handler: CommunicationHandler,
                                       serial: str):
        """
        Escalates the firmware status by querying the status directly from
        central for a more verbose feedback.

        Returns the reason retruned from central.
        
        - Rebooting the device
        - Queued request to upgrade firmware
        - No Update from the device. Please check the status after sometime
        """
        await comm_handler.print_log(
            _('{serial} - Escalate fw status').format(serial=serial))

        return (await self.central_client.get_firmware_status(serial=serial
                                                              ))['reason']
