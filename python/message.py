""" Module defining the Message class that is used as base structure for all
    received messages.
"""

class Message(object):
    """ Data Model for messages.
    """
    def __init__(self, **kwargs):
        """ Create a Message object

        type: string denoting the message type. Standardization efforts are in progress.
        id: identifier for message. Usually a nonce or a DID. This combined with the type
            tell us how to interpret the message.
        message: ambiguous data. Interpretation defined by type and id.

        """
        for key in kwargs.keys():
            self.__setattr__(key, kwargs[key])

    def to_dict(self):
        return self.__dict__
