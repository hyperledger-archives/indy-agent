""" Test Suite fixture definitions.

    These fixtures define the core functionality of the testing agent.

    For more information on how pytest fixtures work, see
    https://docs.pytest.org/en/latest/fixture.html#fixture
"""

import asyncio
import json
import os
import logging
import importlib.util
from inspect import getmembers, isfunction

import pytest
from indy import crypto, wallet
from config import Config
from transport.http_transport import HTTPTransport

@pytest.fixture(scope='session')
def logger():
    """ Test logger
    """
    return logging.getLogger()

@pytest.fixture(scope='session')
def event_loop():
    """ Create a session scoped event loop.

        pytest.asyncio plugin provides a default function scoped event loop
        which cannot be used as a dependency to session scoped fixtures.
    """
    return asyncio.get_event_loop()

@pytest.fixture(scope='session')
async def config(logger):
    """ Gather configuration and initialize the wallet.
    """
    DEFAULT_CONFIG_PATH = 'test_config.toml'
    logger.debug('Loading configuration from file: {}'.format(DEFAULT_CONFIG_PATH))

    config = Config.from_file(DEFAULT_CONFIG_PATH)
    parser = Config.get_arg_parser()

    args = parser.parse_args()
    if args:
        config.update(vars(args))

    yield config

    # TODO: Cleanup?


@pytest.fixture(scope='session')
async def wallet_handle(config, logger):
    # Initialization steps
    # -- Create wallet
    logger.debug('Creating wallet: {}'.format(config.wallet_name))
    try:
        await wallet.create_wallet(
            json.dumps({
                'id': config.wallet_name,
                'storage_config': {
                    'path': config.wallet_path
                }
            }),
            json.dumps({'key': 'test-agent'})
        )
    except:
        pass

    # -- Open a wallet
    logger.debug('Opening wallet: {}'.format(config.wallet_name))
    wallet_handle = await wallet.open_wallet(
        json.dumps({
            'id': config.wallet_name,
            'storage_config': {
                'path': config.wallet_path
            }
        }),
        json.dumps({'key': 'test-agent'})
    )

    yield wallet_handle

    # Cleanup
    if config.clear_wallets:
        logger.debug("Closing wallet")
        await wallet.close_wallet(wallet_handle)
        logger.debug("deleting wallet")
        await wallet.delete_wallet(
            json.dumps({
                'id': config.wallet_name,
                'storage_config': {
                    'path': config.wallet_path
                }
            }),
            json.dumps({'key': 'test-agent'})
        )

        logger.debug("removing wallet directory")
        os.rmdir(config.wallet_path)


@pytest.fixture(scope='session')
async def transport(config, wallet_handle, event_loop, logger):
    """ Transport fixture.

        Initializes the transport layer.
    """
    MSG_Q = asyncio.Queue()
    transport = HTTPTransport(config, MSG_Q)

    logger.debug("Starting transport")
    event_loop.create_task(transport.start_server())
    return transport


### Test configuration loading ###

def pytest_collection(session):
    if os.path.isfile('tests.toml'):
        yield TomlTestDefinitionFile('tests.toml', session=session)
try:
    items = self._perform_collect(args, genitems)
            self.config.pluginmanager.check_pending()
            hook.pytest_collection_modifyitems(
                    session=self, config=self.config, items=items
                    )
finally:
    hook.pytest_collection_finish(session=self)
        self.testscollected = len(items)
return items


class TomlTestDefinitionFile(pytest.File):
    def collect(self):
        import toml # we need a toml parser

        DEFAULT_CONFIG_PATH = "test_config.toml"
        conf = toml.load(DEFAULT_CONFIG_PATH)
        tests = toml.load(self.fspath.open())
        for test in tests['groups']:
            if test['name'] in conf['tests']:
                yield TestGroup(self, test['name'], test['path'])


class TestGroup(pytest.Module):
    def __init__(self, parent, name, path):
        super(TestGroup, self).__init__(path, parent=parent)
        self.name = name

    def repr_failure(self, excinfo):
        """ called when self.runtest() raises an exception. """
        print(excinfo)
        return "\n".join(
            [
                "Agent failed to pass tests for feature"
            ]
        )

    def reportinfo(self):
        return self.fspath, 0, "Feature: %s" % self.name
