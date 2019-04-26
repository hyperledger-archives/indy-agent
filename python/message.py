""" Module defining the Message class that is used as base structure for all
    received messages.
"""
import json
from collections import UserDict

import uuid


class Message(UserDict):
    """ Data Model for messages.
    """
    def __init__(self, *args, **kwargs):
        """ Create a Message object

        @type: string denoting the message type. Standardization efforts are in progress.
        @id: identifier for message. Usually a nonce or a DID. This combined with the type
            tell us how to interpret the message.
        other things: ambiguous data. Interpretation defined by type and id.

        """
        UserDict.__init__(self,*args, **kwargs)
        self.context = {}
        # Assign it an ID
        if '@id' not in self.data:
            self.data['@id'] = str(uuid.uuid4())

    def to_dict(self):
        return self.data

    @property
    def type(self):
        return self.data["@type"]

    @property
    def id(self):
        return self.data["@id"]

    class MessageEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Message):
                return obj.to_dict()
            return json.JSONEncoder.default(self, obj)

    def as_json(self):
        return json.dumps(self, cls=Message.MessageEncoder)

    def pretty_print(self):
        return json.dumps(self, sort_keys=True, indent=2, cls=Message.MessageEncoder)
