""" Module defining Agent class and related methods
"""
import json
from indy import wallet, did

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
        self.modules = []

    async def connect_wallet(self, agent_name, passphrase):
        """ Create if not already exists and open wallet.
        """

        self.owner = agent_name
        wallet_name = '{}-wallet'.format(self.owner)

        wallet_config = json.dumps({"id": wallet_name})
        wallet_credentials = json.dumps({"key": passphrase})

        # pylint: disable=bare-except
        # TODO: better handle potential exceptions.
        try:
            await wallet.create_wallet(wallet_config, wallet_credentials)
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

