import aiohttp_jinja2
import jinja2
import json
from indy import did, wallet

from router.simple_router import SimpleRouter
from agent import Agent
from message import Message
from message_types import ADMIN_WALLETCONNECTION
from . import Module

class AdminWalletConnection(Module):

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(ADMIN_WALLETCONNECTION.CONNECT, self.connect)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def connect(self, msg):
        """ Connect to existing wallet.
        """

        await self.agent.connect_wallet(msg.name, msg.passphrase)
        return await self.agent.modules['ui'].ui_connect(None)
