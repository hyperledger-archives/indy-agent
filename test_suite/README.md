Indy Agent Test Suite
=====================

This is the Indy Agent Test Suite used to certify standards compliance and interoperability.

The tests run by this test suite are based on approved Hyperledger Indy Project Enhancement (HIPE) proposals.

As the test suite matures, documentation will be added on how to create and add tests to the suite.

Requirements
------------
- Python 3.6
- `libindy` version 1.8.0 from https://github.com/hyperledger/indy-sdk

Quickstart
----------

### Step 1: Install dependencies
Create a python virtual environment for installing dependencies. From the `test-suite` directory:

```sh
python -m venv env
source env/bin/activate
```

You may have to specify `python3` depending on the default python version for your system.

This will create and activate a virtual environment in the `env` directory using the python `venv` module. You may
have to install this module through your system package manager or pip.

Then install dependencies by running:

```sh
pip install -r requirements.txt
```

Ensure `libindy` is in your `LD_LIBRARY_PATH` (if you built from source).

### Step 2: Configure the test suite

Configuration options are listed in `config.toml`. Descriptions of each option are given there.

The defaults are as follows:

Option | Value
-------|-------
Testing Agent (test-suite) Host and Port | `localhost:3000`
Testing Agent Message URL | `http://localhost:3000/indy`
Tested Agent Message URL | `http://localhost:3001/indy`
Transport Protocol | HTTP
Testing agent wallet | `testing-agent`
Wallet Path | `.testing-wallets`
Clear wallets (delete wallet after testing complete) | `true`
Log level | Warning (`30`)
Tests | `core.manual`

> **Note:** Some of these defaults don't make as much sense when considering other transport methods like bluetooth or
> NFC or others. When the need (and implementation) arises for these other transport options, the structure of these
> settings will likely change.

You will need to alter the above settings to match your needs.

### Step 3: Start the tested agent

Follow the instructions for starting the agent you are attempting to test.

### Step 4: Run the test suite

```sh
./agtest
```

This will execute the tests selected in `config.toml`.

Command Line Options
--------------------

`agtest` is a wrapper around `pytest`. All `pytest` commandline arguments are valid for `agtest`. The Agent Test Suite
also defines additional arguments.

- `--sc=CONFIG_PATH`, `--suite-config=CONFIG_PATH` - Specify a config file, overriding the default location
	(`./config.toml`).

- `-F REGEX`, `--feature-select=REGEX` - Feature selection based on a regular expression. This overrides the features
	selected in the configuration file.


For a full list of supported arguments, run

```sh
./agtest --help
```

Writing Tests
-------------

Tests follow standard `pytest` conventions. However, due to the asynchronous nature of most Indy-SDK calls and agent
messaging, most tests will likely need `await` a promise and must be marked as asynchronous, e.g.:

```python
@pytest.mark.asyncio
async def test_method():
	await some_indy_sdk_call()
```

Several tools are made available through the test suite to simplify some common tasks.

------------------------------------------------------------------------------------------------------------------------

### Marking Features

Assigning tests to features is done through `pytest` marks. A single test can be marked with an annotation:

```python
@pytest.mark.asyncio
@pytest.mark.features('my_feature')
async def test_method():
	await some_indy_sdk_call()
```

Multiple features can be assigned with a single mark:

```python
@pytest.mark.asyncio
@pytest.mark.features('my_feature', 'my_other_feature')
async def test_method():
	await some_indy_sdk_call()
```

A python class can also be marked in the same manner, allowing all tests belonging to that class to be marked with a
single annotation:

```python

@pytest.mark.features('my_feature')
class MyTestClass:

	@pytest.mark.asyncio
	async def test_method_marked_with_my_feature(self):
		await some_indy_sdk_call()

	@pytest.mark.asyncio
	async def test_another_method_also_marked_with_my_feature(self):
		await some_indy_sdk_call()
```

Python modules can be marked by setting the `pytestmark` variable at the root of the module:

```python

pytestmark = [
	pytest.mark.features('my_feature')
]


@pytest.mark.asyncio
async def test_method_marked_with_my_feature():
	await some_indy_sdk_call()

@pytest.mark.asyncio
async def test_another_method_also_marked_with_my_feature():
	await some_indy_sdk_call()
```

------------------------------------------------------------------------------------------------------------------------

### Test Ordering

In some cases it is useful to explicitly order test execution. This ordering does not represent dependencies in the
tests themselves but rather just an ordering that logically follows; for example, tests for the connection protocol are
configured to execute first as an agent that fails to connect is unlikely to pass later tests.

