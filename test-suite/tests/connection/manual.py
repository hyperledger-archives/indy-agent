import asyncio
import pytest
from message import Message
from tests import expect_message, validate_message, pack, unpack, sign_field, unpack_and_verify_signed_field
from indy import did
from . import Connection

@pytest.mark.asyncio
async def test_connection_started_by_tested_agent(config, wallet_handle, transport):
    invite_url = input('Input generated connection invite: ')

    invite_msg = Connection.Invite.parse(invite_url)

    # Create my information for connection
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, '{}')

    # Send Connection Request to inviter
    request = Connection.Request.build(
        'testing-agent',
        my_did,
        my_vk,
        config.endpoint
    )

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
    response_bytes = await expect_message(transport, 60)

    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=my_vk
    )

    Connection.Response.validate_pre_sig(response)

    response['connection'] = await unpack_and_verify_signed_field(response['connection~sig'])

    Connection.Response.validate(response)

async def get_connection_started_by_suite(config, wallet_handle, transport):
    connection_key = await did.create_key(wallet_handle, '{}')

    invite_str = Connection.Invite.build(connection_key, config.endpoint)

    print("\n\nInvitation encoded as URL: ", invite_str)

    request_bytes = await expect_message(transport, 90) # A little extra time to copy-pasta

    request = await unpack(
        wallet_handle,
        request_bytes,
        expected_to_vk=connection_key
    )

    Connection.Request.validate(request)

    (their_did, their_vk, their_endpoint) = Connection.Request.parse(request)

    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, '{}')

    response = Connection.Response.build(my_did, my_vk, config.endpoint)

    response['connection~sig'] = await sign_field(wallet_handle, connection_key, response['connection'])
    del response['connection']

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
    await get_connection_started_by_suite(config, wallet_handle, transport)
