import json
from datetime import datetime, timedelta

import httpx


class CentralTokenAuth(httpx.Auth):
    requires_request_body = False
    requires_response_body = True

    def __init__(self, base_url, client_id_file, credential_file):
        self.credential_file = credential_file
        self.base_url = base_url
        self.client_id_file = client_id_file
        self.client_id = ''
        self.client_secret = ''
        self.grant_type = 'refresh_token'

        # Load the credential file
        with open(self.credential_file, 'r') as f:
            cred_data = json.load(f)

            self.access_token = cred_data['access_token']
            self.refresh_token = cred_data['refresh_token']
            self.expires_in = cred_data['expires_in']
            self.created_at = cred_data['created_at']

        # Load the client_id and client_secret
        # Used if we need to update the token
        with open(self.client_id_file, 'r') as f:
            client_data = json.load(f)

            self.client_id = client_data['client_id']
            self.client_secret = client_data['client_secret']

        self.expiry = None

    def auth_flow(self, request):
        # Send the request, with bearer.
        request.headers['Authorization'] = f'Bearer {self.access_token}'
        response = yield request

        if response.status_code == 401:
            refresh_response = yield self.build_refresh_request()
            self.update_tokens(refresh_response)

            # Set new Bearer
            request.headers['Authorization'] = f'Bearer {self.access_token}'
            yield request

    def build_refresh_request(self):
        return httpx.Request(method='POST',
                             url=f'{self.base_url}/oauth2/token',
                             params={
                                 'client_id': self.client_id,
                                 'client_secret': self.client_secret,
                                 'grant_type': self.grant_type,
                                 'refresh_token': self.refresh_token
                             },
                             headers={"Accept": "application/json"})

    def update_tokens(self, response):
        if response.status_code == 200:
            # Successfully updated token
            data = response.json()
            self.refresh_token = data['refresh_token']
            self.access_token = data['access_token']
            self.expiry = datetime.now() + \
                timedelta(seconds=data['expires_in'])
            self.expires_in = data['expires_in']
            self.created_at = int(datetime.now().timestamp())
            print('Expiry', self.expiry.isoformat())
            # Save the new credential to disk
            self.write_credentials_to_json()

    def write_credentials_to_json(self):
        with open(self.credential_file, 'r+') as f:
            # Load the old data from file
            cred_data = json.load(f)
            print('Expires In', self.expires_in)
            print('Created At', self.created_at)
            # Overwrite the changed values
            cred_data['access_token'] = self.access_token
            cred_data['refresh_token'] = self.refresh_token
            cred_data['expires_in'] = self.expires_in
            cred_data['created_at'] = self.created_at
            # Return to top
            f.seek(0)
            f.truncate(0)
            # Dump the json to file and overwrite
            json.dump(cred_data, f)
