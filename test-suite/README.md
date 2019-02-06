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
Testing Agent (test-suite) Port | 3000
Tested Agent Port | 3001


> **Note:** Some of these defaults don't make as much sense when considering other transport methods like bluetooth or
> NFC or others. When the need (and implementation) arises for these other transport options, the structure of these
> settings will likely change.


### Step 3: Start the test suite

```sh
python test.py
```

This will execute the tests contained in the folders listed in the `tests` configuration option.

```toml
# A list of tests to be run by the test agent.
tests = [
    "hello_world",
    "core"
]
```

The above `tests` configuration will execute tests contained in the `tests/hello_world` and the `tests/core`
directories.
