import aiohttp_jinja2
import jinja2
import json
from indy import did, wallet

from router.simple_router import SimpleRouter
from agent import Agent, WalletConnectionException
from message import Message
from . import Module

class AdminWalletConnection(Module):
    FAMILY_NAME = "admin_walletconnection"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    CONNECT = FAMILY + "connect"
    DISCONNECT = FAMILY + "disconnect"
    USER_ERROR = FAMILY + "user_error"


    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(AdminWalletConnection.CONNECT, self.connect)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def connect(self, msg):
        """ Connect to existing wallet.
        """

        try:
            await self.agent.connect_wallet(msg['name'], msg['passphrase'])
        except WalletConnectionException:
            return Message({
                '@type': AdminWalletConnection.USER_ERROR,
                'error_code': "invalid_passphrase",
                'message': "Invalid Passphrase",
                'thread': {
                    'thid': msg.id
                }
            })

        # prompt a STATE message.
        return await self.agent.modules['admin'].state_request(None)
