""" Module defining the Message class that is used as base structure for all
    received messages.
"""
import json
from collections import UserDict
from typing import Iterable

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

    def validate(self, expected_attrs: Iterable):
        Message.validate_message(expected_attrs, self)

    @staticmethod
    def validate_message(expected_attrs: Iterable, msg):
        for attribute in expected_attrs:
            if isinstance(attribute, tuple):
                if attribute[0] not in msg:
                    raise KeyError('Attribute "{}" is missing from message: \n{}'.format(attribute[0], msg))
                if msg[attribute[0]] != attribute[1]:
                    raise KeyError('Message.{}: {} != {}'.format(attribute[0], msg[attribute[0]], attribute[1]))
            else:
                if attribute not in msg:
                    raise KeyError('Attribute "{}" is missing from message: \n{}'.format(attribute, msg))