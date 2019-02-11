import re
import base64

from serializer import JSONSerializer as Serializer
from message import Message
from tests import validate_message

class Connection:
    class Message:
        FAMILY_NAME = "connections"
        VERSION = "1.0"
        FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

        INVITE = FAMILY + "invite"
        REQUEST = FAMILY + "request"
        RESPONSE = FAMILY + "response"

    class Invite:
        @staticmethod
        def parse(invite_url: str) -> Message:
            matches = re.match('(.+)?c_i=(.+)', invite_url)
            assert matches, 'Improperly formatted invite url!'

            invite_msg = Serializer.unpack(
                base64.urlsafe_b64decode(matches.group(2)).decode('utf-8')
            )

            validate_message(
                [
                    ('@type', Connection.Message.INVITE),
                    'label',
                    'recipient_keys',
                    'serviceEndpoint'
                ],
                invite_msg
            )

            return invite_msg

    class Request:
        @staticmethod
        def build(label: str, my_did: str, my_vk: str, endpoint: str) -> Message:
            return Message({
                '@type': Connection.Message.REQUEST,
                'label': label,
                'connection': {
                    'DID': my_did,
                    'DIDDoc': {
                        "@context": "https://w3id.org/did/v1",
                        "publicKey": [{
                            "id": my_did + "#keys-1",
                            "type": "Ed25519VerificationKey2018",
                            "controller": my_did,
                            "publicKeyBase58": my_vk
                        }],
                        "service": [{
                            "type": "IndyAgent",
                            "recipient_keys": [my_vk],
                            #"routing_keys": ["<example-agency-verkey>"],
                            "serviceEndpoint": endpoint,
                        }],
                    }
                }
            })

    class Response:
        @staticmethod
        def build(my_did: str, my_vk: str, endpoint: str) -> Message:
            return Message({
                '@type': Connection.Message.RESPONSE,
                'connection': {
                    'DID': my_did,
                    'DIDDoc': {
                        "@context": "https://w3id.org/did/v1",
                        "publicKey": [{
                            "id": my_did + "#keys-1",
                            "type": "Ed25519VerificationKey2018",
                            "controller": my_did,
                            "publicKeyBase58": my_vk
                        }],
                        "service": [{
                            "type": "IndyAgent",
                            "recipient_keys": [my_vk],
                            #"routing_keys": ["<example-agency-verkey>"],
                            "serviceEndpoint": endpoint,
                        }],
                    }
                }
            })

        @staticmethod
        def validate_pre_sig(response: Message):
            validate_message(
                [
                    ('@type', Connection.Message.RESPONSE),
                    'connection~sig'
                ],
                response
            )

        @staticmethod
        def validate(response: Message):
            validate_message(
                [
                    ('@type', Connection.Message.RESPONSE),
                    'connection'
                ],
                response
            )

            validate_message(
                [
                    'DID',
                    'DIDDoc'
                ],
                response['connection']
            )

            validate_message(
                [
                    '@context',
                    'publicKey',
                    'service'
                ],
                response['connection']['DIDDoc']
            )

            for publicKeyBlock in response['connection']['DIDDoc']['publicKey']:
                validate_message(
                    [
                        'id',
                        'type',
                        'controller',
                        'publicKeyBase58'
                    ],
                    publicKeyBlock
                )

            for serviceBlock in response['connection']['DIDDoc']['service']:
                validate_message(
                    [
                        ('type', 'IndyAgent'),
                        'recipient_keys',
                        'serviceEndpoint'
                    ],
                    serviceBlock
                )