Tests are ordered based on priority where higher priorities occur first. Priority is set using a `pytest` mark. Setting
priority follows the same rules for tests, classes, and modules as noted above in [Marking Fixtures](#Marking-Fixtures).

Example:

```python
@pytest.mark.asyncio
@pytest.mark.features('my_feature')
@pytest.mark.priority(10)
async def test_method():
	await some_indy_sdk_call()
```

The above test will be executed strictly after all tests with priority greater than 10, in an undefined order (most
likely alphabetical based on test name) for other tests with priority equal to 10, and strictly before tests with
priority less than 10.

------------------------------------------------------------------------------------------------------------------------

### Fixtures

Several `pytest` fixtures are defined in `conftest.py`. You may view that file for details on each of these fixtures. A
summary of each will be given here.

#### Usage

Pytest will automatically inject fixtures into test functions when given as parameters matching the fixture names:

```python
async def test_method(config, wallet_handle, transport):
await some_indy_sdk_call(wallet_handle)
```

The above `test_method` will receive the fixture matching the names `config`, `wallet_handle`, and `transport`.

------------------------------------------------------------------------------------------------------------------------

#### Event Loop

Property| Value
--------|-------------
Fixture | `event_loop`
Scope   | Session
Depends on | None
Dependent Fixtures | `transport`

**Description:** The `event_loop` fixture provides an asynchronous event loop for Python `asyncio` tasks. It is unlikely
that you will need to use this fixture directly in your testing and is mostly used in starting transports.

------------------------------------------------------------------------------------------------------------------------

#### Config

Property| Value
--------|-------------
Fixture | `config`
Scope   | Session
Depends on | None
Dependent Fixtures | `logger`, `wallet_handle`, `transport`

**Description:** The `config` fixture is an object representation of the configuration options in `config.toml`

------------------------------------------------------------------------------------------------------------------------

#### Logger

Property| Value
--------|-------------
Fixture | `logger`
Scope   | Session
Depends on | `config`
Dependent Fixtures | `wallet_handle`, `transport`

**Description:** The `logger` fixture is a python `logging.Logger` to be used for logging during tests. Pytest prints
logs from failing tests after completion.

------------------------------------------------------------------------------------------------------------------------

#### Wallet Handle

Property| Value
--------|-------------
Fixture | `wallet_handle`
Scope   | Session
Depends on | `config`, `logger`
Dependent Fixtures | None

**Description:** The `wallet_handle` fixture provides a session persistent handle to the Indy-SDK wallet. This fixture
automatically closes and deletes (if the `clear_wallets` is configuration option is `true`) the wallet on test session
termination.

------------------------------------------------------------------------------------------------------------------------

#### Transport

Property| Value
--------|-------------
Fixture | `transport`
Scope   | Session
Depends on | `config`, `event_loop`, `logger`
Dependent Fixtures | None

**Description:** The `transport` fixture provides a transport mechanism based on the `transport` configuration option.
At present, only HTTP transport is implemented.

------------------------------------------------------------------------------------------------------------------------

### Helper Functions

Several helper functions are defined in `tests/__init__.py` and are available to all tests.

These methods can be imported into tests using the following, assuming the test module is within the `tests` directory:

```python
from tests import expect_message, check_for_attrs_in_message, pack, unpack
```

------------------------------------------------------------------------------------------------------------------------

#### `expect_message`

**Method Signature:**
```python
async def expect_message(transport: BaseTransport, timeout: int) -> bytes
```

**Description:** `expect_message` takes a `transport` and `timeout` and waits a given number of seconds for a message to
be received over the transport. If no message is received, the test containing the call will fail. If a message is
received, the message bytes are returned to the caller.

------------------------------------------------------------------------------------------------------------------------

#### `check_for_attrs_in_message`

**Method Signature:**
```python
def check_for_attrs_in_message(expected_attrs: [str], msg: Message)
```

**Description:** `check_for_attrs_in_message` checks a `Message` object (essentially a python dictionary) for a given set of keys,
failing if an expected key is missing.

**Example:**
```python
check_for_attrs_in_message(
	[
		'@type',
		'label',
		'key',
		'endpoint'
	],
	invite_msg
)
```

------------------------------------------------------------------------------------------------------------------------

#### `pack`

**Method Signature:**
```python
async def pack(wallet_handle: int, my_vk: str, their_vk: str, msg: Message) -> bytes
```

**Description:** `pack` packs a message using the Indy-SDK `crypto.pack_message` and is wrapped here for convenience.

------------------------------------------------------------------------------------------------------------------------

#### `unpack`

**Method Signature:**
```python
async def unpack(wallet_handle: int, wire_msg_bytes: bytes, **kwargs) -> Message
```

**Description:** `unpack` unpacks a message using the Indy-SDK `crypto.unpack_message`. Optionally, two keyword
arguments can be specified to verify that the expected "from" and "to" verification keys were used to pack the message.
The method will fail if the expected keys are not found.

**Example:**
```python
response = await unpack(wallet_handle, response_bytes, expected_to_vk=my_vk, expected_from_vk=their_vk)
```
