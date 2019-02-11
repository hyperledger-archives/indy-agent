import asyncio
import pytest
from message import Message
from tests import expect_message, validate_message, pack, unpack, unpack_and_verify_signed_field
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
            invite_msg['recipient_keys'][0],
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
