from router.simple_router import SimpleRouter
from python_agent_utils.messages.message import Message
from . import Module


class AdminTrustPing(Module):
    FAMILY_NAME = "admin_trustping"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION

    SEND_TRUSTPING = FAMILY + "/send_trustping"
    TRUSTPING_SENT = FAMILY + "/trustping_sent"
    TRUSTPING_RECEIVED = FAMILY + "/trustping_received"
    TRUSTPING_RESPONSE_RECEIVED = FAMILY + "/trustping_response_received"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(AdminTrustPing.SEND_TRUSTPING, self.send_trustping)

    async def route(self, msg: Message) -> None:
        return await self.router.route(msg)

    async def trustping_response(self, msg: Message) -> None:
        print("trustping_response")
        print(msg)

    async def send_trustping(self, msg: Message) -> None:
        """ UI activated method.
        """

        their_did_str = msg['to']

        message = Message({
            '@type': TrustPing.PING
        })

        await self.agent.send_message_to_agent(their_did_str, message)

        await self.agent.send_admin_message(
            Message({
                '@type': AdminTrustPing.TRUSTPING_SENT,
                'to': their_did_str,
            })
        )


class TrustPing(Module):
    FAMILY_NAME = "trust_ping"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION

    PING = FAMILY + "/ping"
    PING_RESPONSE = FAMILY + "/ping_response"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(TrustPing.PING, self.ping)
        self.router.register(TrustPing.PING_RESPONSE, self.ping_response)

    async def route(self, msg: Message) -> None:
        return await self.router.route(msg)

    async def ping(self, msg: Message) -> None:
        r = await self.validate_common_message_blocks(msg, TrustPing.FAMILY)
        if not r:
            return

        await self.agent.send_admin_message(
            Message({
                '@type': AdminTrustPing.TRUSTPING_RECEIVED,
                'from': msg.context['from_did'],
            })
        )

        await self.agent.send_message_to_agent(
            msg.context['from_did'],
            Message({
                '@type': TrustPing.PING_RESPONSE,
                '~thread': {Message.THREAD_ID: msg.id, Message.SENDER_ORDER: 0}
            })
        )

    async def ping_response(self, msg: Message) -> None:
        await self.agent.send_admin_message(
            Message({
                '@type': AdminTrustPing.TRUSTPING_RESPONSE_RECEIVED,
                'from': msg.context['from_did'],
            })
        )
