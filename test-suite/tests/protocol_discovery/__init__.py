import uuid
from message import Message
from tests import validate_message

class ProtocolDiscovery:
    class Message:
        FAMILY_NAME = "protocol_discovery"
        VERSION = "1.0"
        FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

        QUERY = FAMILY + "query"
        DISCLOSE = FAMILY + "disclose"

    class Query:
        @staticmethod
        def build(query: str):
            return Message({
                '@type': ProtocolDiscovery.Message.QUERY,
                '@id': str(uuid.uuid4()),
                'query': query
            })

        @staticmethod
        def validate(query):
            validate_message(
                [
                    ('@type', ProtocolDiscovery.Message.QUERY),
                    '@id',
                    'query'
                ],
                query
            )

    class Disclose:
        @staticmethod
        def build(thid: str, supported_families: [str]):
            return Message({
                '@type': ProtocolDiscovery.Message.DISCLOSE,
                '~thread': {'thid': thid},
                'protocols': list(map(lambda mod: {'pid': mod}, supported_families))
            })

        @staticmethod
        def validate(disclose, thid):
            validate_message(
                [
                    ('@type', ProtocolDiscovery.Message.DISCLOSE),
                    '~thread',
                    'protocols'
                ],
                disclose
            )
            validate_message(
                [
                    ('thid', thid)
                ],
                disclose['~thread']
            )
