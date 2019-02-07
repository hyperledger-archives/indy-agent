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
def event_loop():
    """ Create a session scoped event loop.

        pytest.asyncio plugin provides a default function scoped event loop
        which cannot be used as a dependency to session scoped fixtures.
    """
    return asyncio.get_event_loop()

@pytest.fixture(scope='session')
async def config():
    """ Gather configuration and initialize the wallet.
    """
    DEFAULT_CONFIG_PATH = 'config.toml'
    print('Loading test configuration from file: {}'.format(DEFAULT_CONFIG_PATH))

    config = Config.from_file(DEFAULT_CONFIG_PATH)
    parser = Config.get_arg_parser()

    args = parser.parse_args()
    if args:
        config.update(vars(args))

    yield config

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
async def transport(config, event_loop, logger):
    """ Transport fixture.

        Initializes the transport layer.
    """
    MSG_Q = asyncio.Queue()
    if config.transport == "http":
        transport = HTTPTransport(config, logger, MSG_Q)
    else:
        transport = None

    logger.debug("Starting transport")
    event_loop.create_task(transport.start_server())
    return transport


### Test configuration loading ###

def pytest_ignore_collect(path, config):
    if path.ext != ".toml":
        return True

def pytest_runtest_makereport(item, call):
    from _pytest.runner import TestReport, ExceptionInfo, skip
    when = call.when
    duration = call.stop - call.start
    keywords = {x: 1 for x in item.keywords}
    excinfo = call.excinfo
    sections = []
    if not call.excinfo:
        outcome = "passed"
        longrepr = None
    else:
        if not isinstance(excinfo, ExceptionInfo):
            outcome = "failed"
            longrepr = excinfo
        elif excinfo.errisinstance(skip.Exception):
            outcome = "skipped"
            r = excinfo._getreprcrash()
            longrepr = (str(r.path), r.lineno, r.message)
        else:
            outcome = "failed"
            if call.when == "call":
                longrepr = item.repr_failure(excinfo)
            else:  # exception in setup or teardown
                longrepr = item._repr_failure_py(
                    excinfo, style=item.config.option.tbstyle
                )
    for rwhen, key, content in item._report_sections:
        sections.append(("%s %s" % (key, rwhen), content))
    return TestReport(
        item.nodeid,
        item.location,
        keywords,
        outcome,
        longrepr,
        when,
        sections,
        duration,
        user_properties=item.user_properties,
)

def pytest_collect_file(path, parent):
    if path.ext == ".toml" and path.basename.startswith("tests"):
        return TomlTestDefinitionFile(path, parent)

class TomlTestDefinitionFile(pytest.File):
    def collect(self):
        import toml # we need a toml parser

        DEFAULT_CONFIG_PATH = "config.toml"
        conf = toml.load(DEFAULT_CONFIG_PATH)
        tests = toml.load(self.fspath.open())
        for test in tests['feature']:
            if test['name'] in conf['tests']:
                yield Feature(self, test['name'], test['paths'], test['description'])


class Feature(pytest.Collector):
    def __init__(self, parent, name, paths, description):
        super(Feature, self).__init__(name, parent=parent)
        self.parent = parent
        self.name = name
        self.paths = paths
        self.description = description
        self.test_failed = False
        self.items = []

    def collect(self):
        for path in self.paths:
            self.items.append(FeaturePart(self, self.name, path))
        yield from self.items

    def last_part(self):
        if not self.items:
            return None
        return self.items[-1]


class FeaturePart(pytest.Module):
    def __init__(self, parent, name, path):
        super(FeaturePart, self).__init__(path, parent=parent)
        self.name = '{}.{}'.format(name, path)
        self._nodeid = name
        self.items = []

    def collect(self):
        self.items = super(FeaturePart, self).collect()
        for item in self.items:
            if isinstance(item, pytest.Function):
                yield FeatureTestFunction(self.name, item)
            else:
                yield item

    def last_child(self):
        if self.parent.last_part() != self:
            return None
        if not self.items:
            return None

        return self.items[-1]

    @property
    def description(self):
        return self.parent.description

    @property
    def test_failed(self):
        return self.parent.test_failed

    @test_failed.setter
    def test_failed(self, val):
        self.parent.test_failed = val

class FeatureTestFunction(pytest.Function):
    def __init__(self, feature, func):
        self.feature = feature
        self.func = func

    def __getattribute__(self, name):
        try:
            attr = object.__getattribute__(self, name)
        except AttributeError:
            attr = self.func.__getattribute__(name)

        return attr

    def repr_failure(self, excinfo):
        """ called when self.runtest() raises an exception. """
        if not self.parent.test_failed:
            self.parent.test_failed = True

        if self.parent.test_failed and self.parent.last_child() == self.func:
            self.add_report_section(self.feature, "Feature Description:", self.parent.description)

        return self._repr_failure_py(excinfo, style="long")

    def reportinfo(self):
        return self.fspath, 0, "Feature: %s, Test: %s" % (self.feature, self.name)
