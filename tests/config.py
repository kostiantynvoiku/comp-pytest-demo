import re
import json


class Config:
    def __init__(self, env, start_url, jwt_key):
        start_url = re.search(r'(?:https?://)?(?:www\.)?([^/]+)(?=/|$)', start_url).group(1)
        self.start_url = start_url

        if env is None:
            self.env = {
                'localhost:8009': 'dev',
                'mercury.sandbox.starofservice.com': 'sandbox',
                'mercury.starofservice.com': 'prod'
            }[start_url]
        else:
            self.env = env

        prefix = 'http' if self.env == 'dev' else 'https'
        ws_prefix = 'ws' if self.env == 'dev' else 'wss'
        self.graphql_endpoint = f"{prefix}://{start_url}/graphql"
        self.wss_endpoint = f"{ws_prefix}://{start_url }/graphql-ws"
        if jwt_key is None:
            with open('access_keys.json') as f:
                keys = json.load(f)
                print(f"KEY: {keys.get('jwt_key')}")
            self.jwt_key = keys.get('jwt_key', None)
        else:
            self.jwt_key = jwt_key

        self.gql_headers = {
            'Authorization': '',
            'Country': 'fr',
            'User-Agent': 'SOS.ApiRequestTask/1.0'
        }

        self.api_headers = {
            "User-Agent": "SOS.ApiRequestTask/1.0",
            "Content-Type": "application/json",
            "Accept": "application/vnd.api+json",
        }

        self.time_assert = 2000
