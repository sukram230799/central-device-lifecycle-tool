from cgitb import enable
from http import client
import json
from multiprocessing.spawn import import_main_path

import typing

from uuid import uuid4

from decorest import (GET, PATCH, POST, PUT, HTTPErrorWrapper, RestClient,
                      accept, backend, body, content, endpoint, on, query,
                      timeout)
from CentralAPI.APIKeySetupAndCheck import APIKeySetupAndCheck
from Decomission.CentralDecomission import CentralDecomission
from Decomission.DECWebsocketHandler import DECWebsocketHandler
from Decomission.DecomissionExcelHandler import DecomissionExcelHandler
from Decomission.DecomissionHandler import DecomissionHandler, redir_handler as dec_redir_handler
from Firmware.FWWebsocketHandler import FWWebsocketHandler

from CentralTokenAuth.CentralTokenAuth import CentralTokenAuth

import argparse

import asyncio

import json
from aiohttp import web, web_ws

from Firmware.FirmwareExcelHandler import FirmwareExcelHandler
from CentralAPI.CentralAPI import Central
from Communication.CommunicationHandler import CommunicationHandler
from Communication.WebsocketCommunicationHandler import WebsocketCommunicationHandler
from Firmware.CentralFirmwareUpgrade import CentralFirmwareUpgrade
from Firmware.FirmwareUpgradeHandler import FirmwareUpgradeHandler, redir_handler as fw_redir_handler

args = None


class WebRoot():

    def __init__(self, routes: typing.List[typing.Dict]) -> None:
        self.routes = routes

    async def web_root_handler(self, request):
        body = ''
        for route in self.routes:
            body += f'<a href="{route["url"]}">{route["name"]}</a><br>'
        return web.Response(body=f'<html><body>{body}</body></html>',
                            content_type='text/html')


