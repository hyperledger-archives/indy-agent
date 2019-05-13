""" Connection protocol tests.

    Tests are operated manually.
"""
import pytest
from test_suite.tests import expect_message, pack, unpack, sign_field, \
    get_verified_data_from_signed_field, expect_silence, check_problem_report
from indy import did
from python_agent_utils.messages.connection import Connection
from python_agent_utils.messages.did_doc import DIDDoc


# Mark the module
pytestmark = [
    pytest.mark.features('connection.manual', 'core.manual'),
    pytest.mark.priority(10)
]

EXPECT_MESSAGE_TIMEOUT = 30

@pytest.mark.asyncio
async def test_connection_started_by_tested_agent(config, wallet_handle, transport):
    invite_url = input('Input generated connection invite: ')

    invite_msg = Connection.Invite.parse(invite_url)

    print("\nReceived Invite:\n", invite_msg.pretty_print())

    # Create my information for connection
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, '{}')

    # Send Connection Request to inviter
    request = Connection.Request.build(
        'test-connection-started-by-tested-agent',
        my_did,
        my_vk,
        config.endpoint
    )

    print("\nSending Request:\n", request.pretty_print())

    await transport.send(
        invite_msg['serviceEndpoint'],
        await pack(
            wallet_handle,
            my_vk,
            invite_msg['recipientKeys'][0],
            request
        )
    )

    # Wait for response
    print("Awaiting response from tested agent...")
    response_bytes = await expect_message(transport, EXPECT_MESSAGE_TIMEOUT)

    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=my_vk
    )

    Connection.Response.validate_pre_sig(response)
    print("\nReceived Response (pre signature verification):\n", response.pretty_print())

    response['connection'] = await get_verified_data_from_signed_field(response['connection~sig'])

    Connection.Response.validate(response, request.id)
    print("\nReceived Response (post signature verification):\n", response.pretty_print())


async def get_connection_started_by_suite(config, wallet_handle, transport, label=None):
    if label is None:
        label = 'test-suite'

    connection_key = await did.create_key(wallet_handle, '{}')

    invite_str = Connection.Invite.build(label, connection_key, config.endpoint)

    print("\n\nInvitation encoded as URL: ", invite_str)

    print("Awaiting request from tested agent...")
    request_bytes = await expect_message(transport, EXPECT_MESSAGE_TIMEOUT) # A little extra time to copy-pasta

    request = await unpack(
        wallet_handle,
        request_bytes,
        expected_to_vk=connection_key
    )

    Connection.Request.validate(request)
    print("\nReceived request:\n", request.pretty_print())

    (their_did, their_vk, their_endpoint) = Connection.Request.parse(request)

    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, '{}')

    response = Connection.Response.build(request.id, my_did, my_vk, config.endpoint)
    print("\nSending Response (pre signature packing):\n", response.pretty_print())

    response['connection~sig'] = await sign_field(wallet_handle, connection_key, response['connection'])
    del response['connection']
    print("\nSending Response (post signature packing):\n", response.pretty_print())

    await transport.send(
        their_endpoint,
        await pack(
            wallet_handle,
            my_vk,
            their_vk,
            response
        )
    )

    return {
        'my_did': my_did,
        'my_vk': my_vk,
        'their_did': their_did,
        'their_vk': their_vk,
        'their_endpoint': their_endpoint
    }


@pytest.mark.asyncio
async def test_connection_started_by_suite(config, wallet_handle, transport):
    await get_connection_started_by_suite(config, wallet_handle, transport, 'test-connection-started-by-suite')


@pytest.mark.asyncio
async def test_malformed_connection_request_by_testing_agent(config, wallet_handle, transport):
    # Send malformed connection requests

    invite_url = input('Input generated connection invite: ')

    invite_msg = Connection.Invite.parse(invite_url)

    print("\nReceived Invite:\n", invite_msg.pretty_print())

    # Create my information for connection
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, '{}')

    # Send a malformed Connection Request to inviter by removing the DID Doc from request. Expect no response
    request = Connection.Request.build(
        'test-connection-started-by-tested-agent',
        my_did,
        my_vk,
        config.endpoint
    )
    did_doc = request[Connection.CONNECTION].pop(DIDDoc.DID_DOC)
    await transport.send(
        invite_msg['serviceEndpoint'],
        await pack(
            wallet_handle,
            my_vk,
            invite_msg['recipientKeys'][0],
            request
        )
    )
    await expect_silence(transport, EXPECT_MESSAGE_TIMEOUT)
    # TODO: Need some way to ensure tested agent has gracefully handled the error and not crashed.

    # Send a malformed Connection Request to inviter by removing only the DID from request. Expect error in response
    request[Connection.CONNECTION][DIDDoc.DID_DOC] = did_doc
    request[Connection.CONNECTION].pop(DIDDoc.DID)
    await transport.send(
        invite_msg['serviceEndpoint'],
        await pack(
            wallet_handle,
            my_vk,
            invite_msg['recipientKeys'][0],
            request
        )
    )
    response_bytes = await expect_message(transport, EXPECT_MESSAGE_TIMEOUT)
    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=my_vk
    )
    check_problem_report(response, expected_problem_code=Connection.REQUEST_NOT_ACCEPTED)


@pytest.mark.asyncio
async def test_recv_connection_resp_without_sending_req(config, wallet_handle, transport):
    # Tested agent starts the connection. Testing agent receives the invite,
    # does not send connection request but sends a response
    invite_url = input('Input generated connection invite: ')

    invite_msg = Connection.Invite.parse(invite_url)

    print("\nReceived Invite:\n", invite_msg.pretty_print())

    # Create my information for connection
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, '{}')

    response = Connection.Response.build(invite_msg.id, my_did, my_vk, config.endpoint)
    print("\nSending Response (pre signature packing):\n", response.pretty_print())

    response['connection~sig'] = await sign_field(wallet_handle, my_vk, response['connection'])
    del response['connection']
    print("\nSending Response (post signature packing):\n", response.pretty_print())

    await transport.send(
        invite_msg['serviceEndpoint'],
        await pack(
            wallet_handle,
            my_vk,
            invite_msg['recipientKeys'][0],
            response
        )
    )
    response_bytes = await expect_message(transport, EXPECT_MESSAGE_TIMEOUT)
    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=my_vk
    )
    check_problem_report(response, expected_problem_code=Connection.RESPONSE_FOR_UNKNOWN_REQUEST)
