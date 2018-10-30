import aiohttp_jinja2
import jinja2
import json
from indy import did, wallet

from router.simple_router import SimpleRouter
from model import Message, Agent
from message_types import UI
from . import Module

class Ui(Module):

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(UI.STATE_REQUEST, self.ui_connect)
        self.router.register(UI.INITIALIZE, self.initialize_agent)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def ui_connect(self, _) -> Message:

        return Message(
            type=UI.STATE,
            content={
                'initialized': self.agent.initialized,
                'agent_name': self.agent.owner
            }
        )


    async def initialize_agent(self, msg):
        """ Initialize agent.
        """
        data = msg.content
        self.agent.owner = data['name']
        passphrase = data['passphrase']

        #set wallet name from msg contents
        wallet_name = '%s-wallet' % self.agent.owner

        wallet_config = json.dumps({"id": wallet_name})
        wallet_credentials = json.dumps({"key": passphrase})

        # pylint: disable=bare-except
        # TODO: better handle potential exceptions.
        try:
            await wallet.create_wallet(wallet_config, wallet_credentials)
        except Exception as e:
            print(e)

        try:
            self.agent.wallet_handle = await wallet.open_wallet(wallet_config,
                                                           wallet_credentials)
        except Exception as e:
            print(e)
            print("Could not open wallet!")

        (_, self.agent.endpoint_vk) = await did.create_and_store_my_did(
            self.agent.wallet_handle, "{}")

        self.agent.initialized = True
        return await self.ui_connect(None)

@aiohttp_jinja2.template('index.html')
async def root(request):
    agent = request.app['agent']
    agent.offer_endpoint = request.url.scheme + '://' + request.url.host
    agent.endpoint = request.url.scheme + '://' + request.url.host
    if request.url.port is not None:
        agent.endpoint += ':' + str(request.url.port) + '/indy'
        agent.offer_endpoint += ':' + str(request.url.port) + '/offer'
    else:
        agent.endpoint += '/indy'
        agent.offer_endpoint += '/offer'
    return {'ui_token': agent.ui_token}
