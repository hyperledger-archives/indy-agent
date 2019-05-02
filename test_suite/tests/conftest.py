import pytest

from indy import did

from modules.connection import Connection
from modules.basicmessage import BasicMessage
from modules.trustping import TrustPing
from agent import Agent


@pytest.mark.asyncio
async def ref_agent(event_loop):
    agent = Agent()
    agent.register_module(Connection)
    agent.register_module(BasicMessage)
    agent.register_module(TrustPing)

    agent.wallet_handle = await agent.connect_wallet('test123', 'test123', ephemeral=True)

    (_, agent.endpoint_vk) = await did.create_and_store_my_did(agent.wallet_handle, "{}")

    agent.initialized = True


async def add_send_wire_msg_to_running_agent(agent, wire_msg):
    await agent.message_queue.put(wire_msg)


async def process_1_agent_message(agent):
    if not agent.message_queue.empty():
        await agent.handle_incoming()
