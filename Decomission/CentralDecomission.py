import typing
from typing import List, Literal, Tuple, cast

from CentralAPI.CentralAPI import CENTRAL_SERVICES, SKU_TYPE, Central
from Communication.CommunicationHandler import CommunicationHandler


class CentralDecomission():

    def __init__(self, central_client: Central, device_type: SKU_TYPE) -> None:
        self.device_dict = {}

        self.central_client = central_client

        self.device_type = device_type

        # self.get_devices()
        pass

    def devices_to_dict(self, devices_dict: dict, devices):
        for device in devices:
            devices_dict[device['serial']] = device

        return devices_dict

    async def get_devices(self):
        """
        Pagination aware loading of devices to a dictionary
        """
        step = 1000
        offset = 0
        total = None

        devices_dict = {}

        while total == None or (offset < total and len(devices_dict) < total):
            devices_c = await self.central_client.get_devices_from_inventory(
                sku_type=self.device_type,  # type: ignore
                limit=step,
                offset=offset)

            offset = offset + step
            total = devices_c['total']

            devices_dict = self.devices_to_dict(devices_dict,
                                                devices_c['devices'])

        return devices_dict

    async def refresh_devices(self, *, comm_handler: CommunicationHandler
                              | None):
        """
        Refresh local devices list in `self.devices_dict` from central
        """
        if comm_handler:
            await comm_handler.print_log('Refreshing devices list')
        self.device_dict = await self.get_devices()

    async def is_device_in_central(self, *, comm_handler: CommunicationHandler,
                                   serial: str):
        """
        Local check if device is in `self.gateway_dict`.

        Retruns `true` if `serial` found in central.
        """
        await comm_handler.print_log(f'{serial} - Device in central?')
        return serial in self.device_dict

    async def get_device_type(self, *, comm_handler: CommunicationHandler,
                              serial: str) -> str | None:
        if serial not in self.device_dict.keys():
            return None
        if 'device_type' not in self.device_dict[serial].keys():
            return None
        device_type = self.device_dict[serial]['device_type']
        await comm_handler.print_log(f'{serial} is {device_type}')
        return device_type

    async def delete_device(self, *, comm_handler: CommunicationHandler,
                            serial: str) -> bool:
        device_type = await self.get_device_type(comm_handler=comm_handler,
                                                 serial=serial)
        if not device_type:
            await comm_handler.print_log(
                f'{serial} - Device Type not known. Aborting')
            return False

        if device_type.upper() == 'GATEWAY':
            await comm_handler.print_log(f'{serial} - Delete Gateway')
            success = self.central_client.delete_gateway(serial)
            #, proxies="http://localhost:8080", verify=None)
            await comm_handler.print_log(f'{serial} - Deleted Gateway')

            # TODO: Handle out
            return success

        if device_type.upper() == 'SWITCH':
            await comm_handler.print_log(
                f'{serial} - Device Type SWITCH not supported. Aborting')
            return False
            raise NotImplementedError()

        if device_type.upper() == 'AP':
            await comm_handler.print_log(
                f'{serial} - Device Type AP not supported. Aborting')
            return False
            raise NotImplementedError()

        await comm_handler.print_log(
            f'{serial} - Device Type {device_type} not supported. Aborting')
        return False

        raise NotImplementedError()

    async def get_device_services(
            self, *, comm_handler: CommunicationHandler,
            serial: str) -> typing.List[CENTRAL_SERVICES] | None:
        if serial not in self.device_dict.keys():
            return None
        if 'services' not in self.device_dict[serial].keys():
            return None
        device_services = self.device_dict[serial]['services']
        await comm_handler.print_log(
            f'{serial} has those services: {device_services}')
        return device_services

    async def unassign_subscription(
        self,
        *,
        comm_handler: CommunicationHandler,
        serial: str,
        services: typing.List[CENTRAL_SERVICES]
        | None = None
    ) -> Tuple[bool, dict]:
        if not services:
            services = await self.get_device_services(
                comm_handler=comm_handler, serial=serial)
        if not services:
            return False, {'error': 'No Subscriotions found'}

        out = self.central_client.unassign_subscription_device(
            {
                'serials': [serial],
                'services': services
            }, )
        # proxies="http://localhost:8080",
        # verify=None)
        # out = good_result = {"response": "success"}
        if 'response' in out and out['response'] == 'success':
            return True, out
        else:
            return False, out
