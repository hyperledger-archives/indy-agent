""" Test Suite fixture definitions.

    These fixtures define the core functionality of the testing agent.

    For more information on how pytest fixtures work, see
    https://docs.pytest.org/en/latest/fixture.html#fixture
"""

import asyncio
import json
import os
import logging

import pytest
from indy import wallet
from test_suite.transport.http_transport import HTTPTransport

@pytest.fixture(scope='session')
def event_loop():
    """ Create a session scoped event loop.

        pytest.asyncio plugin provides a default function scoped event loop
        which cannot be used as a dependency to session scoped fixtures.
    """
    return asyncio.get_event_loop()


@pytest.fixture(scope='session')
def config(pytestconfig):
    """ Get suite configuration.
    """
    yield pytestconfig.suite_config

    # TODO: Cleanup?


@pytest.fixture(scope='session')
def logger(config):
    """ Test logger
    """
    logger = logging.getLogger()
    logger.setLevel(config.log_level)
    return logging.getLogger()


@pytest.fixture(scope='session')
async def wallet_handle(config, logger):
    wallet_config = (
        json.dumps({
            'id': config.wallet_name,
            'storage_config': {
                'path': config.wallet_path
            }
        }),
        json.dumps({'key': 'test-agent'})
    )
    # Initialization steps
    # -- Create wallet
    logger.debug('Creating wallet: {}'.format(config.wallet_name))
    try:
        await wallet.create_wallet(*wallet_config)
    except:
        pass

    # -- Open a wallet
    logger.debug('Opening wallet: {}'.format(config.wallet_name))
    wallet_handle = await wallet.open_wallet(*wallet_config)

    yield wallet_handle

    # Cleanup
    if config.clear_wallets:
        logger.debug("Closing wallet")
        await wallet.close_wallet(wallet_handle)
        logger.debug("deleting wallet")
        await wallet.delete_wallet(*wallet_config)

        logger.debug("removing wallet directory")
        os.rmdir(config.wallet_path)


@pytest.fixture(scope='session')
async def transport(config, event_loop, logger):
    """ Transport fixture.

        Initializes the transport layer.
    """
    MSG_Q = asyncio.Queue()
    if config.transport == "http":
        transport = HTTPTransport(config, logger, MSG_Q)
    else:
        #transport = None
        raise RuntimeError("{} not supported. Support only HTTP transport for now", config.transport)

    logger.debug("Starting transport")
    event_loop.create_task(transport.start_server())
    return transport


@pytest.fixture(scope='session')
async def connection(config, wallet_handle, transport):
    from test_suite.tests.connection.manual import get_connection_started_by_suite

    yield await get_connection_started_by_suite(config, wallet_handle, transport)
