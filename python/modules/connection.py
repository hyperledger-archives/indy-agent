""" Module to handle the connection process.
"""

# pylint: disable=import-error

import json
import base64
import aiohttp
from indy import crypto, did, pairwise

import serializer.json_serializer as Serializer
from model import Message
from message_types import UI, CONN, FORWARD
from helpers import serialize_bytes_json, bytes_to_str, str_to_bytes


async def send_invite(msg: Message, my_agent) -> Message:
    their_endpoint = msg.content['endpoint']
    conn_name = msg.content['name']

    (endpoint_did_str, connection_key) = await did.create_and_store_my_did(my_agent.wallet_handle, "{}")

    meta_json = json.dumps(
        {
            "conn_name": conn_name
        }
    )

    await did.set_did_metadata(my_agent.wallet_handle, endpoint_did_str, meta_json)

    msg = Message(
        type=CONN.SEND_INVITE,
        content={
            'name': conn_name,
            'endpoint': {
                'url': my_agent.endpoint,
            },
            'connection_key': connection_key
        }
    )
    serialized_msg = Serializer.pack(msg)
    async with aiohttp.ClientSession() as session:
        async with session.post(their_endpoint, data=serialized_msg) as resp:
            print(resp.status)
            print(await resp.text())

    return Message(
        type=UI.INVITE_SENT,
        id=my_agent.ui_token,
        content={'name': conn_name})


async def invite_received(msg: Message, my_agent) -> Message:
    conn_name = msg.content['name']
    their_endpoint = msg.content['endpoint']
    their_connection_key = msg.content['connection_key']

    return Message(
        type=UI.INVITE_RECEIVED,
        content={'name': conn_name,
                 'endpoint': their_endpoint,
                 'connection_key': their_connection_key,
                 'history': msg}
    )


async def send_request(msg: Message, agent) -> Message:
    their_endpoint = msg.content['endpoint']
    conn_name = msg.content['name']
    their_connection_key = msg.content['key']

    my_endpoint_uri = agent.endpoint

    (my_endpoint_did_str, my_connection_key) = await did.create_and_store_my_did(agent.wallet_handle, "{}")

    data_to_send = json.dumps(
        {
            "did": my_endpoint_did_str,
            "key": my_connection_key
        }
    )

    data_to_send_bytes = str_to_bytes(data_to_send)

    meta_json = json.dumps(
        {
            "conn_name": conn_name,
            "their_endpoint": their_endpoint
        }
    )

    await did.set_did_metadata(agent.wallet_handle, my_endpoint_did_str, meta_json)

    inner_msg = Message(
        type=CONN.SEND_REQUEST,
        to="did:sov:ABC",
        endpoint=my_endpoint_uri,
        content=serialize_bytes_json(await crypto.auth_crypt(agent.wallet_handle, my_connection_key, their_connection_key, data_to_send_bytes))
    )

    outer_msg = Message(
        type=FORWARD.FORWARD_TO_KEY,
        to="ABC",
        content=inner_msg
    )

    serialized_outer_msg = Serializer.pack(outer_msg)

    serialized_outer_msg_bytes = str_to_bytes(serialized_outer_msg)

    all_message = Message(
        type=CONN.SEND_REQUEST,
        content=serialize_bytes_json(
            await crypto.anon_crypt(their_connection_key,
                                    serialized_outer_msg_bytes))
    )

    serialized_msg = Serializer.pack(all_message)

    async with aiohttp.ClientSession() as session:
        async with session.post(their_endpoint, data=serialized_msg) as resp:
            print(resp.status)
            print(await resp.text())

    return Message(
        type=UI.REQUEST_SENT,
        id=agent.ui_token,
        content={'name': conn_name}
    )


