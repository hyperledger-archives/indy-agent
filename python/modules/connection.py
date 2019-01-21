""" Module to handle the connection process.
"""

# pylint: disable=import-error

import json
import base64
import uuid
import re

import aiohttp
from indy import crypto, did, pairwise, non_secrets

import serializer.json_serializer as Serializer
from router.simple_router import SimpleRouter
from . import Module
from message import Message
from helpers import serialize_bytes_json, bytes_to_str, str_to_bytes

class AdminConnection(Module):
    FAMILY_NAME = "admin_connections"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    # Message Types in this family
    CONNECTION_LIST = FAMILY + "connection_list"
    CONNECTION_LIST_REQUEST = FAMILY + "connection_list_request"

    GENERATE_INVITE = FAMILY + "generate_invite"
    INVITE_GENERATED = FAMILY + "invite_generated"
    INVITE_RECEIVED = FAMILY + "invite_received"
    RECEIVE_INVITE = FAMILY + "receive_invite"

    SEND_REQUEST = FAMILY + "send_request"
    REQUEST_SENT = FAMILY + "request_sent"
    REQUEST_RECEIVED = FAMILY + "request_received"

    SEND_RESPONSE = FAMILY + "send_response"
    RESPONSE_SENT = FAMILY + "response_sent"
    RESPONSE_RECEIVED = FAMILY + "response_received"

    class BadInviteException(Exception):
        def __init__(self, msg):
            super.__init__(msg)

    def __init__(self, agent):
        self.agent = agent

        self.router = SimpleRouter()
        self.router.register(AdminConnection.GENERATE_INVITE, self.generate_invite)
        self.router.register(AdminConnection.RECEIVE_INVITE, self.receive_invite)
        self.router.register(AdminConnection.SEND_REQUEST, self.send_request)
        self.router.register(AdminConnection.SEND_RESPONSE, self.send_response)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def generate_invite(self, msg: Message) -> Message:
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
        (my_did, my_vk) = await did.create_and_store_my_did(self.agent.wallet_handle, "{}")

        invite_msg = Message({
            '@type': Connection.INVITE,
            'label': self.agent.owner,
            'did': my_did,
            'key': my_vk,
            'endpoint': self.agent.endpoint,
        })

        b64_invite = \
            base64.urlsafe_b64encode(bytes(Serializer.pack(invite_msg), 'utf-8')).decode('ascii')

        await self.agent.send_admin_message(
            Message({
                '@type': AdminConnection.INVITE_GENERATED,
                'invite': '{}?c_i={}'.format(self.agent.endpoint, b64_invite)
            })
        )

    async def receive_invite(self, msg: Message) -> Message:
        """ Receive and save invite.

            This interaction represents an out-of-band communication channel. In the future and in
            practice, these sort of invitations will be received over any number of channels such as
            SMS, Email, QR Code, NFC, etc.

            In this iteration, invite messages are received from the admin interface as a URL
            after being copied and pasted from another agent instance.

            The URL is formatted as follows:

                https://<domain>/<path>?c_i=<invitationstring>

            The invitation string is a base64 url encoded json string.

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

            Currently, only peer DID format is supported.
        """

        # Parse invite string
        matches = re.match("(.+)?c_i=(.+)", msg['invite'])
        if not matches:
            raise BadInviteException("Invite string is improperly formatted")

        invite_msg = Serializer.unpack(
            base64.urlsafe_b64decode(matches.group(2)).decode('utf-8')
        )

        record = uuid.uuid4().hex

        await self.agent.send_admin_message(Message({
            '@type': AdminConnection.INVITE_RECEIVED,
            'label': invite_msg['label'],
            'did': invite_msg['did'],
            'key': invite_msg['key'],
            'endpoint': invite_msg['endpoint']
        }))

        await non_secrets.add_wallet_record(
            self.agent.wallet_handle,
            'invitation',
            invite_msg['did'],
            Serializer.pack(invite_msg),
            '{}'
        )

    async def send_request(self, msg: Message):
        """ Recall invite message from wallet and prepare and send request to the inviter.

            send_request message format:

                {
                  "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/admin_connections/1.0/send_request",
                  "did": <did sent in invite>
                }

            Request format:

                {
                  "@type": "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/request",
                  "label": "Bob",
                  "DID": "B.did@B:A",
                  "DIDDoc": {
                      // did Doc here.
                  }
                }
        """
        invite = Serializer.unpack(
            json.loads(
                await non_secrets.get_wallet_record(
                    self.agent.wallet_handle,
                    'invitation',
                    msg['did'],
                    '{}'
                )
            )['value']
        )

        my_label = self.agent.owner
        label = invite['label']
        their_did = invite['did']
        their_vk = invite['key']
        their_endpoint = invite['endpoint']

        # Store their information from invite
        await did.store_their_did(
            self.agent.wallet_handle,
            json.dumps({
                'did': their_did,
                'verkey': their_vk,
            })
        )
        await did.set_did_metadata(
            self.agent.wallet_handle,
            their_did,
            json.dumps({
                'label': label,
                'endpoint': their_endpoint
            })
        )

        # Create my information for connection
        (my_did, my_vk) = await did.create_and_store_my_did(self.agent.wallet_handle, '{}')

        # Create pairwise relationship between my did and their did
        await pairwise.create_pairwise(
            self.agent.wallet_handle,
            their_did,
            my_did,
            json.dumps({
                'label': label,
                'their_endpoint': their_endpoint,
                'their_vk': their_vk,
                'my_vk': my_vk
            })
        )

        # Send Connection Request to inviter
        request = Message({
            '@type': Connection.REQUEST,
            'label': my_label,
            'DID': my_did,
            'DIDDoc': {
                'key': my_vk,
                'endpoint': self.agent.endpoint,
            }
        })

        await self.agent.send_message_to_agent(their_did, request)

        await self.agent.send_admin_message(
            Message({
                '@type': AdminConnection.REQUEST_SENT,
                'label': label
            })
        )

        return
        # read invitation from wallet if id present. otherwise, use values from args

        their_endpoint = msg['content']['endpoint']
        conn_name = msg['content']['name']
        their_connection_key = msg['content']['key']

        my_endpoint_uri = self.agent.endpoint

        (my_endpoint_did_str, my_connection_key) = await did.create_and_store_my_did(self.agent.wallet_handle, "{}")

        to_did = "needed from admin message"
        msg = Message({
            '@type': Connection.REQUEST,
            "did": my_endpoint_did_str,
            "key": my_connection_key,
            'endpoint': my_endpoint_uri,
        })

        # we call the underlying method here because we don't know their did yet.
        await self.agent.send_message_to_endpoint_and_key(my_connection_key, their_connection_key, their_endpoint, msg)

        meta_json = json.dumps(
            {
                "conn_name": conn_name,
                "their_endpoint": their_endpoint
            }
        )

        await did.set_did_metadata(self.agent.wallet_handle, my_endpoint_did_str, meta_json)

        await self.agent.send_admin_message(
            Message({
                '@type': AdminConnection.REQUEST_SENT,
                'id': self.agent.ui_token,
                'content': {'name': conn_name}
            })
        )

    async def send_response(self, msg: Message) -> Message:
        """ UI activated method.
        """

        their_did_str = msg['content']['endpoint_did']

        pairwise_conn_info_str = await pairwise.get_pairwise(self.agent.wallet_handle, their_did_str)
        pairwise_conn_info_json = json.loads(pairwise_conn_info_str)

        my_did_str = pairwise_conn_info_json['my_did']

        metadata_json = json.loads(pairwise_conn_info_json['metadata'])
        conn_name = metadata_json['conn_name']

        msg = Message({
            '@type': Connection.RESPONSE,
            "did": my_did_str,
        })

        await self.agent.send_message_to_agent(their_did_str, msg)

        await self.agent.send_admin_message(
            Message({
                '@type': AdminConnection.RESPONSE_SENT,
                'id': self.agent.ui_token,
                'content': {'name': conn_name}
            })
        )

