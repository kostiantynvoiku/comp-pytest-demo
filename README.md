# 🤖 Pytest: GraphQL Component Testing Demo

This is a [Pytest](https://pytest.org) project dedicated to [GraphQL](https://graphql.org/) component's functional tests. We test how the component behaves using real environments and services it interacts with.

## ⚙️ Installation & Usage

##### Local run:

1. With `python` > `v3.7.0` install all the packages listed in [requirements.txt](https://github.com/StarOfService/conspector/blob/master/requirements.txt) file;
2. Check [pytest.ini](https://github.com/StarOfService/conspector/blob/master/pytest.ini) to see all available markers and CLi options adopted by default;
3. Run the suite: `$ pytest`
4. Use `-m` option for triggering the run of a specific test case(s) or a class(es): `pytest -m conversations`; 

## 🧩 Test suite structure
The suite structure:
```
|-- Conversations module :
|   |---- As a system, I want to create a conversation between users.
|   |---- As a participant, I want to get all my conversations.
|   |---- As a participant, I want to get a particular conversation.
|
|-- User Presence module:
|   |---- As a logged-in user, I want to indicate that I am online.
|   |---- As a logged-in user, I want to know when another user has an update on their presence.
|   |---- As a system, I want to get a list of users with unread messages.
|...
```

#### The logic of the tests is following:
- **Schema validation**: fetching the schema with [gql client](https://gql.readthedocs.io/en/v3.0.0a5/usage/validation.html#using-introspection) directly from the server (when **introspection** enabled);
- **Data validation**: checking that each field has the expected values (e.g. user data is as expected, etc.);
- **Elapsed time assertion**: checking the elapsed time is =< expected.
 
## 💼 References:
- [GQL-3 documentation](https://gql.readthedocs.io/en/v3.0.0a5/index.html)
- [Pytest documentation](https://docs.pytest.org/en/stable/)