async def request_received(msg: Message, my_agent) -> Message:
    their_endpoint_uri = msg.endpoint

    my_did_str = msg.did
    my_did_info_str = await did.get_my_did_with_meta(my_agent.wallet_handle, my_did_str)
    my_did_info_json = json.loads(my_did_info_str)

    my_verkey = my_did_info_json['verkey']
    metadata_str = my_did_info_json['metadata']
    metadata_dict = json.loads(metadata_str)

    conn_name = metadata_dict['conn_name']

    message_bytes = str_to_bytes(msg.content)
    message_bytes = base64.b64decode(message_bytes)

    their_key_str, their_data_bytes = await crypto.auth_decrypt(
        my_agent.wallet_handle, my_verkey, message_bytes)

    # change verkey passed via send_invite to the agent without encryption
    my_new_verkey = await did.replace_keys_start(my_agent.wallet_handle, my_did_str, '{}')
    await did.replace_keys_apply(my_agent.wallet_handle, my_did_str)

    their_data_json = json.loads(bytes_to_str(their_data_bytes))

    their_did_str = their_data_json['did']

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

    await did.store_their_did(my_agent.wallet_handle, identity_json)
    await pairwise.create_pairwise(my_agent.wallet_handle, their_did_str, my_did_str, meta_json)

    return Message(
        type=UI.REQUEST_RECEIVED,
        content={
            'name': conn_name,
            'endpoint_did': their_did_str,
            'history': msg
        }
    )


async def send_response(msg: Message, my_agent) -> Message:
    their_did_str = msg.content['endpoint_did']

    pairwise_conn_info_str = await pairwise.get_pairwise(my_agent.wallet_handle, their_did_str)
    pairwise_conn_info_json = json.loads(pairwise_conn_info_str)

    my_did_str = pairwise_conn_info_json['my_did']

    data_to_send = json.dumps(
        {
            "did": my_did_str
        }
    )

    data_to_send_bytes = str_to_bytes(data_to_send)

    metadata_json = json.loads(pairwise_conn_info_json['metadata'])
    conn_name = metadata_json['conn_name']
    their_endpoint = metadata_json['their_endpoint']
    their_verkey_str = metadata_json['their_verkey']

    my_did_info_str = await did.get_my_did_with_meta(my_agent.wallet_handle, my_did_str)
    my_did_info_json = json.loads(my_did_info_str)
    my_verkey_str = my_did_info_json['verkey']

    inner_msg = Message(
        type=CONN.SEND_RESPONSE,
        to="did:sov:ABC",
        content=serialize_bytes_json(await crypto.auth_crypt(
            my_agent.wallet_handle, my_verkey_str, their_verkey_str, data_to_send_bytes))
    )

    outer_msg = Message(
        type=FORWARD.FORWARD,
        to="ABC",
        content=inner_msg
    )

    serialized_outer_msg = Serializer.pack(outer_msg)

    serialized_outer_msg_bytes = str_to_bytes(serialized_outer_msg)

    all_message = Message(
        content=serialize_bytes_json(await crypto.anon_crypt(their_verkey_str,
                                                             serialized_outer_msg_bytes))
    )

    serialized_msg = Serializer.pack(all_message)

    async with aiohttp.ClientSession() as session:
        async with session.post(their_endpoint, data=serialized_msg) as resp:
            print(resp.status)
            print(await resp.text())

    return Message(type=UI.RESPONSE_SENT,
                   id=my_agent.ui_token,
                   content={'name': conn_name})


async def response_received(msg: Message, my_agent) -> Message:
    my_did_str = msg.did

    my_did_info_str = await did.get_my_did_with_meta(my_agent.wallet_handle, my_did_str)
    my_did_info_json = json.loads(my_did_info_str)

    my_verkey = my_did_info_json['verkey']
    metadata_str = my_did_info_json['metadata']
    metadata_dict = json.loads(metadata_str)

    conn_name = metadata_dict['conn_name']
    their_endpoint = metadata_dict['their_endpoint']

    message_bytes = str_to_bytes(msg.content)
    message_bytes = base64.b64decode(message_bytes)

    their_key_str, their_data_bytes = await crypto.auth_decrypt(
        my_agent.wallet_handle, my_verkey, message_bytes)

    their_data_json = json.loads(bytes_to_str(their_data_bytes))

    their_did_str = their_data_json['did']

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

    await did.store_their_did(my_agent.wallet_handle, identity_json)
    await pairwise.create_pairwise(my_agent.wallet_handle, their_did_str, my_did_str, meta_json)

    #  pairwise connection between agents is established to this point
    return Message(
        type=UI.RESPONSE_RECEIVED,
        id=my_agent.ui_token,
        content={'name': conn_name,
                 'their_did': their_did_str,
                 'history': msg}
    )