class Connection(Module):

    FAMILY_NAME = "connections"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    INVITE = FAMILY + "invite"
    REQUEST = FAMILY + "request"
    RESPONSE = FAMILY + "response"


    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(Connection.INVITE, self.invite_received)
        self.router.register(Connection.REQUEST, self.request_received)
        self.router.register(Connection.RESPONSE, self.response_received)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)


    async def invite_received(self, msg: Message) -> Message:
        """ Received an Invite. In this iteration, invite messages are sent from the admin interface
            after being copy and pasted from another agent instance.

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

            Since receiving an invite is a user triggered action, we go ahead and send a request
            back to the inviter here.
        """


    async def request_received(self, msg: Message) -> Message:
        their_endpoint_uri = msg['endpoint']

        my_did_str = msg.context['to_did']
        their_did_str = msg['did']
        their_key_str = msg.context['from_key']

        my_did_info_str = await did.get_my_did_with_meta(self.agent.wallet_handle, my_did_str)
        my_did_info_json = json.loads(my_did_info_str)
        metadata_str = my_did_info_json['metadata']
        metadata_dict = json.loads(metadata_str)

        conn_name = metadata_dict['conn_name']

        # change verkey passed via send_invite to the agent without encryption
        my_new_verkey = await did.replace_keys_start(self.agent.wallet_handle, my_did_str, '{}')
        await did.replace_keys_apply(self.agent.wallet_handle, my_did_str)

        identity_json = json.dumps(
            {
                "did": their_did_str,
                "verkey": their_key_str
            }
        )

        meta_json = json.dumps(
            {
                "conn_name": conn_name,
                "their_endpoint": their_endpoint_uri,
                "their_verkey": their_key_str,
                "my_verkey": my_new_verkey
            }
        )

        await did.store_their_did(self.agent.wallet_handle, identity_json)
        await pairwise.create_pairwise(self.agent.wallet_handle, their_did_str, my_did_str, meta_json)

        await self.agent.send_admin_message(
            Message({
                '@type': AdminConnection.REQUEST_RECEIVED,
                'content': {
                    'name': conn_name,
                    'endpoint_did': their_did_str,
                    'history': msg
                }
            })
        )


    async def response_received(self, msg: Message) -> Message:
        my_did_str = msg.context['to_did']
        their_did_str = msg['did']
        their_key_str = msg.context['from_key']

        my_did_info_str = await did.get_my_did_with_meta(self.agent.wallet_handle, my_did_str)
        my_did_info_json = json.loads(my_did_info_str)

        my_verkey = my_did_info_json['verkey']
        metadata_str = my_did_info_json['metadata']
        metadata_dict = json.loads(metadata_str)

        conn_name = metadata_dict['conn_name']
        their_endpoint = metadata_dict['their_endpoint']

        identity_json = json.dumps(
            {
                "did": their_did_str,
                "verkey": their_key_str
            }
        )

        meta_json = json.dumps(
            {
                "conn_name": conn_name,
                "their_endpoint": their_endpoint,
                "their_verkey": their_key_str,
                "my_verkey": my_verkey
            }
        )

        await did.store_their_did(self.agent.wallet_handle, identity_json)
        await pairwise.create_pairwise(self.agent.wallet_handle, their_did_str, my_did_str, meta_json)

        #  pairwise connection between agents is established to this point
        await self.agent.send_admin_message(
            Message({
                '@type': AdminConnection.RESPONSE_RECEIVED,
                'id': self.agent.ui_token,
                'content': {
                    'name': conn_name,
                    'their_did': their_did_str,
                    'history': msg
                }
            })
        )
