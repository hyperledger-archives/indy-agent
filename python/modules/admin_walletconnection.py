""" Module allowing a user to create and connect to an Indy wallet (or open an existing one).
"""
# pylint: disable=import-error
from agent import WalletConnectionException
from modules import Module
from modules.admin import Admin
from python_agent_utils.messages.message import Message
from router.simple_router import SimpleRouter


class AdminWalletConnection(Module):
    """ Class handling messages received from the UI.
    """
    FAMILY_NAME = "admin_walletconnection"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION

    CONNECT = FAMILY + "/connect"
    DISCONNECT = FAMILY + "/disconnect"
    USER_ERROR = FAMILY + "/user_error"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(AdminWalletConnection.CONNECT, self.connect)
        self.router.register(AdminWalletConnection.DISCONNECT, self.disconnect)

    async def route(self, msg: Message) -> Message:
        """ Route a message to its registered callback
        """
        return await self.router.route(msg)

    async def connect(self, msg: Message) -> Message:
        """ Connect to an existing wallet.
        """
        try:
            await self.agent.connect_wallet(msg['name'], msg['passphrase'])
        except WalletConnectionException:
            await self.agent.send_admin_message(Message({
                '@type': AdminWalletConnection.USER_ERROR,
                'error_code': 'invalid_passphrase',
                'message': 'Invalid Passphrase',
                'thread': {'thid': msg['id']}
            }))

        # Prompt a STATE message.
        return await self.agent.modules[Admin.FAMILY].state_request(None)

    async def disconnect(self, _) -> Message:
        """ Disconnect from an existing wallet.
        """
        await self.agent.disconnect_wallet()

        # Prompt a STATE message.
        return await self.agent.modules[Admin.FAMILY].state_request(None)
