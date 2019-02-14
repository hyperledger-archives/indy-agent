import asyncio
import pytest
import datetime
from message import Message
from tests import expect_message, validate_message, pack, unpack, sign_field, unpack_and_verify_signed_field

from . import BasicMessage

@pytest.mark.asyncio
async def test_basic_message(config, wallet_handle, transport, connection):
    msg = BasicMessage.build("Reply with: donut")

    print("\nSending Message:\n", msg.pretty_print())
    await transport.send(
        connection['their_endpoint'],
        await pack(
            wallet_handle,
            connection['my_vk'],
            connection['their_vk'],
            msg
        )
    )

    print("Awaiting BasicMessage response from tested agent...")
    response_bytes = await expect_message(transport, 60)

    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=connection['my_vk']
    )

    BasicMessage.validate(response)
    print("\nReceived Message:\n", response.pretty_print())

    assert response['content'] == 'donut', 'Did not respond with donut!'
