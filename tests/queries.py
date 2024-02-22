# ruff: noqa: E501
import asyncio
from sys import argv
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from timeit import default_timer as timer
from gql.transport.websockets import WebsocketsTransport


class Queries:

    def execute_gql(self, endpoint, user, headers, raw_body, params=None):

        introspection = True
        if 'prod' in argv:
            introspection = False

        headers["Authorization"] = f"Bearer {user['jwt_token']}"
        with open(raw_body, 'r') as f:
            request_body = f.read()
        transport = RequestsHTTPTransport(
            url=endpoint,
            use_json=True,
            headers=headers
        )
        client = Client(
            transport=transport,
            fetch_schema_from_transport=introspection,
        )
        query = gql(request_body)
        start = timer()
        result = client.execute(query, variable_values=params)
        end = timer()
        elapsed = round((end - start) * 1000)
        return result, elapsed


class AsyncQueries:

    def create_wss_clients(self, headers, wss_endpoint, user1_auth, user2_auth):
        introspection = True
        if 'prod' in argv:
            introspection = False
        user1_headers = {**headers, "Authorization": f"Bearer {user1_auth}"}
        user2_headers = {**headers, "Authorization": f"Bearer {user2_auth}"}
        user1_transport = WebsocketsTransport(
            url=wss_endpoint, init_payload=user1_headers, headers=user1_headers)
        user2_transport = WebsocketsTransport(
            url=wss_endpoint, init_payload=user2_headers, headers=user2_headers)
        user1_client = Client(transport=user1_transport,
                              fetch_schema_from_transport=introspection)
        user2_client = Client(transport=user2_transport,
                              fetch_schema_from_transport=introspection)
        return user1_client, user2_client

    async def execute_async_gql(self, session, tag, raw_body, params=None):
        with open(raw_body, 'r') as f:
            request_body = f.read()
        query = gql(request_body)
        # delay before sending query, so subscription will be active already
        await asyncio.sleep(1)
        start = timer()
        result = await session.execute(query, variable_values=params)
        end = timer()
        elapsed = round((end - start) * 1000)
        event_name = list(result.keys())[0]
        print(
            f"[INFO][{tag}]: '{event_name}' has returned the response: {result[event_name]}")
        return {'response': result, 'elapsed': elapsed}

    async def execute_subscription(self, session, tag, raw_body, n_events, params=None):
        with open(raw_body, 'r') as f:
            request_body = f.read()
        query = gql(request_body)
        counter = 0
        r = []
        elapsed = None
        start = timer()
        async for result in session.subscribe(query, variable_values=params):
            end = timer()
            elapsed = round((end - start) * 1000)
            event_name = list(result.keys())[0]
            r.append(result)
            print(
                f"[PASSED][{tag}]: Subscription '{event_name}' has returned the response: '{result[event_name]}'")
            counter += 1
            if counter >= n_events:
                break
        return {'response': r, 'elapsed': elapsed}
