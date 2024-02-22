# 🤖 Conspector

**Conspector** is a _Pytest_ project dedicated to Mercury's functional tests on a component level. We test how the component behaves using real environments and services it interacts with.

## ⚙️ Installation & Usage

##### Local run:

1. With `python` > `v3.7.0` install all the packages listed in [requirements.txt](https://github.com/StarOfService/conspector/blob/master/requirements.txt) file;
2. Check [pytest.ini](https://github.com/StarOfService/conspector/blob/master/pytest.ini) to see all available markers and CLi options adopted by default;
3. Run the suite: `$ pytest --start_url mercury.qa.starofservice.com`
4. Use `-m` option for triggering the run of a specific test case(s) or a class(es): `$ pytest -m conversations`; 

## 🧩 Test suite structure
The suite structure:
```
|-- Conversations module :
|   |---- As a system, I want to create a booking conversation between users.
|   |---- As a participant, I want to get all my conversations.
|   |---- As a participant, I want to get a particular conversation.
|
|-- Sending Messages module:
|   |---- As a participant, I want to send a text message.
|   |---- As a participant, I want to send a text message with attachments.
|   |---- As a participant, I want to send attachments.
|...
```

#### The logic of the tests is following:
- **Schema validation**: fetching the schema with [gql client](https://gql.readthedocs.io/en/v3.0.0a5/usage/validation.html#using-introspection) directly from the server (when **introspection** enabled);
- **Data validation**: checking that each field has the expected values (e.g. user data is as expected, etc.);
- **Elapsed time assertion**: checking the elapsed time is =< expected.
 
## 💼 References:
- [Mercury repository](https://github.com/StarOfService/mercury)
- [GQL-3 documentation](https://gql.readthedocs.io/en/v3.0.0a5/index.html)
- [Pytest documentation](https://docs.pytest.org/en/stable/)