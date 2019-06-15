"""
Serializer using json as i/o format.
"""

import json

from python_agent_utils.messages.message import Message
from . import BaseSerializer


class JSONSerializer(BaseSerializer):
    """ Serializer using json as i/o format.
    """
    @staticmethod
    def deserialize(dump: bytes) -> Message:
        """ Deserialize from json string to Message, if it looks like a Message.
            Returns a dictionary otherwise.
        """

        return Message(json.loads(dump))

    @staticmethod
    def serialize(msg: Message) -> bytes:
        """ Serialize from Message to json string or from dictionary to json string.
        """

        return msg.as_json().encode('utf-8')
