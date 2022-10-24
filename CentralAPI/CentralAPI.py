import json

import typing

from decorest import (GET, PATCH, POST, PUT, DELETE, HTTPErrorWrapper,
                      RestClient, accept, backend, body, content, endpoint, on,
                      query, timeout)

SKU_TYPE = typing.Literal['GATEWAY', 'AP', 'SWITCH', 'all']

CENTRAL_SERVICES = typing.Literal['pa', 'foundation_switch_6200', 'clarity',
                                  'ucc', 'dm', 'advanced_ap', 'airgroup',
                                  'advance_90xx_sec', 'cloud_guest']


class UnassignSubscriptionType(typing.TypedDict):
    serials: typing.List[str]
    services: typing.List[CENTRAL_SERVICES]


@backend('httpx')
@timeout(60)
class Central(RestClient):

    @GET('monitoring/v1/gateways')
    @query('limit')
    @query('offset')
    @query('calculate_total')
    async def get_gateways(self,
                           limit: int | None = 1000,
                           offset: int | None = None,
                           calculate_total: bool = True) -> typing.Dict:
        """
        Get gateways. You can only specify one of group, label parameters.
        Possible error_codes for the error responses are

        0001 - General Error.
        0002 - Validation Error. Out of Range value for a query parameter.
        0003 - Validation Error. Unsupported query combination
        0004 - Validation Error. Invalid value for a query parameter

        ---

        https://developer.arubanetworks.com/aruba-central/reference/apiexternal_controllerget_gateways
        """
        # Example
        return {
            "count":
            1,
            "total":
            8,
            "gateways": [{
                'cpu_utilization': 0,
                'firmware_backup_version': None,
                'firmware_version': 'string',
                'group_name': 'default',
                'ip_address': 'string',
                'labels': [],
                'mac_range': None,
                'macaddr': 'string',
                'mem_free': 0,
                'mem_total': 0,
                'mode': 'GATEWAY',
                'model': 'A9004-LTE',
                'name': 'string',
                'reboot_reason': None,
                'role': '',
                'serial': 'string',
                'site': None,
                'status': 'Down',
                'uptime': 0
            }]
        }

    @POST('configuration/v1/devices/move')
    @accept('application/json')
    @content('application/json')
    @on(200, lambda r: r.json())
    @on(500, lambda r: r.json())
    @body('data', lambda data: json.dumps(data))
    async def move_to_group(self, data) -> typing.Dict:
        """
        List of given device serials will be moved to the specified group.

        If the device is already part of any group: Move device to group and assign specified group in device management page.
        Note: if given device is part of a swarm, stack or controller, all associated devices will be moved to the target group.

        If device is not part of any group: Assign specified group in device management page.

        The 'preserve_config_overrides' parameter can be used to retain device configuration overrides when it is moved to UI group.
        The configuration of devices of type mentioned in this list will be preserved when the device is moved to a UI group.
        The device configuration will not be reset completely with the group level configuration
        This is supported only for AOS_CX devices.

        ---
        
        https://developer.arubanetworks.com/aruba-central/reference/apigroupsmove_devices
        """
        return {}

    @GET('firmware/v1/status')
    @query('serial')
    @accept('application/json')
    @on(200, lambda r: r.json())
    async def get_firmware_status(self, serial: str) -> typing.Dict:
        """
        Get firmware upgrade status of device.

        You can either specify swarm_id if device_type is "IAP" or serial for rest of device_type, but not both.

        Possible error_codes for the error responses are

        0001 - General Error.
        0003 - Validation Error. Unsupported query combination
        0004 - Validation Error. Invalid value for a query parameter

        ---

        https://developer.arubanetworks.com/aruba-central/reference/apifirmwareget_firmware_status
        """
        # Example
        return {
            "state": "string",
            "reason": "string",
            "firmware_scheduled_at": 0
        }

    @GET('firmware/v1/upgrade/compliance_version')
    @query('group')
    @query('device_type')
    @accept('application/json')
    @on(200, lambda r: r.json())
    def get_firmware_compliance(
            self, group: str,
            device_type: typing.Literal['IAP', 'MAS', 'HP',
                                        'CONTROLLER']) -> typing.Dict:
        """
        To get firmware compliance version for specific device_type, for customer.

        To get firmware compliance version for group level, Please specify group name.

        Please specify device_type as one of "IAP" for swarm, "MAS" for MAS switches, "HP" for aruba switches, "CONTROLLER" for controllers respectively.

        Possible error_codes for the error responses are

        0001 - General Error.
        0003 - Validation Error. Unsupported query combination
        0004 - Validation Error. Invalid value for a query parameter
        0005 - Validation Error. Missing required parameter.

        ---

        https://developer.arubanetworks.com/aruba-central/reference/apifirmwareget_firmware_compliance
        """
        # Example
        return {
            "firmware_compliance_version": "string",
            "compliance_scheduled_at": 0
        }

    @GET('platform/device_inventory/v1/devices')
    @query('sku_type')
    @query('limit')
    @query('offset')
    @accept('application/json')
    @on(200, lambda r: r.json())
    async def get_devices_from_inventory(self,
                                         sku_type: SKU_TYPE,
                                         limit=None,
                                         offset=None) -> typing.Dict:
        """
        This API is used to fetch list of devices from device inventory.

        ---

        https://developer.arubanetworks.com/aruba-central/reference/acp_servicenb_apiapidevice_inventoryget_devices
        """
        # Example
        return {
            'devices': [{
                'aruba_part_no': 'R3V91A',
                'customer_id': 'string',
                'customer_name': 'string',
                'device_type': 'GATEWAY',
                'imei': None,
                'macaddr': 'string',
                'model': '9004LTE-US',
                'serial': 'string',
                'services': ['ADVANCE_90XX_SEC'],
                'tier_type': 'advanced'
            }],
            'total':
            1
        }

    @DELETE('monitoring/v1/gateways/{serial}')
    @accept('application/json')
    @on(200, lambda r: r.json())
    @on(404, lambda _: False)
    def delete_gateway(self, serial) -> bool:
        """
        Delete gateway

        ---

        https://developer.arubanetworks.com/aruba-central/reference/apiexternal_controllerdelete_gateway
        """
        # Example
        return False

    @POST('platform/licensing/v1/subscriptions/unassign')
    @accept('application/json')
    @content('application/json')
    @on(200, lambda r: r.json())
    @on(500, lambda r: r.json())
    @body('data', lambda data: json.dumps(data))
    def unassign_subscription_device(
            self, data: UnassignSubscriptionType) -> typing.Dict:
        """
        This API is used to unassign subscriptions to device by specifying its serial. 

        `{"serials": ["SN01"], "services": ["Service"]}`

        ---

        https://developer.arubanetworks.com/aruba-central/reference/acp_servicelicensewebviewsadmin_licenseapigw_unassign_licenses
        """
        # Example
        return {}
