import aiohttp
import aiohttp_jinja2
import jinja2
import base64
import json
import time
import uuid
from indy import did, wallet, pairwise, crypto, non_secrets

from helpers import str_to_bytes, serialize_bytes_json, bytes_to_str
from router.simple_router import SimpleRouter
import serializer.json_serializer as Serializer
from agent import Agent, WalletConnectionException
from message import Message
from . import Module

class AdminTrustPing(Module):
    FAMILY_NAME = "admin_trustping"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    SEND_TRUSTPING = FAMILY + "send_trustping"
    TRUSTPING_SENT = FAMILY + "trustping_sent"
    TRUSTPING_RECEIVED = FAMILY + "trustping_received"
    TRUSTPING_RESPONSE_RECEIVED = FAMILY + "trustping_response_received"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(AdminTrustPing.SEND_TRUSTPING, self.send_trustping)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def trustping_response(self, msg: Message) -> Message:
        print("trustping_response")
        print(msg)

    async def send_trustping(self, msg: Message) -> Message:
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
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    PING = FAMILY + "ping"
    PING_RESPONSE = FAMILY + "ping_response"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(TrustPing.PING, self.ping)
        self.router.register(TrustPing.PING_RESPONSE, self.ping_response)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def ping(self, msg: Message) -> Message:
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
                '~thread': {'thid': msg.id}
            })
        )

    async def ping_response(self, msg: Message) -> Message:
        await self.agent.send_admin_message(
            Message({
                '@type': AdminTrustPing.TRUSTPING_RESPONSE_RECEIVED,
                'from': msg.context['from_did'],
            })
        )
