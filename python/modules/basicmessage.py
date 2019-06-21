""" Module allowing a user to send and receive basic messages with their Indy agent.
"""
import datetime
import json
import uuid

from indy import non_secrets

from indy_sdk_utils import get_wallet_records
from python_agent_utils.messages.message import Message
from router.simple_router import SimpleRouter
from . import Module


class AdminBasicMessage(Module):
    """ Class handling messages received from the UI.
    """
    FAMILY_NAME = "admin_basicmessage"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION

    MESSAGE_RECEIVED = FAMILY + "/message_received"
    SEND_MESSAGE = FAMILY + "/send_message"
    MESSAGE_SENT = FAMILY + "/message_sent"
    GET_MESSAGES = FAMILY + "/get_messages"
    MESSAGES = FAMILY + "/messages"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(AdminBasicMessage.SEND_MESSAGE, self.send_message)
        self.router.register(AdminBasicMessage.GET_MESSAGES, self.get_messages)

    async def route(self, msg: Message) -> None:
        """ Route a message to its registered callback.
        """
        return await self.router.route(msg)

    async def send_message(self, msg: Message) -> None:
        """ UI activated method providing a message to be sent.

        :param msg: Message from the UI to send a basic message to another Indy agent. It contains:
            {
                '@type': AdminBasicMessage.SEND_MESSAGE,
                'from': 'TkbZ5zphpvX4MYDhRRQ5o7',  # DID of the sender of the message.
                'to': 'Q3TnvPk6QtRazeiALDdLGs',  # DID fo the recipient of the message.
                'message': 'Hello',  # text of the message to be sent.
            }
        """
        my_did_str = msg['from']
        their_did_str = msg['to']
        message_to_send = msg['message']
        sent_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc).isoformat(' ')

        # Store message in the wallet
        await non_secrets.add_wallet_record(
            self.agent.wallet_handle,
            'basicmessage',
            uuid.uuid4().hex,
            json.dumps({
                'from': my_did_str,
                'sent_time': sent_time,
                'content': message_to_send
            }),
            json.dumps({
                'their_did': their_did_str
            })
        )

        message = Message({
            '@type': BasicMessage.MESSAGE,
            '~l10n': {'locale': 'en'},
            'sent_time': sent_time,
            'content': message_to_send
        })

        await self.agent.send_message_to_agent(their_did_str, message)

        await self.agent.send_admin_message(
            Message({
                '@type': AdminBasicMessage.MESSAGE_SENT,
                'id': self.agent.ui_token,
                'with': their_did_str,
                'message': {
                    'from': my_did_str,
                    'sent_time': sent_time,
                    'content': message_to_send
                }
            })
        )

    async def get_messages(self, msg: Message) -> None:
        """ UI activated method requesting a list of messages exchanged with a given agent.

        :param msg: Message from the UI to get a list of message exchanged with a given DID:
            {
                '@type': AdminBasicMessage.GET_MESSAGES,
                'with': 'CzznW3pTbFr2YqDCGWWf8x',  # DID of other party with whom messages
                                                   # have been exchanged
            }
        :return: None
        """
        their_did = msg['with']
        messages = await get_wallet_records(self.agent.wallet_handle, 'basicmessage',
                                            json.dumps({'their_did': their_did}))
        messages = sorted(messages, key=lambda n: n['sent_time'], reverse=True)

        await self.agent.send_admin_message(
            Message({
                '@type': AdminBasicMessage.MESSAGES,
                'with': their_did,
                'messages': messages
            })
        )


class BasicMessage(Module):
    """ Class handling messages received from another Indy agent.
    """
    FAMILY_NAME = "basicmessage"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION

    MESSAGE = FAMILY + "/message"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(BasicMessage.MESSAGE, self.receive_message)

    async def route(self, msg: Message) -> None:
        """ Route a message to its registered callback.
        """
        return await self.router.route(msg)

    async def receive_message(self, msg: Message) -> None:
        """ Process the reception of a basic message from another Indy agent.

        :param msg: Basic message is of the following format:
            {
                '@type': BasicMessage.MESSAGE,
                '~l10n': {'locale': 'en'},
                'sent_time': '2019-05-27 08:34:25.105373+00:00',
                'content': 'Hello'
            }
        :return: None
        """
        is_valid = await self.validate_common_message_blocks(msg, BasicMessage.FAMILY)
        if not is_valid:
            return

        # Store message in the wallet
        await non_secrets.add_wallet_record(
            self.agent.wallet_handle,
            'basicmessage',
            uuid.uuid4().hex,
            json.dumps({
                'from': msg.context['from_did'],
                'sent_time': msg['sent_time'],
                'content': msg['content']
            }),
            json.dumps({
                'their_did': msg.context['from_did']
            })
        )

        await self.agent.send_admin_message(
            Message({
                '@type': AdminBasicMessage.MESSAGE_RECEIVED,
                'id': self.agent.ui_token,
                'with': msg.context['from_did'],
                'message': {
                    'from': msg.context['from_did'],
                    'sent_time': msg['sent_time'],
                    'content': msg['content']
                }
            })
        )
