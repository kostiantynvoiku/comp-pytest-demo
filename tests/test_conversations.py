# ruff: noqa: E501
from pytest import mark
from datetime import datetime, timedelta
from tests.queries import Queries


@mark.conversations
class ConversationTests:

    @mark.create_conversation
    def test_as_a_system_i_want_to_create_a_conversation_between_users(self, env_config, create_users):
        """
        :param env_config: fetch the environment configs: mercury_endpoint, domain, ect.
        :param create_users: fetch auth data and uuid of the users.

        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. Assert conversation has been created correctly.

        """
        # Fetch data from fixtures:
        queries = Queries()
        user1, user2 = create_users
        params = {"participant": user2['uuid']}
        time_now = datetime.utcnow()
        time_now_formatted = datetime.utcnow().strftime('%Y-%m-%dT%H:%M')
        event_name = 'createConversation'
        result, elapsed = queries.execute_gql(endpoint=env_config.mercury_endpoint,
                                              user=user1,
                                              headers=env_config.gql_headers,
                                              raw_body=f'resources/gql_payload/mutations/{event_name}.graphql',
                                              params=params)
        # ---- ASSERTIONS ---- :
        assert result[event_name]['conversation']['createdAt'][:16] in [time_now_formatted,
                                                                        (time_now + timedelta(minutes=1)).strftime(
                                                                            '%Y-%m-%dT%H:%M')]
        assert len(result[event_name]['conversation']['id']) > 0
        assert result[event_name]['conversation']['title'] == "Test conversation"
        assert result[event_name]['conversation']['creator']['apiId'] == user1['uuid']
        assert len(result[event_name]['conversation']['creator']['id']) > 0
        assert not result[event_name]['conversation']['creator']['isOnline']
        assert not result[event_name]['conversation']['creator']['lastSeen']
        assert all(participant['node']['apiId'] in [user1['uuid'], user2['uuid']]
                   for participant in result[event_name]['conversation']['participants']['edges']
                   ), f"Users '{user1['uuid']}' or '{user2['uuid']}' not found in participants"
        assert elapsed <= env_config.time_assert
        print(f"[PASSED] Conversation created: {result[event_name]['conversation']['id']}")
        print(f"[INFO] Elapsed time: {elapsed} ms")

    @mark.get_conversations
    def test_as_a_participant_i_want_to_get_all_my_conversations(self, env_config, create_users, create_conversation):
        """
        :param env_config: fetch the environment configs: mercury_endpoint, domain, ect.
        :param create_users: fetch auth data and uuid of the users.
        :param create_conversation: fetch conversation_id.

        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. Get all conversation for User1.

        """
        queries = Queries()
        conversation_id = create_conversation['createConversation']['conversation']['id']
        user1, user2 = create_users
        event_name = 'conversations'
        params = {"conversation_id": conversation_id, "tagsFilter": "-"}
        result, elapsed = queries.execute_gql(endpoint=env_config.mercury_endpoint,
                                              user=user1,
                                              headers=env_config.gql_headers,
                                              raw_body=f'resources/gql_payload/queries/{event_name}.graphql',
                                              params=params)
        # ---- ASSERTIONS ---- :
        edges = len(result[event_name]['edges'])
        assert edges >= 1
        for e in range(0, edges):
            if result[event_name]['edges'][e]['node']['id'] == conversation_id:
                cursor = result[event_name]['edges'][e]['cursor']
                assert len(cursor) > 0
                assert cursor in result[event_name]['pageInfo'].values()
                assert result[event_name]['edges'][e]['node']['title'] == "Test conversation"
                assert result[event_name]['edges'][e]['node']['creator']['apiId'] == user1['uuid']
                assert result[event_name]['edges'][e]['node']['lastMessage'] is None
                assert result[event_name]['edges'][e]['node']['participants']['edges'][0]['node']['apiId'] == \
                       user1['uuid']
                assert result[event_name]['edges'][e]['node']['participants']['edges'][1]['node']['apiId'] == \
                       user2['uuid']
                break
        assert not result[event_name]['pageInfo']['hasNextPage']
        assert not result[event_name]['pageInfo']['hasPreviousPage']
        assert elapsed <= env_config.time_assert
        print(f"[PASSED] Conversation fetched: {conversation_id}")
        print(f"[INFO] Elapsed time: {elapsed} ms")

    @mark.conversations_with
    def test_as_a_participant_i_want_to_get_all_my_conversations_with_specific_participants(self, env_config,
                                                                                            create_users,
                                                                                            create_conversation):
        """
        :param env_config: fetch the environment configs: mercury_endpoint, domain, ect.
        :param create_users: fetch auth data and uuid of the users.
        :param create_conversation: fetch conversation_id.

        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. Get all conversations with specific participants.

        """
        queries = Queries()
        conversation_id = create_conversation['createConversation']['conversation']['id']
        user1, user2 = create_users
        params = {"user_id": user2['uuid'], "tagsFilter": "-"}
        event_name = 'conversationsWith'
        result, elapsed = queries.execute_gql(endpoint=env_config.mercury_endpoint,
                                              user=user1,
                                              headers=env_config.gql_headers,
                                              raw_body='resources/gql_payload/queries/conversationsWith.graphql',
                                              params=params)
        # ---- ASSERTIONS ---- :
        edges = len(result[event_name]['edges'])
        assert edges >= 1
        is_param_found = False
        for e in range(0, edges):
            for key, dict in result[event_name]['edges'][e].items():
                for subkey, subvalue in dict.items():
                    if subvalue == conversation_id:
                        is_param_found = True
                        break
        assert is_param_found
        assert elapsed <= env_config.time_assert
        print(f"[PASSED] Conversation fetched: {conversation_id}")
        print(f"[INFO] Elapsed time: {elapsed} ms")

    @mark.add_conversation_tag
    def test_as_a_participant_i_want_to_add_conversation_tag(self, env_config, create_users, create_conversation):
        """
        :param env_config: fetch the environment configs: mercury_endpoint, domain, ect.
        :param create_users: fetch auth data and uuid of the users.
        :param create_conversation: fetch conversation_id.

        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. Add tag to the conversation;
        4. Assert tag added;

        """
        # Fetch data from fixtures:
        queries = Queries()
        conversation_id = create_conversation['createConversation']['conversation']['id']
        conversation_api_id = create_conversation['createConversation']['conversation']['apiId']
        user1, _ = create_users
        params = {"conversationApiId": conversation_api_id, "tagName": "conspector"}
        event_name = 'addConversationTag'

        # Add tag to the conversation:
        _, elapsed = queries.execute_gql(endpoint=env_config.mercury_endpoint,
                                         user=user1,
                                         headers=env_config.gql_headers,
                                         raw_body=f'resources/gql_payload/mutations/{event_name}.graphql',
                                         params=params)
        assert elapsed <= env_config.time_assert
        print(f"[INFO] Elapsed time: {elapsed} ms")

        # Assert tag has been added :
        event_name = 'conversations'
        params = {"conversation_id": conversation_id, "tagsFilter": "conspector"}
        result, _ = queries.execute_gql(endpoint=env_config.mercury_endpoint,
                                        user=user1,
                                        headers=env_config.gql_headers,
                                        raw_body=f'resources/gql_payload/queries/{event_name}.graphql',
                                        params=params)
        edges = len(result[event_name]['edges'])
        assert edges >= 1
        for e in range(0, edges):
            if result[event_name]['edges'][e]['node']['id'] == conversation_id:
                assert result[event_name]['edges'][e]['node']['creator']['apiId'] == user1['uuid']
                assert result[event_name]['edges'][e]['node']['tags'] == ['conspector']
                break
        print(f"[PASSED] Conversation with tag 'conspector' found: {conversation_id}")

    @mark.remove_conversation_tag
    def test_as_a_participant_i_want_to_remove_conversation_tag(self, env_config, create_users, create_conversation):
        """
        :param env_config: fetch the environment configs: mercury_endpoint, domain, ect.
        :param create_users: fetch auth data and uuid of the users.
        :param create_conversation: fetch conversation_id.

        TEST CASE:
        1. Create 2 users;
        2. Create a conversation;
        3. Remove tag from the conversation;
        4. Assert tag removed;

        """
        # Fetch data from fixtures:
        queries = Queries()
        conversation_id = create_conversation['createConversation']['conversation']['id']
        conversation_api_id = create_conversation['createConversation']['conversation']['apiId']
        user1, _ = create_users
        event_name = 'removeConversationTag'

        # Remove tag from the conversation:
        params = {"conversationApiId": conversation_api_id, "tagName": "conspector"}
        _, elapsed = queries.execute_gql(endpoint=env_config.mercury_endpoint,
                                         user=user1,
                                         headers=env_config.gql_headers,
                                         raw_body=f'resources/gql_payload/mutations/{event_name}.graphql',
                                         params=params)
        assert elapsed <= env_config.time_assert
        print(f"[INFO] Elapsed time: {elapsed} ms")

        # Assert tag has been removed :
        event_name = 'conversations'
        params = {"conversation_id": conversation_id, "tagsFilter": "conspector"}
        result, _ = queries.execute_gql(endpoint=env_config.mercury_endpoint,
                                        user=user1,
                                        headers=env_config.gql_headers,
                                        raw_body=f'resources/gql_payload/queries/{event_name}.graphql',
                                        params=params)
        assert len(result[event_name]['edges']) == 0
        print("[PASSED] Conversation with tag 'conspector' not found")
