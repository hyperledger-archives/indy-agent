""" Module to handle the connection process.
"""

# pylint: disable=import-error

import json
import base64
import uuid

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

    SEND_INVITE = FAMILY + "send_invite"
    INVITE_SENT = FAMILY + "invite_sent"
    INVITE_RECEIVED = FAMILY + "invite_received"

    REQUEST_RECEIVED = FAMILY + "request_received"
    RESPONSE_RECEIVED = FAMILY + "response_received"

    SEND_REQUEST = FAMILY + "send_request"
    REQUEST_SENT = FAMILY + "request_sent"

    SEND_RESPONSE = FAMILY + "send_response"
    RESPONSE_SENT = FAMILY + "response_sent"

    def __init__(self, agent):
        self.agent = agent

        self.router = SimpleRouter()
        self.router.register(AdminConnection.SEND_INVITE, self.send_invite)
        self.router.register(AdminConnection.SEND_REQUEST, self.send_request)
        self.router.register(AdminConnection.SEND_RESPONSE, self.send_response)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def send_invite(self, msg: Message) -> Message:
        """ UI activated method.
        """

        their_endpoint = msg['endpoint']
        conn_name = msg['name']

        (endpoint_did_str, connection_key) = await did.create_and_store_my_did(self.agent.wallet_handle, "{}")

        meta_json = json.dumps(
            {
                "conn_name": conn_name
            }
        )

        await did.set_did_metadata(self.agent.wallet_handle, endpoint_did_str, meta_json)

        msg = Message({
            '@type': Connection.INVITE,
            'content': {
                'name': conn_name,
                'endpoint': {
                    'url': self.agent.endpoint,
                },
                'connection_key': connection_key
            }
        })
        serialized_msg = Serializer.pack(msg)
        async with aiohttp.ClientSession() as session:
            async with session.post(their_endpoint, data=serialized_msg) as resp:
                print(resp.status)
                print(await resp.text())

        await self.agent.send_admin_message(
            Message({
                '@type': AdminConnection.INVITE_SENT,
                'id': self.agent.ui_token,
                'content': {'name': conn_name}
            })
        )

    async def send_request(self, msg: Message) -> Message:
        """ UI activated method.
        """

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
        conn_name = msg['content']['name']
        their_endpoint = msg['content']['endpoint']
        their_connection_key = msg['content']['connection_key']

        # store invite in the wallet
        await non_secrets.add_wallet_record(self.agent.wallet_handle,
            "invitation", uuid.uuid4().hex,
            json.dumps({
            'name': conn_name,
            'endpoint': their_endpoint,
            'connection_key': their_connection_key
        }), json.dumps({}))

        await self.agent.send_admin_message(
            Message({
                '@type': AdminConnection.INVITE_RECEIVED,
                'content': {
                    'name': conn_name,
                    'endpoint': their_endpoint,
                    'connection_key': their_connection_key,
                    'history': msg
                }
            })
        )


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
