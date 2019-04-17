import re
from message import Message
from router.simple_router import SimpleRouter

from . import Module

class AdminProtocolDiscovery(Module):
    FAMILY_NAME = "admin-protocol-discovery"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    SEND_QUERY = FAMILY + "send_query"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(AdminProtocolDiscovery.SEND_QUERY, self.send_query)

    async def route(self, msg: Message):
        print("ROUTING ADMIN PROTOCOL DISCOVERY")
        return await self.router.route(msg)

    async def send_query(self, msg: Message):
        print("SENDING QUERY")
        query_msg = Message({
            '@type': ProtocolDiscovery.QUERY,
            'query': msg['query']
        })

        await self.agent.send_message_to_agent(msg['did'], query_msg)


class ProtocolDiscovery(Module):
    FAMILY_NAME = "protocol-discovery"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    QUERY = FAMILY + "query"
    DISCLOSE = FAMILY + "disclose"


    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(ProtocolDiscovery.QUERY, self.query_received)
        self.router.register(ProtocolDiscovery.DISCLOSE, self.disclose_received)

    async def route(self, msg: Message):
        print("ROUTING PROTOCOL DISCOVERY")
        return await self.router.route(msg)

    async def query_received(self, msg: Message):
        print("RECEIVED QUERY")
        matching_modules = []
        def map_query(char):
            if char == '*':
                return '.*'
            return char

        query = ''.join(list(map(map_query, msg['query'])))
        for module in self.agent.modules.keys():
            matches = re.match(query, module)
            if matches:
                matching_modules.append(module)

        disclose_msg = Message({
            '@type': ProtocolDiscovery.DISCLOSE,
            '~thread': {'thid': msg.id},
            'protocols': list(map(lambda mod: {'pid': mod}, matching_modules)),
        })

        await self.agent.send_message_to_agent(msg.context['from_did'], disclose_msg)

    async def disclose_received(self, msg: Message):
        print("RECEIVED DISCLOSE")
        print(msg.as_json())

