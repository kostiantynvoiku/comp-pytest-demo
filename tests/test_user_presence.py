# ruff: noqa: E501
import asyncio
import backoff
from pytest import mark, fail
from datetime import datetime, timedelta
from tests.queries import Queries, AsyncQueries


@mark.user_presence
class UserPresenceTests:

    @mark.last_seen
    def test_as_a_logged_in_user_i_want_to_indicate_that_i_am_online(self, env_config, create_users):
        """
        TEST CASE:
        1. Create 1 user;
        2. User sends 'lastSeen' mutation;
        3. Assert 'lastSeen' has returned 'success: True'.

        """
        q = Queries()
        user1, _ = create_users
        event_name = 'lastSeen'
        result, elapsed = q.execute_gql(endpoint=env_config.graphql_endpoint,
                                        user=user1,
                                        headers=env_config.gql_headers,
                                        raw_body=f'resources/gql_payload/mutations/{event_name}.graphql')
        # ---- ASSERTIONS ---- :
        assert result[event_name]['success']
        assert elapsed <= env_config.time_assert
        print(
            f"[PASSED] User '{user1['uuid']}' lastSeen:{result[event_name]['success']}")
        print(f"[INFO] Elapsed time: {elapsed} ms")

    @mark.user_online
    def test_as_a_logged_in_user_i_want_to_know_when_another_user_has_an_update_on_their_presence(self, env_config, create_users, create_conversation):
        """
        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. User1 subscribes to 'userOnline' event;
        4. User2 sends 'lastSeen' mutation;
        5. User2 receives 'userOnline' event.

        """
        async_query = AsyncQueries()
        conversation_id = create_conversation['createConversation']['conversation']['id']
        user1, user2 = create_users
        event_name = 'userOnline'

        @backoff.on_exception(backoff.expo, Exception, max_time=5)
        async def graphql_connection():
            user1_client, user2_client = async_query.create_wss_clients(
                headers=env_config.gql_headers,
                wss_endpoint=env_config.wss_endpoint,
                user1_auth=f"{user1['jwt_token']}",
                user2_auth=f"{user2['jwt_token']}")
            async with user1_client as user1_session, user2_client as user2_session:
                task1 = asyncio.create_task(
                    async_query.execute_subscription(
                        session=user1_session,
                        tag='user1',
                        raw_body=f'resources/gql_payload/subscriptions/{event_name}.graphql',
                        n_events=1,
                        params={"conversation_id": [conversation_id]}))
                task2 = asyncio.create_task(
                    async_query.execute_async_gql(
                        session=user2_session,
                        tag='user2',
                        raw_body='resources/gql_payload/mutations/lastSeen.graphql'))
                try:
                    r = await asyncio.wait_for(asyncio.gather(task1, task2), timeout=60)
                except asyncio.TimeoutError:
                    fail("Subscription got no events!")
            return r[0], r[1]
        r_task1, r_task2 = asyncio.run(graphql_connection())
        # ---- ASSERTIONS ---- :
        assert r_task1['response'][0][event_name]['user']['apiId'] == user2['uuid']
        assert r_task1['response'][0][event_name]['user']['isOnline']
        assert r_task2['response']['lastSeen']['success']
        assert r_task1['elapsed'] <= env_config.time_assert
        print(f"[INFO] 'userOnline' elapsed time: {r_task1['elapsed']} ms")
        print(f"[INFO] 'lastSeen' elapsed time: {r_task2['elapsed']} ms")

    @mark.user_meta
    def test_as_a_logged_in_user_i_want_to_get_user_meta(self, env_config, create_users):
        """
        TEST CASE:
        1. Create 1 user;
        2. User sends 'userMeta' query;
        3. Assert 'userMeta' has returned 'unreadCount' and user's data.

        """
        q = Queries()
        user1, _ = create_users
        event_name = 'userMeta'
        result, elapsed = q.execute_gql(endpoint=env_config.graphql_endpoint,
                                        user=user1,
                                        headers=env_config.gql_headers,
                                        raw_body='resources/gql_payload/queries/userMeta.graphql')
        # ---- ASSERTIONS ---- :
        assert isinstance(result[event_name]['unreadCount'], int)
        assert result[event_name]['user']['apiId'] == user1['uuid']
        assert elapsed <= env_config.time_assert
        print(f"[PASSED] User '{user1['uuid']}' meta:{result[event_name]}")
        print(f"[INFO] Elapsed time: {elapsed} ms")

    @mark.participants_with_unread_messages
    def test_as_system_i_want_to_get_a_list_of_users_with_unread_messages(self, env_config, create_users):

        q = Queries()
        user1, _ = create_users
        event_name = 'participantsWithUnreadMessages'
        time = datetime.now() - timedelta(hours=24)
        timestamp = round(time.timestamp())
        result, elapsed = q.execute_gql(endpoint=env_config.graphql_endpoint,
                                        user=user1,
                                        headers=env_config.gql_headers,
                                        raw_body='resources/gql_payload/queries/participantsWithUnreadMessages.graphql',
                                        params={"timestamp": timestamp})
        # ---- ASSERTIONS ---- :
        assert result[event_name]['edges'][0]['node']['conversation']
        assert result[event_name]['edges'][0]['node']['id']
        assert result[event_name]['edges'][0]['node']['user']['apiId']
        assert elapsed <= env_config.time_assert
        print(
            f"[PASSED] Participants with unread messages {result[event_name]}")
        print(f"[INFO] Elapsed time: {elapsed} ms")
