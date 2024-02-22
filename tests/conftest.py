import jwt
from datetime import datetime, timedelta
from pytest import fixture
from .config import Config
from .queries import Queries


def pytest_addoption(parser):
    parser.addoption(
        "--env",
        action="store",
        help="Environment to run tests against"
    )
    parser.addoption(
        "--start_url",
        action="store",
        help="Domain to run test against",
        default="mercury.sandbox.starofservice.com"
    )
    parser.addoption(
        '--jwt_key',
        action='store',
        help='JWT secret key for Auth tokens'
    )


@fixture(scope='session')
def get_param(request):
    config_param = {
        "env": request.config.getoption("--env"),
        "start_url": request.config.getoption("--start_url"),
        'jwt_key': request.config.getoption('--jwt_key'),
    }
    return config_param


@fixture(scope='session')
def env_config(get_param):
    cfg = Config(get_param['env'], get_param['start_url'], get_param['jwt_key'])
    return cfg


@fixture(scope="session")
def create_users(env_config):
    user1_data = dict()
    user2_data = dict()
    for i in [user1_data, user2_data]:
        uuid = f"user-conspector-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
        jwt_token = jwt.encode({"id": uuid, "super_admin": True, "iat": datetime.utcnow(),
                                "exp": datetime.utcnow() + timedelta(minutes=30)},
                               env_config.jwt_key, algorithm="HS256")
        i.update({
            'uuid': uuid,
            'jwt_token': jwt_token
        })
    return user1_data, user2_data


@fixture(scope="session")
def create_conversation(env_config, create_users):
    queries = Queries()
    user1, user2 = create_users
    params = {"participant": user2['uuid']}
    result, _ = queries.execute_gql(endpoint=env_config.graphql_endpoint,
                                    user=user1,
                                    headers=env_config.gql_headers,
                                    raw_body='resources/gql_payload/mutations/createConversation_fixture_cut.graphql',
                                    params=params)
    print(
        f"[INFO] Conversation created: {result['createConversation']['conversation']['id']}")
    return result


@fixture(scope="function")
def send_text_message(env_config, create_users, create_conversation):
    queries = Queries()
    user1, _ = create_users
    conversation_id = create_conversation['createConversation']['conversation']['id']
    message = "This is my text message"
    params = {"conversation_id": conversation_id,
              "message": message}
    result, _ = queries.execute_gql(endpoint=env_config.graphql_endpoint,
                                    user=user1,
                                    headers=env_config.gql_headers,
                                    raw_body='resources/gql_payload/mutations/sendTextMessage_fixture_cut.graphql',
                                    params=params)
    print(
        f"[INFO] Message sent, messageId: {result['sendTextMessage']['message']['id']}")
    return result


@fixture(scope="function")
def get_messages_by_conversation(env_config, create_users, create_conversation, send_text_message):
    queries = Queries()
    _, user2 = create_users
    conversation_id = create_conversation['createConversation']['conversation']['id']
    message = "This is my text message"
    params = {"conversation_id": conversation_id,
              "message": message}
    result, _ = queries.execute_gql(endpoint=env_config.graphql_endpoint,
                                    user=user2,
                                    headers=env_config.gql_headers,
                                    raw_body='resources/gql_payload/queries/messagesByConversation.graphql',
                                    params=params)
    return result
