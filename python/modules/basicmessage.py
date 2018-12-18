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
from message_types import BASICMESSAGE, ADMIN_BASICMESSAGE, CONN, FORWARD
from . import Module

class AdminBasicMessage(Module):
    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(ADMIN_BASICMESSAGE.SEND_MESSAGE, self.send_message)
        self.router.register(ADMIN_BASICMESSAGE.GET_MESSAGES, self.get_messages)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def send_message(self, msg: Message) -> Message:
        """ UI activated method.
        """

        their_did_str = msg['to']
        message_to_send = msg['message']

        pairwise_conn_info_str = await pairwise.get_pairwise(self.agent.wallet_handle, their_did_str)
        pairwise_conn_info_json = json.loads(pairwise_conn_info_str)

        my_did_str = pairwise_conn_info_json['my_did']
        time_sent = time.time()

        data_to_send = json.dumps(
            {
                "timestamp": time_sent,
                "content": message_to_send
            }
        )

        # store message in the wallet
        await non_secrets.add_wallet_record(
            self.agent.wallet_handle,
            "basicmessage",
            uuid.uuid4().hex,
            json.dumps({
                'from': my_did_str,
                'timestamp': time_sent,
                'content': message_to_send
            }),
            json.dumps({
                "their_did": their_did_str
            })
        )

        data_to_send_bytes = str_to_bytes(data_to_send)

        metadata_json = json.loads(pairwise_conn_info_json['metadata'])
        conn_name = metadata_json['conn_name']
        their_endpoint = metadata_json['their_endpoint']
        their_verkey_str = metadata_json['their_verkey']

        my_did_info_str = await did.get_my_did_with_meta(self.agent.wallet_handle,
                                                         my_did_str)
        my_did_info_json = json.loads(my_did_info_str)
        my_verkey_str = my_did_info_json['verkey']

        inner_msg = Message({
            '@type': BASICMESSAGE.MESSAGE,
            'from': my_did_str,
            'message': serialize_bytes_json(
                await crypto.auth_crypt(self.agent.wallet_handle, my_verkey_str,
                                        their_verkey_str, data_to_send_bytes))
        })

        outer_msg = Message({
            '@type': FORWARD.FORWARD,
            'to': "ABC",
            'content': inner_msg
        })

        serialized_outer_msg = Serializer.pack(outer_msg)

        serialized_outer_msg_bytes = str_to_bytes(serialized_outer_msg)

        all_message = Message({
            'content': serialize_bytes_json(await crypto.anon_crypt(their_verkey_str,
                                                                 serialized_outer_msg_bytes))
        })

        serialized_msg = Serializer.pack(all_message)

        async with aiohttp.ClientSession() as session:
            async with session.post(their_endpoint, data=serialized_msg) as resp:
                print(resp.status)
                print(await resp.text())

        return Message({
            '@type': ADMIN_BASICMESSAGE.MESSAGE_SENT,
            'id': self.agent.ui_token,
            'with': their_did_str,
            'message': {
                'from': my_did_str,
                'timestamp': time_sent,
                'content': message_to_send
            }
        })

    async def get_messages(self, msg: Message) -> Message:
        their_did = msg['with']
        search_handle = await non_secrets.open_wallet_search(
            self.agent.wallet_handle, "basicmessage",
            json.dumps({"their_did": their_did}),
            json.dumps({})
        )
        results = await non_secrets.fetch_wallet_search_next_records(self.agent.wallet_handle, search_handle, 100)

        messages = []
        for r in json.loads(results)["records"] or []: # records is None if empty
            d = json.loads(r['value'])
            d["_id"] = r["id"] # include record id for further reference.
            messages.append(d)
        #TODO: fetch in loop till all records are processed
        await non_secrets.close_wallet_search(search_handle)
        messages = sorted(messages, key=lambda n: n['timestamp'], reverse=True)

        return Message({
            '@type': ADMIN_BASICMESSAGE.MESSAGES,
            'with': their_did,
            'messages': messages
        })


class BasicMessage(Module):

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(BASICMESSAGE.MESSAGE, self.receive_message)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def receive_message(self, msg: Message) -> Message:
        their_did_str = msg['from']

        pairwise_conn_info_str = await pairwise.get_pairwise(self.agent.wallet_handle, their_did_str)
        pairwise_conn_info_json = json.loads(pairwise_conn_info_str)

        my_did_str = pairwise_conn_info_json['my_did']
        metadata = json.loads(pairwise_conn_info_json['metadata'])

        my_did_info_str = await did.get_my_did_with_meta(self.agent.wallet_handle, my_did_str)

        my_did_info_json = json.loads(my_did_info_str)
        my_verkey = my_did_info_json['verkey']

        message_bytes = str_to_bytes(msg['message'])
        message_bytes = base64.b64decode(message_bytes)

        their_key_str, their_data_bytes = await crypto.auth_decrypt(
            self.agent.wallet_handle, my_verkey, message_bytes)

        their_data_json = json.loads(bytes_to_str(their_data_bytes))

        # store message in the wallet
        await non_secrets.add_wallet_record(
            self.agent.wallet_handle,
            "basicmessage",
            uuid.uuid4().hex,
            json.dumps({
                'from': their_did_str,
                'timestamp': their_data_json['timestamp'],
                'content': their_data_json['content']
            }),
            json.dumps({
                "their_did": their_did_str
            })
        )

        return Message({
            '@type': ADMIN_BASICMESSAGE.MESSAGE_RECEIVED,
            'id': self.agent.ui_token,
            'with': their_did_str,
            'message': {
                'from': their_did_str,
                'timestamp': their_data_json['timestamp'],
                'content': their_data_json['content']
            }
        })
