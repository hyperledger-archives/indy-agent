""" Module to handle the connection process.
"""

# pylint: disable=import-error

import json
import base64
import re
import datetime
from typing import Optional

from indy import did, pairwise, non_secrets, error

import indy_sdk_utils as utils
import serializer.json_serializer as Serializer
from python_agent_utils.messages.did_doc import DIDDoc
from python_agent_utils.messages.connection import Connection as ConnectionMessage
from router.simple_router import SimpleRouter
from . import Module
from python_agent_utils.messages.message import Message

class AdminStaticConnection(Module):
    FAMILY_NAME = "admin_staticconnections"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION

    # Message Types in this family
    CREATE_STATIC_CONNECTION = FAMILY + "/create_static_connection"
    STATIC_CONNECTION_CREATED = FAMILY + "/static_connection_created"


    def __init__(self, agent):
        self.agent = agent

        self.router = SimpleRouter()
        self.router.register(AdminStaticConnection.CREATE_STATIC_CONNECTION, self.create_static_connection)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def create_static_connection(self, msg: Message) -> Message:
        """ Generate new connection invitation.

            This interaction represents an out-of-band communication channel. In the future and in
            practice, these sort of invitations will be received over any number of channels such as
            SMS, Email, QR Code, NFC, etc.

            Structure of an invite message:

                {
                    "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation",
                    "label": "Alice",
                    "did": "did:sov:QmWbsNYhMrjHiqZDTUTEJs"
                }

            Or, in the case of a peer DID:

                {
                    "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/invitation",
                    "label": "Alice",
                    "did": "did:peer:oiSqsNYhMrjHiqZDTUthsw",
                    "key": "8HH5gYEeNc3z7PYXmd54d4x6qAfCNrqQqEB3nS7Zfu7K",
                    "endpoint": "https://example.com/endpoint"
                }

            Currently, only peer DID is supported.
        """
        their_did = msg['did']
        their_vk = msg['vk']
        their_endpoint = msg['endpoint']
        label = msg['label']


        # Store their information from request
        await utils.store_their_did(self.agent.wallet_handle, their_did, their_vk)

        await did.set_did_metadata(
            self.agent.wallet_handle,
            their_did,
            json.dumps({
                'label': label,
                'endpoint': their_endpoint,

            })
        )

        # Create my information for connection
        (my_did, my_vk) = await utils.create_and_store_my_did(self.agent.wallet_handle)

        # Create pairwise relationship between my did and their did
        await pairwise.create_pairwise(
            self.agent.wallet_handle,
            their_did,
            my_did,
            json.dumps({
                'label': label,
                'their_endpoint': their_endpoint,
                'their_vk': their_vk,
                'my_vk': my_vk,
                'static': True
            })
        )

        await self.agent.send_admin_message(
            Message({
                '@type': AdminStaticConnection.STATIC_CONNECTION_CREATED,
                'label': label,
                'my_did': my_did,
                'my_vk': my_vk,
                'my_endpoint': self.agent.endpoint
            })
        )