async def send_message(msg: Message, my_agent) -> Message:
    their_did_str = msg.content['their_did']
    message_to_send = msg.content['message']

    pairwise_conn_info_str = await pairwise.get_pairwise(my_agent.wallet_handle, their_did_str)
    pairwise_conn_info_json = json.loads(pairwise_conn_info_str)

    my_did_str = pairwise_conn_info_json['my_did']

    data_to_send = json.dumps(
        {
            "message": message_to_send
        }
    )

    data_to_send_bytes = str_to_bytes(data_to_send)

    metadata_json = json.loads(pairwise_conn_info_json['metadata'])
    conn_name = metadata_json['conn_name']
    their_endpoint = metadata_json['their_endpoint']
    their_verkey_str = metadata_json['their_verkey']

    my_did_info_str = await did.get_my_did_with_meta(my_agent.wallet_handle,
                                                     my_did_str)
    my_did_info_json = json.loads(my_did_info_str)
    my_verkey_str = my_did_info_json['verkey']

    inner_msg = Message(
        type=CONN.SEND_MESSAGE,
        to="did:sov:ABC",
        content=serialize_bytes_json(
            await crypto.auth_crypt(my_agent.wallet_handle, my_verkey_str,
                                    their_verkey_str, data_to_send_bytes))
    )

    outer_msg = Message(
        type=FORWARD.FORWARD,
        to="ABC",
        content=inner_msg
    )

    serialized_outer_msg = Serializer.pack(outer_msg)

    serialized_outer_msg_bytes = str_to_bytes(serialized_outer_msg)

    all_message = Message(
        content=serialize_bytes_json(await crypto.anon_crypt(their_verkey_str,
                                                             serialized_outer_msg_bytes))
    )

    serialized_msg = Serializer.pack(all_message)

    async with aiohttp.ClientSession() as session:
        async with session.post(their_endpoint, data=serialized_msg) as resp:
            print(resp.status)
            print(await resp.text())

    return Message(type=UI.MESSAGE_SENT,
                   id=my_agent.ui_token,
                   content={'name': conn_name})


async def message_received(msg: Message, my_agent) -> Message:
    my_did_str = msg.did
    their_did_str = ""
    conn_name = ""
    my_verkey = ""

    my_agent_pairwises_list_str = await pairwise.list_pairwise(my_agent.wallet_handle)
    my_agent_pairwises_list = json.loads(my_agent_pairwises_list_str)

    for my_agent_pairwise_str in my_agent_pairwises_list:
        my_agent_pairwise_json = json.loads(my_agent_pairwise_str)
        if not my_agent_pairwise_json['my_did'] == my_did_str:
            continue
        their_did_str = my_agent_pairwise_json['their_did']

        metadata_str = my_agent_pairwise_json['metadata']
        metadata_json = json.loads(metadata_str)
        conn_name = metadata_json['conn_name']
        my_verkey = metadata_json['my_verkey']

    message_bytes = str_to_bytes(msg.content)
    message_bytes = base64.b64decode(message_bytes)

    their_key_str, their_data_bytes = await crypto.auth_decrypt(
        my_agent.wallet_handle, my_verkey, message_bytes)

    their_data_json = json.loads(bytes_to_str(their_data_bytes))

    return Message(
        type=UI.MESSAGE_RECEIVED,
        id=my_agent.ui_token,
        content={'name': conn_name,
                 'their_did': their_did_str,
                 'history': their_data_json}
    )