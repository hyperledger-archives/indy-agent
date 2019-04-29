import pytest
import random
from test_suite.tests import expect_message, pack, unpack

from python_agent_utils.messages.basicmessage import BasicMessage

expect_message_timeout = 30


@pytest.mark.asyncio
async def test_basic_message(config, wallet_handle, transport, connection):
    possible_random_messages = ['donut', 'cake', 'milk', 'cookies', 'cupcake', 'pie']
    random_message = possible_random_messages[random.randint(0,5)]
    msg = BasicMessage.build("Reply with: {}".format(random_message))

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
    response_bytes = await expect_message(transport, expect_message_timeout)

    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=connection['my_vk']
    )

    BasicMessage.validate(response)
    print("\nReceived Message:\n", response.pretty_print())

    assert response['content'] == random_message, 'Did not respond with {}!'.format(random_message)
