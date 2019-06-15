import uuid

from .message import Message


class TrustPing(Message):
    FAMILY_NAME = "trust_ping"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    PING = FAMILY + "ping"
    PING_RESPONSE = FAMILY + "ping_response"

    class Ping:
        @staticmethod
        def build():
            return Message({
                '@type': TrustPing.PING,
                '@id': str(uuid.uuid4())
            })

        @staticmethod
        def validate(message):
            message.check_for_attrs(
                [
                    ('@type', TrustPing.PING),
                    '@id'
                ]
            )

    class Pong:
        @staticmethod
        def build(ping_id: str):
            return Message({
                '@type': TrustPing.PING_RESPONSE,
                '~thread': {Message.THREAD_ID: ping_id, Message.SENDER_ORDER: 0}
            })

        @staticmethod
        def validate(message, ping_id):
            message.check_for_attrs(
                [
                    ('@type', TrustPing.PING_RESPONSE),
                    '~thread'
                ]
            )

            Message.check_for_attrs_in_message(
                [
                    ('thid', ping_id)
                ],
                message['~thread']
            )
