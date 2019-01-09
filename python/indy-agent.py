""" indy-agent python implementation
"""

# Pylint struggles to find packages inside of a virtual environments;
# pylint: disable=import-error

# Pylint also dislikes the name indy-agent but this follows conventions already
# established in indy projects.
# pylint: disable=invalid-name

import asyncio
import sys
import uuid
import aiohttp_jinja2
import jinja2
import base64
import json
import argparse

from aiohttp import web
from indy import crypto, did, error, IndyError, wallet

from helpers import deserialize_bytes_json, str_to_bytes, bytes_to_str
from modules.connection import Connection, AdminConnection
from modules.admin import Admin
from modules.admin_walletconnection import AdminWalletConnection
from modules.basicmessage import AdminBasicMessage, BasicMessage

import modules.admin
import serializer.json_serializer as Serializer
from receiver.message_receiver import MessageReceiver as Receiver
from ui_event import UIEventQueue
from agent import Agent
from message import Message


# Argument Parsing
parser = argparse.ArgumentParser()
parser.add_argument("port", nargs="?", default="8080", type=int, help="The port to attach.")
parser.add_argument("--wallet", nargs=2, metavar=('walletname','walletpass'), help="The name and passphrase of the wallet to connect to.")
parser.add_argument("--ephemeralwallet", action="store_true", help="Use ephemeral wallets")
args = parser.parse_args()

# config webapp

LOOP = asyncio.get_event_loop()

WEBAPP = web.Application()

aiohttp_jinja2.setup(WEBAPP, loader=jinja2.FileSystemLoader('view'))

WEBAPP['msg_receiver'] = Receiver()

WEBAPP['ui_event_queue'] = UIEventQueue(LOOP)

WEBAPP['conn_receiver'] = Receiver()

AGENT = Agent()

WEBAPP['agent'] = AGENT

AGENT.register_module(Admin)
AGENT.register_module(Connection)
AGENT.register_module(AdminConnection)
AGENT.register_module(AdminWalletConnection)
AGENT.register_module(BasicMessage)
AGENT.register_module(AdminBasicMessage)


ROUTES = [
    web.get('/', modules.admin.root),
    web.get('/ws', WEBAPP['ui_event_queue'].ws_handler),
    web.static('/res', 'view/res'),
    web.post('/indy', WEBAPP['msg_receiver'].handle_message),
    web.post('/offer', WEBAPP['conn_receiver'].handle_message)
]

WEBAPP.add_routes(ROUTES)

RUNNER = web.AppRunner(WEBAPP)
LOOP.run_until_complete(RUNNER.setup())

SERVER = web.TCPSite(runner=RUNNER, port=args.port)

if args.wallet:
    try:
        LOOP.run_until_complete(AGENT.connect_wallet(args.wallet[0], args.wallet[1], ephemeral=args.ephemeralwallet))
        print("Connected to wallet via command line args: {}".format(args.wallet[0]))
    except Exception as e:
        print(e)
else:
    print("Configure wallet connection via UI.")

async def conn_process(agent):
    conn_receiver = agent['conn_receiver']
    ui_event_queue = agent['ui_event_queue']

    while True:
        msg_bytes = await conn_receiver.recv()
        try:
            msg = Serializer.unpack(msg_bytes)
        except Exception as e:
            print('Failed to unpack message: {}\n\nError: {}'.format(msg_bytes, e))
            continue

        res = await AGENT.route_message_to_module(msg)
        if res is not None:
            await ui_event_queue.send(Serializer.pack(res))


async def message_process(agent):
    """ Message processing loop task.
    """
    msg_receiver = agent['msg_receiver']
    ui_event_queue = agent['ui_event_queue']

    while True:
        wire_msg_bytes = await msg_receiver.recv()

        try:
            msg = await agent['agent'].unpack_agent_message(wire_msg_bytes)
        except Exception as e:
            print('Failed to unpack message: {}\n\nError: {}'.format(wire_msg_bytes, e))
            continue  # handle next message in loop

        #route message by payload type
        res = await AGENT.route_message_to_module(msg)

        if res is not None:
            await ui_event_queue.send(Serializer.pack(res))

async def ui_event_process(agent):
    ui_event_queue = agent['ui_event_queue']

    while True:
        msg = await ui_event_queue.recv()

        if not isinstance(msg, Message):
            try:
                msg = Serializer.unpack(msg)
            except Exception as e:
                print('Failed to unpack message: {}\n\nError: {}'.format(msg, e))
                continue

        res = await AGENT.route_message_to_module(msg)
        if res is not None:
            await ui_event_queue.send(Serializer.pack(res))

try:
    print('===== Starting Server on: http://localhost:{} ====='.format(args.port))
    LOOP.create_task(SERVER.start())
    LOOP.create_task(conn_process(WEBAPP))
    LOOP.create_task(message_process(WEBAPP))
    LOOP.create_task(ui_event_process(WEBAPP))
    LOOP.run_forever()
except KeyboardInterrupt:
    print("exiting")
