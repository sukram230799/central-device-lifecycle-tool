from http import client
import json
import os.path

from decorest import endpoint


class APIKeySetupAndCheck():

    def __init__(self, endpoint_file: str, client_id_file: str,
                 credential_file: str) -> None:
        self.endpoint_file = endpoint_file
        self.client_id_file = client_id_file
        self.credential_file = credential_file
        pass

    def check_and_wait_create(self):
        while not self.check_endpoint():
            while not self.create_endpoint():
                print(_('Failed'))
        while not self.check_client_id():
            while not self.create_client_id():
                print(_('Failed'))
        while not self.check_credential():
            while not self.create_credential():
                print(_('Failed'))

        print(_('Endpoint, Client_ID and Credential exist. Continue'))
        return True

    def check_endpoint(self) -> bool:
        try:
            with open(self.endpoint_file, 'r') as f:
                base_url = json.load(f)['base_url']
        except:
            return False
        return True

    def check_client_id(self) -> bool:
        try:
            with open(self.client_id_file, 'r') as f:
                client_data = json.load(f)

                client_id = client_data['client_id']
                client_secret = client_data['client_secret']

        except:
            return False
        return True

    def check_credential(self) -> bool:
        try:
            with open(self.credential_file, 'r') as f:
                cred_data = json.load(f)

                access_token = cred_data['access_token']
                refresh_token = cred_data['refresh_token']
                expires_in = cred_data['expires_in']
                created_at = cred_data['created_at']
        except:
            return False
        return True

    def create_endpoint(self) -> bool:
        try:
            print(_('Please paste an endpoint URL.'))
            url = str(input()).strip()
            with open(self.endpoint_file, 'w') as f:
                endpoint = {"name": "AUTO GENERATED", "base_url": url}

                f.write(json.dumps(endpoint))
                f.flush()
                f.close()
                return True
        except:
            return False

    def create_client_id(self) -> bool:
        try:
            print(_('Please paste the client id.'))
            client_id = str(input()).strip()
            print(_('Please paste the client secret.'))
            client_secret = str(input()).strip()
            with open(self.client_id_file, 'w') as f:
                client_id_data = {
                    "client_id": client_id,
                    "client_secret": client_secret
                }

                f.write(json.dumps(client_id_data))
                f.flush()
                f.close()
                return True
        except:
            return False

    def create_credential(self) -> bool:
        try:
            print(
                _('Please paste the full credential file from central. Then enter until okay.'
                  ))

            credential_json = self.json_import()
            with open(self.credential_file, 'w') as f:
                f.write(json.dumps(credential_json))
                f.flush()
                f.close()
                return True
        except:
            return False

    @staticmethod
    def json_import() -> dict:
        json_string = ''
        last_line = None
        while not last_line == '':
            last_line = input()
            json_string += last_line
        return json.loads(json_string)
