""" Module defining Agent class and related methods
"""
import json
import base64
import asyncio
import traceback
import aiohttp
from indy import wallet, did, error, crypto, pairwise, non_secrets

from serializer import json_serializer as Serializer
from helpers import bytes_to_str, serialize_bytes_json, str_to_bytes
from message import Message
from router.family_router import FamilyRouter

class WalletConnectionException(Exception):
    pass

class Agent:
    """ Agent class storing all needed elements for agent operation.
    """
    def __init__(self):
        self.owner = None
        self.wallet_handle = None
        self.endpoint = None
        self.endpoint_vk = None
        self.ui_token = None
        self.pool_handle = None
        self.ui_socket = None
        self.initialized = False
        self.modules = {}
        self.family_router = FamilyRouter()
        self.message_queue = asyncio.Queue()
        self.outbound_admin_message_queue = asyncio.Queue()

    def register_module(self, module):
        self.modules[module.FAMILY] = module(self)
        self.family_router.register(module.FAMILY, self.modules[module.FAMILY])

    async def route_message_to_module(self, message):
        return await self.family_router.route(message)

    async def start(self):
        """ Message processing loop task.
        """
        while True:
            try:
                wire_msg_bytes = await self.message_queue.get()

                # Try to unpack message assuming it's not encrypted
                try:
                    msg = Serializer.unpack(wire_msg_bytes)
                except Exception as e:
                    print("Message encryped, attempting to unpack...")

                # TODO: More graceful checking here
                # (This is an artifact of the provisional wire format and connection protocol)
                if not isinstance(msg, Message) or "@type" not in msg:
                    # Message IS encrypted so unpack it
                    try:
                        msg = await self.unpack_agent_message(wire_msg_bytes)
                    except Exception as e:
                        print('Failed to unpack message: {}\n\nError: {}'.format(wire_msg_bytes, e))
                        continue  # handle next message in loop

                await self.route_message_to_module(msg)
            except Exception as e:
                    print("\n\n--- Message Processing failed --- \n\n")
                    traceback.print_exc()

    async def connect_wallet(self, agent_name, passphrase, ephemeral=False):
        """ Create if not already exists and open wallet.
        """

        self.owner = agent_name
        wallet_suffix = "wallet"
        if ephemeral:
            wallet_suffix = "ephemeral_wallet"
        wallet_name = '{}-{}'.format(self.owner, wallet_suffix)

        wallet_config = json.dumps({"id": wallet_name})
        wallet_credentials = json.dumps({"key": passphrase})

        # Handle ephemeral wallets
        if ephemeral:
            try:
                await wallet.delete_wallet(wallet_config, wallet_credentials)
                print("Removing ephemeral wallet.")
            except error.IndyError as e:
                if e.error_code is error.ErrorCode.WalletNotFoundError:
                    pass  # This is ok, and expected.
                else:
                    print("Unexpected Indy Error: {}".format(e))
            except Exception as e:
                print(e)
        # pylint: disable=bare-except

        try:
            await wallet.create_wallet(wallet_config, wallet_credentials)
        except error.IndyError as e:
            if e.error_code is error.ErrorCode.WalletAlreadyExistsError:
                pass # This is ok, and expected.
            else:
                print("Unexpected Indy Error: {}".format(e))
        except Exception as e:
            print(e)

        try:
            self.wallet_handle = await wallet.open_wallet(
                wallet_config,
                wallet_credentials
            )

            (_, self.endpoint_vk) = await did.create_and_store_my_did(self.wallet_handle, "{}")

            self.initialized = True

        except Exception as e:
            print(e)
            print("Could not open wallet!")

            raise WalletConnectionException


    async def unpack_agent_message(self, wire_msg_bytes):
        wire_msg = json.loads(wire_msg_bytes)

        # get key from wallet from to: did
        # TODO: add error reporting if DID not found

        #load my key list
        did_list_str = await did.list_my_dids_with_meta(self.wallet_handle)
        did_list = json.loads(did_list_str)
        my_verkey_to_did = {}
        for d in did_list:
            my_verkey_to_did[d['verkey']] = d['did']

        if wire_msg['to'] not in my_verkey_to_did:
            try:
                connection_key = json.loads(
                    await non_secrets.get_wallet_record(
                        self.wallet_handle,
                        'connection_key',
                        wire_msg['to'],
                        '{}'
                    )
                )['value']
                my_verkey_to_did[wire_msg['to']] = None
            except Exception as e:
                raise Exception("Unknown recipient key")

        #load pairwise
        pairwise_list_str = await pairwise.list_pairwise(self.wallet_handle)
        pairwise_list = json.loads(pairwise_list_str)
        their_verkey_to_did = {}
        for p_str in pairwise_list:
            p = json.loads(p_str)
            p_meta = json.loads(p['metadata'])
            their_verkey_to_did[p_meta['their_vk']] = p['their_did']

        from_did = None
        if wire_msg['from'] in their_verkey_to_did:
            from_did = their_verkey_to_did[wire_msg['from']]

        # now process payload
        message_bytes = base64.b64decode(wire_msg['payload'])

        their_key_str, their_data_bytes = await crypto.auth_decrypt(
            self.wallet_handle, wire_msg['to'], message_bytes)

        msg_str = bytes_to_str(their_data_bytes)
        msg_json = json.loads(msg_str)

        msg = Message(msg_json)

        msg.context = {
            'from_did': from_did, # will be none if unknown sender verkey
            'from_key': their_key_str,
            'to_key': wire_msg['to'],
            'to_did': my_verkey_to_did[wire_msg['to']]
        }
        return msg

    async def send_message_to_agent(self, to_did, msg:Message):
        their_did = to_did

        pairwise_info = json.loads(await pairwise.get_pairwise(self.wallet_handle, their_did))
        pairwise_meta = json.loads(pairwise_info['metadata'])

        my_did = pairwise_info['my_did']
        their_endpoint = pairwise_meta['their_endpoint']
        their_vk = pairwise_meta['their_vk']

        my_vk = await did.key_for_local_did(self.wallet_handle, my_did)

        await self.send_message_to_endpoint_and_key(my_vk, their_vk, their_endpoint, msg)

    # used directly when sending to an endpoint without a known did
    async def send_message_to_endpoint_and_key(self, my_ver_key, their_ver_key, their_endpoint, msg):
        wire_message = {
            'to': their_ver_key,
            'from': my_ver_key,
            'payload': serialize_bytes_json(await crypto.auth_crypt(self.wallet_handle, my_ver_key,
                                                                    their_ver_key, str_to_bytes(msg.as_json())))
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(their_endpoint, data=json.dumps(wire_message)) as resp:
                print(resp.status)
                print(await resp.text())

    async def send_admin_message(self, msg: Message):
        await self.outbound_admin_message_queue.put(msg.as_json())
