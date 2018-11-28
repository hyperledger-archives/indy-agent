import aiohttp_jinja2
import jinja2
import json
from indy import did, wallet

from router.simple_router import SimpleRouter
from agent import Agent
from message import Message
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
        if self.agent.initialized is True:
            return
        data = msg.content
        agent_name = data['name']
        passphrase = data['passphrase']
        await self.agent.connect_wallet(data['name'], data['passphrase'])

        return await self.ui_connect(None)

@aiohttp_jinja2.template('index.html')
async def root(request):
    print(request)
    agent = request.app['agent']
    agent.offer_endpoint = request.url.scheme + '://' + request.url.host
    print(agent.offer_endpoint)
    agent.endpoint = request.url.scheme + '://' + request.url.host
    if request.url.port is not None:
        agent.endpoint += ':' + str(request.url.port) + '/indy'
        agent.offer_endpoint += ':' + str(request.url.port) + '/offer'
    else:
        agent.endpoint += '/indy'
        agent.offer_endpoint += '/offer'
    return {'ui_token': agent.ui_token}
