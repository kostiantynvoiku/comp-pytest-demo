# ruff: noqa: E501
import asyncio
import backoff
from pytest import mark, fail
from tests.queries import Queries, AsyncQueries


@mark.delivery_read_receipts
class DeliveryReadReceiptsTests:

    @mark.message_received
    def test_as_a_participant_i_want_to_inform_that_i_have_received_a_message(self, env_config, create_users,
                                                                              send_text_message,
                                                                              get_messages_by_conversation):
        """
        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. User1 send a message to User2;
        4. User2 gets the message by conversation;
        5. Assert message is marked as 'delivered' to User2.

        """
        _, user2 = create_users
        q = Queries()
        conversation_id = get_messages_by_conversation['messagesByConversation']['edges'][0]['node'][
            'conversation']['id']
        result, _ = q.execute_gql(endpoint=env_config.mercury_endpoint,
                                        user=user2,
                                        headers=env_config.gql_headers,
                                        raw_body='resources/gql_payload/queries/messagesByConversation.graphql',
                                        params={"conversation_id": conversation_id
                                                })
        recipient = result['messagesByConversation']['edges'][-1]['node']['deliveredTo'][0][
            'apiId']
        message_id = send_text_message['sendTextMessage']['message']['id']
        assert recipient == user2['uuid']
        print(f"[PASSED] Message '{message_id}' received by {recipient}")

    @mark.mark_as_read
    def test_as_a_participant_i_want_to_let_others_know_that_i_have_read_a_message(self, env_config, create_users,
                                                                                   send_text_message):
        """
        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. User1 send a message to User2;
        4. User2 marks the message as 'Read' with 'markAsRead.graphql' query.
        """
        q = Queries()
        message_id = send_text_message['sendTextMessage']['message']['id']
        _, user2 = create_users
        event_name = 'markAsRead'
        params = {"message_id": message_id}
        result, elapsed = q.execute_gql(endpoint=env_config.mercury_endpoint,
                                        user=user2,
                                        headers=env_config.gql_headers,
                                        raw_body=f'resources/gql_payload/mutations/{event_name}.graphql',
                                        params=params)
        # ---- ASSERTIONS ---- :
        assert result[event_name]['message']['id'] == message_id
        assert result[event_name]['message']['readBy'][0]['apiId'] == user2['uuid']
        assert elapsed <= env_config.time_assert
        print(f"[PASSED] Message '{message_id}' is read by {user2['uuid']}")
        print(f"[INFO] Elapsed time: {elapsed} ms")

    @mark.message_delivered
    def test_as_a_participant_i_want_to_know_when_my_message_is_delivered_to_someone(self, env_config, create_users,
                                                                                     create_conversation,
                                                                                     send_text_message):
        """
        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. User1 sends a message to User2;
        4. User1 subscribe to 'messageDelivered.graphql' event;
        5. User2 sends 'messagesByConversation.graphql' query;
        6. User1 receives 'messageDelivered.graphql' event.
        """
        async_query = AsyncQueries()
        message_id = send_text_message['sendTextMessage']['message']['id']
        conversation_id = create_conversation['createConversation']['conversation']['id']
        user1, user2 = create_users
        event_name = 'messageDelivered'

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
                        n_events=1))
                task2 = asyncio.create_task(
                    async_query.execute_async_gql(
                        session=user2_session,
                        tag='user2',
                        raw_body='resources/gql_payload/queries/messagesByConversation.graphql',
                        params={"conversation_id": conversation_id}))
                try:
                    r = await asyncio.wait_for(asyncio.gather(task1, task2), timeout=60)
                except asyncio.TimeoutError:
                    fail("Subscription got no events!")
            return r[0], r[1]
        r_task1, r_task2 = asyncio.run(graphql_connection())
        # ---- ASSERTIONS ---- :
        assert r_task1['response'][0][event_name]['message']['id'] == message_id
        assert r_task1['response'][0][event_name]['recipient']['apiId'] == user2['uuid']
        assert r_task2['response']['messagesByConversation']['edges'][0]['node']['id'] == message_id
        assert r_task2['response']['messagesByConversation']['edges'][0]['node']['body'] == "This is my text message"
        assert r_task1['elapsed'] <= env_config.time_assert
        print(
            f"[INFO] 'messageDelivered' elapsed time: {r_task1['elapsed']} ms")
        print(
            f"[INFO] 'messagesByConversation' elapsed time: {r_task2['elapsed']} ms")

    @mark.message_read
    def test_as_a_participant_i_want_to_know_when_my_message_is_read_by_someone(self, env_config, create_users,
                                                                                send_text_message):
        """
        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. User1 sends a message to User2;
        4. User1 subscribe to 'messageRead.graphql' event;
        5. User2 sends 'markAsRead.graphql' query;
        6. User1 receives 'messageRead.graphql' event.
        """

        async_query = AsyncQueries()
        message_id = send_text_message['sendTextMessage']['message']['id']
        user1, user2 = create_users
        event_name = 'messageRead'

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
                        n_events=1))
                task2 = asyncio.create_task(
                    async_query.execute_async_gql(
                        session=user2_session,
                        tag='user2',
                        raw_body='resources/gql_payload/mutations/markAsRead.graphql',
                        params={"message_id": message_id}))
                try:
                    r = await asyncio.wait_for(asyncio.gather(task1, task2), timeout=60)
                except asyncio.TimeoutError:
                    fail("Subscription got no events!")
            return r[0], r[1]

        r_task1, r_task2 = asyncio.run(graphql_connection())
        # ---- ASSERTIONS ---- :
        assert r_task1['response'][0][event_name]['message']['id'] == message_id
        assert r_task1['response'][0][event_name]['reader']['apiId'] == user2['uuid']
        assert r_task2['response']['markAsRead']['message']['id'] == message_id
        assert r_task2['response']['markAsRead']['message']['readBy'][0]['apiId'] == user2['uuid']
        assert r_task1['elapsed'] <= env_config.time_assert
        print(f"[INFO] 'messageRead' elapsed time: {r_task1['elapsed']} ms")
        print(f"[INFO] 'markAsRead' elapsed time: {r_task2['elapsed']} ms")

    @mark.unread_messages
    def test_as_a_participant_i_want_to_get_my_unread_messages(self, env_config, create_users, create_conversation,
                                                               send_text_message):
        """
        :param env_config: fetch the environment configs: mercury_endpoint, domain, ect.
        :param create_users: fetch auth data and uuid of the users.
        :param create_conversation: fetch conversation_id.

        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. User1 sends a message to User2;
        4. User2 sends query 'unreadMessages';
        4. Assert message's data is fetched correctly.

        """
        queries = Queries()
        conversation_id = create_conversation['createConversation']['conversation']['id']
        message_id = send_text_message['sendTextMessage']['message']['id']
        _, user2 = create_users
        event_name = "unreadMessages"
        result, elapsed = queries.execute_gql(endpoint=env_config.mercury_endpoint,
                                              user=user2,
                                              headers=env_config.gql_headers,
                                              raw_body='resources/gql_payload/queries/unreadMessages.graphql',
                                              params={"conversation_id": conversation_id})
        # ---- ASSERTIONS ---- :
        assert result[event_name]['edges'][0]['node']['id'] == message_id
        assert result[event_name]['edges'][0]['node']['body'] == "This is my text message"
        assert elapsed <= env_config.time_assert
        print(f"[PASSED] Got unread message: {message_id}")
        print(f"[INFO] Elapsed time: {elapsed} ms")
