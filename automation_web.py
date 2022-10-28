import gettext
import locale
import os

import argparse
import asyncio
import json
import typing

from aiohttp import web

from CentralAPI.APIKeySetupAndCheck import APIKeySetupAndCheck
from CentralAPI.CentralAPI import Central
from CentralTokenAuth.CentralTokenAuth import CentralTokenAuth
from Communication.CommunicationHandler import CommunicationHandler
from Decomission.CentralDecomission import CentralDecomission
from Decomission.DecomissionExcelHandler import DecomissionExcelHandler
from Decomission.DecomissionHandler import DecomissionHandler
from Decomission.DecomissionHandler import redir_handler as dec_redir_handler
from Decomission.DECWebsocketHandler import DECWebsocketHandler
from Firmware.CentralFirmwareUpgrade import CentralFirmwareUpgrade
from Firmware.FirmwareExcelHandler import FirmwareExcelHandler
from Firmware.FirmwareUpgradeHandler import FirmwareUpgradeHandler
from Firmware.FirmwareUpgradeHandler import redir_handler as fw_redir_handler
from Firmware.FWWebsocketHandler import FWWebsocketHandler

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

    # Localization
    localedir = './locale'
    translate_de = gettext.translation('messages', localedir, languages=['de'])
    translate_en = gettext.translation('messages', localedir, languages=['en'])

    if 'LANG' in os.environ and 'de' in os.environ['LANG']:
        translate_de.install()
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
    else:
        translate_en.install()

    # Arguments Parsing
    parser = argparse.ArgumentParser(
        description=_('Check Gateway Fírmware status.'))
    parser.add_argument('-w',
                        '--web',
                        help=_('Launch using web api and interface'),
                        action='store_true')
    parser.add_argument(
        '--console',
        help=_('Lauch locally using a simplistic command line interface'),
        action='store_true',
        default=True)
    parser.add_argument('--web-port',
                        type=int,
                        default=8080,
                        help=_('Specify the port for webserver'))
    parser.add_argument('--web-address',
                        type=str,
                        default='127.0.0.1',
                        help=_('Specify the address for webserver'))
    parser.add_argument(
        '--firmware',
        help=
        _('Override target firmware for the device. **CAUTION** does not set the version in central - So it might not match and therefore throw errors'
          ))
    parser.add_argument('--group',
                        default='default',
                        help=_('Group for the devices in central'))
    parser.add_argument('--client-id-file',
                        '-i',
                        help=_('Client id file'),
                        default='client_id.json')
    parser.add_argument('--credential-file',
                        '-c',
                        help=_('Client id file'),
                        default='credential.json')
    parser.add_argument('--endpoint-file',
                        '-e',
                        help=_('Client id file'),
                        default='endpoint.json')
    parser.add_argument('--no-excel',
                        action='store_false',
                        dest='excel',
                        help=_('Enable excel module'))
    parser.add_argument('--excel-file',
                        default='log.xlsx',
                        help=_('Excel log file'))
    parser.add_argument(
        '--excel-dir',
        default='./out',
        help=_('Path for excel files to be stored for download'))
    parser.add_argument(
        '--download-url',
        default='/out',
        help=_('URL from which the excel download will be served'))
    parser.add_argument(
        '--excel-persist',
        action='store_true',
        help=
        _('Instead of deleteing the excel file after a session completes keep it'
          ))
    parser.add_argument('--lang', help=_('Language option'))

    args = parser.parse_args()

    if 'de' == args.lang:
        translate_de.install()
        locale.setlocale(locale.LC_ALL, 'de_DE.UTF-8')
    elif 'en' == args.lang:
        translate_en.install()

    endpoint_file = args.endpoint_file  # "./endpoint.json"
    client_id_file = args.client_id_file  # "./client_id.json"
    credential_file = args.credential_file  # "./credential.json"

    APIKeySetupAndCheck(
        endpoint_file=endpoint_file,
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

    # Local Decomissioning module
    cen_dec = CentralDecomission(central_client=central_client,
                                 device_type='all')

    # cen_com = CentralComisison(central_client=central_client,
    #                              device_type='all')

    # Check if we should provide the web interface
    if args.web:
        print(_('Running in web mode'))
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
        print(_('Running in local mode'))

        print(
            _('Decomission {decomission} or Firmware {firmware}').format(
                decomission='d', firmware='f'))
        mode = ''
        while mode not in ['f', 'd']:
            mode = input('d/f: ')
            print(_('Operation mode unknown'))

        if mode == 'd':
            asyncio.run(
                local_decomission(
                    cen_dec=cen_dec,
                    excel_file=excel_file,
                ))
        elif mode == 'f':
            asyncio.run(local_firmware_check(
                cfu=cfu,
                excel_file=excel_file,
            ))

        print(_('Operation mode unknown'))

    print(_('Please specify either --web or --console'))


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
        await comm_handler.print_log(_('Serial Number'))

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
        await comm_handler.print_log(_('Serial Number'))

        await client_handler.handle_input(serial=str(input()).strip(),
                                          options={'unlicense': False})


if __name__ == '__main__':
    main()