def main():
    global args

    parser = argparse.ArgumentParser(
        description='Check Gateway Fírmware status.')
    parser.add_argument('-w',
                        '--web',
                        help='Launch using web api and interface',
                        action='store_true')
    parser.add_argument(
        '--console',
        help='Lauch locally using a simplistic command line interface',
        action='store_true',
        default=True)
    parser.add_argument('--web-port',
                        type=int,
                        default=8080,
                        help='Specify the port for webserver')
    parser.add_argument('--web-address',
                        type=str,
                        default='127.0.0.1',
                        help='Specify the address for webserver')
    parser.add_argument(
        '--firmware',
        help=
        'Override target firmware for the device. **CAUTION** does not set the version in central - So it might not match and therefore throw errors'
    )
    parser.add_argument('--group',
                        default='default',
                        help='Group for the devices in central')
    parser.add_argument('--client-id-file',
                        '-i',
                        help='Client id file',
                        default='client_id.json')
    parser.add_argument('--credential-file',
                        '-c',
                        help='Client id file',
                        default='credential.json')
    parser.add_argument('--endpoint-file',
                        '-e',
                        help='Client id file',
                        default='endpoint.json')
    parser.add_argument('--no-excel',
                        action='store_false',
                        dest='excel',
                        help='Enable excel module')
    parser.add_argument('--excel-file',
                        default='log.xlsx',
                        help='Excel log file')
    parser.add_argument('--excel-dir',
                        default='./out',
                        help='Path for excel files to be stored for download')
    parser.add_argument(
        '--download-url',
        default='/out',
        help='URL from which the excel download will be served')
    parser.add_argument(
        '--excel-persist',
        action='store_true',
        help=
        'Instead of deleteing the excel file after a session completes keep it'
    )

    args = parser.parse_args()

    endpoint_file = args.endpoint_file  # "./endpoint.json"
    client_id_file = args.client_id_file  # "./client_id.json"
    credential_file = args.credential_file  # "./credential.json"

    APIKeySetupAndCheck(endpoint_file=endpoint_file,
           client_id_file=client_id_file,
           credential_file=credential_file).check_and_wait_create()

    excel_file = None
    excel_dir = None
    download_url = None
    if args.excel:
        excel_file = args.excel_file
        excel_dir = args.excel_dir
        download_url = args.download_url

    excel_persist = args.excel_persist

    group = args.group
    target_firmware = args.firmware

    # Extract base_url from endpoint configuration file
    base_url = None
    with open(endpoint_file, 'r') as f:
        base_url = json.load(f)['base_url']

    # Configure central api client using credential provided via `client_id_file` and `credential_file`
    central_client = Central(base_url,
                             backend='httpx',
                             auth=CentralTokenAuth(
                                 base_url=base_url,
                                 client_id_file=client_id_file,
                                 credential_file=credential_file))

    # Local Firmware checking module
    cfu = CentralFirmwareUpgrade(central_client=central_client,
                                 group=group,
                                 target_firmware=target_firmware)

    cen_dec = CentralDecomission(central_client=central_client,
                                 device_type='all')

    # Check if we should provide the web interface
    if args.web:
        print('Running in web mode')
        app = web.Application()

        routes = [
            web.static('/app', './web', show_index=True),
            web.get(
                '/firmware/ws',
                FWWebsocketHandler(
                    cfu=cfu,
                    excel_dir=excel_dir,
                    download_url=download_url,
                    excel_persist=excel_persist).websocket_handler),
            web.get('/firmware', fw_redir_handler),
            web.get(
                '/decomission/ws',
                DECWebsocketHandler(
                    cen_dec=cen_dec,
                    excel_dir=excel_dir,
                    download_url=download_url,
                    excel_persist=excel_persist).websocket_handler),
            web.get('/decomission', dec_redir_handler),
            web.get(
                '/',
                WebRoot(routes=[{
                    'name': 'Firmware',
                    'url': '/firmware'
                }, {
                    'name': 'Decomission',
                    'url': '/decomission'
                }]).web_root_handler)
        ]
        if excel_dir and download_url:
            routes.append(web.static(download_url, excel_dir), )
        app.router.add_routes(routes)
        web.run_app(app, host=args.web_address, port=args.web_port)
    elif args.console:
        print('Running in local mode')

        asyncio.run(local_decomission(
            cen_dec=cen_dec,
            excel_file=excel_file,
        ))

        # asyncio.run(local_firmware_check(
        #     cfu=cfu,
        #     excel_file=excel_file,
        # ))

    print('Please specify either --web or --console')


async def local_firmware_check(cfu: CentralFirmwareUpgrade,
                               excel_file: typing.Union[str, None] = None):
    # For logs to excel
    excel_handler = None
    if excel_file:
        print(f'Excel {excel_file}')
        excel_handler = FirmwareExcelHandler(excel_file)

    comm_handler = CommunicationHandler()

    await cfu.refresh_gateways(comm_handler=comm_handler)

    client_handler = FirmwareUpgradeHandler(cfu,
                                            comm_handler=comm_handler,
                                            excel_handler=excel_handler)
    while True:

        await comm_handler.print_log()
        await comm_handler.print_log('Serial Number')

        await client_handler.handle_input(serial=str(input()).strip())


async def local_decomission(cen_dec: CentralDecomission,
                            excel_file: typing.Union[str, None] = None):
    # For logs to excel
    excel_handler = None
    if excel_file:
        print(f'Excel {excel_file}')
        excel_handler = DecomissionExcelHandler(excel_file)

    comm_handler = CommunicationHandler()

    await cen_dec.refresh_devices(comm_handler=comm_handler)

    client_handler = DecomissionHandler(cen_dec=cen_dec,
                                        comm_handler=comm_handler,
                                        excel_handler=excel_handler)

    while True:
        await comm_handler.print_log()
        await comm_handler.print_log('Serial Number')

        await client_handler.handle_input(serial=str(input()).strip(),
                                          options={'unlicense': False})


if __name__ == '__main__':
    main()
