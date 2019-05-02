import pytest
from test_suite.tests import expect_message, pack, unpack, sign_field, get_verified_data_from_signed_field, \
    expect_silence, check_problem_report
from indy import did
from python_agent_utils.messages.connection import Connection
from python_agent_utils.messages.did_doc import DIDDoc


@pytest.mark.asyncio
async def connection_done(config, wallet_handle, transport, ref_agent):
    pass
