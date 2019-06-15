""" Module containing serializers.

    These functions are provided as definitions of the basic interface
    that all serializers should implement.

    This abstraction is intended to allow easily switching from one form
    of serialization to another.
"""

from python_agent_utils.messages.message import Message


class BaseSerializer:
    @staticmethod
    def deserialize(dump: bytes) -> Message:  #pylint: disable=unused-argument
        """ Deserialize to Message.
        """

        raise NotImplementedError("Unpack method in serializer module \
            is not implemented. Use the methods contained in a submodule of \
            serializer, such as json_serializer.")

    @staticmethod
    def serialize(msg: Message) -> bytes:  #pylint: disable=unused-argument
        """ Serialize to bytes.
        """

        raise NotImplementedError("Pack method in serializer module \
            is not implemented. Use the methods contained in a submodule of \
            serializer, such as json_serializer.")
