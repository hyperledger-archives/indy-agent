import pytest

from python_agent_utils.messages.trustping import TrustPing

from test_suite.tests import expect_message, pack, unpack

pytestmark = [
    pytest.mark.features('trustping.manual', 'core.manual')
]

EXPECT_MESSAGE_TIMEOUT = 30

@pytest.mark.asyncio
async def test_trustping_started_by_suite(config, wallet_handle, transport, connection):
    ping = TrustPing.Ping.build()

    print("\nSending trustping:\n", ping.pretty_print())
    await transport.send(
        connection['their_endpoint'],
        await pack(
            wallet_handle,
            connection['my_vk'],
            connection['their_vk'],
            ping
        )
    )

    print("Awaiting TrustPing response from tested agent...")
    response_bytes = await expect_message(transport, EXPECT_MESSAGE_TIMEOUT)

    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=connection['my_vk']
    )

    print("\nReceived TrustPing response:\n", response.pretty_print())
    TrustPing.Pong.validate(response, ping.id)


@pytest.mark.asyncio
async def test_trustping_started_by_tested_agent(config, wallet_handle, transport, connection):
    print("Send a trustping to the test-suite connection using the tested agent.")

    print("Awaiting trustping from tested agent...")
    ping_bytes = await expect_message(transport, EXPECT_MESSAGE_TIMEOUT)

    ping = await unpack(
        wallet_handle,
        ping_bytes,
        expected_to_vk=connection['my_vk']
    )

    print("\nReceived trustping:\n", ping.pretty_print())
    TrustPing.Ping.validate(ping)

    pong = TrustPing.Pong.build(ping.id)
    print("\nSending trustping response:\n", pong.pretty_print())

    await transport.send(
        connection['their_endpoint'],
        await pack(
            wallet_handle,
            connection['my_vk'],
            connection['their_vk'],
            pong
        )
    )

    print("Verify that the tested agent received the trustping response.")
