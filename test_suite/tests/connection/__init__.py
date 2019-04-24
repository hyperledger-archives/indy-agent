import re
import base64
import uuid
from typing import Optional, Tuple

from test_suite.serializer import JSONSerializer as Serializer
from test_suite.message import Message
from test_suite.tests import validate_message
from test_suite.tests.did_doc import DIDDoc


class Connection:
    CONNECTION = 'connection'

    class Message:
        FAMILY_NAME = "connections"
        VERSION = "1.0"
        FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

        INVITE = FAMILY + "invitation"
        REQUEST = FAMILY + "request"
        RESPONSE = FAMILY + "response"

    class Invite:
        @staticmethod
        def parse(invite_url: str) -> Message:
            matches = re.match('(.+)?c_i=(.+)', invite_url)
            assert matches, 'Improperly formatted invite url!'

            invite_msg = Serializer.unpack(
                base64.urlsafe_b64decode(matches.group(2)).decode('ascii')
            )

            validate_message(
                [
                    ('@type', Connection.Message.INVITE),
                    'label',
                    'recipientKeys',
                    'serviceEndpoint'
                ],
                invite_msg
            )

            return invite_msg

        @staticmethod
        def build(label: str, connection_key: str, endpoint: str) -> str:
            msg = Message({
                '@type': Connection.Message.INVITE,
                'label': label,
                'recipientKeys': [connection_key],
                'serviceEndpoint': endpoint,
                # routing_keys not specified, but here is where they would be put in the invite.
            })

            b64_invite = base64.urlsafe_b64encode(
                bytes(
                    Serializer.pack(msg),
                    'ascii'
                )
            ).decode('ascii')

            return '{}?c_i={}'.format(endpoint, b64_invite)

    class Request:
        @staticmethod
        def parse(request: Message):
            return (
                request[Connection.CONNECTION][DIDDoc.DID_DOC]['publicKey'][0]['controller'],
                request[Connection.CONNECTION][DIDDoc.DID_DOC]['publicKey'][0]['publicKeyBase58'],
                request[Connection.CONNECTION][DIDDoc.DID_DOC]['service'][0]['serviceEndpoint']
            )

        @staticmethod
        def build(label: str, my_did: str, my_vk: str, endpoint: str) -> Message:
            return Message({
                '@type': Connection.Message.REQUEST,
                '@id': str(uuid.uuid4()),
                'label': label,
                'connection': {
                    'did': my_did,
                    'did_doc': {
                        "@context": "https://w3id.org/did/v1",
                        "id": my_did,
                        "publicKey": [{
                            "id": my_did + "#keys-1",
                            "type": "Ed25519VerificationKey2018",
                            "controller": my_did,
                            "publicKeyBase58": my_vk
                        }],
                        "service": [{
                            "id": my_did + ";indy",
                            "type": "IndyAgent",
                            "recipientKeys": [my_vk],
                            #"routingKeys": ["<example-agency-verkey>"],
                            "serviceEndpoint": endpoint,
                        }],
                    }
                }
            })

        @staticmethod
        def validate(request):
            validate_message(
                [
                    ('@type', Connection.Message.REQUEST),
                    '@id',
                    'label',
                    Connection.CONNECTION
                ],
                request
            )

            validate_message(
                [
                    DIDDoc.DID,
                    DIDDoc.DID_DOC
                ],
                request[Connection.CONNECTION]
            )

            DIDDoc.validate(request[Connection.CONNECTION][DIDDoc.DID_DOC])

        @staticmethod
        def extract_verkey_endpoint(msg: Message) -> (Optional, Optional):
            """
            Extract verkey and endpoint that will be used to send message back to the sender of this message. Might return None.
            """
            vks = msg.get(Connection.CONNECTION, {}).get(DIDDoc.DID_DOC, {}).get('publicKey')
            vk = vks[0].get('publicKeyBase58') if vks and isinstance(vks, list) and len(vks) > 0 else None
            endpoints = msg.get(Connection.CONNECTION, {}).get(DIDDoc.DID_DOC, {}).get('service')
            endpoint = endpoints[0].get('serviceEndpoint') if endpoints and isinstance(endpoints, list) and len(endpoints) > 0 else None
            return vk, endpoint

    class Response:
        @staticmethod
        def build(req_id: str, my_did: str, my_vk: str, endpoint: str) -> Message:
            return Message({
                '@type': Connection.Message.RESPONSE,
                '@id': str(uuid.uuid4()),
                '~thread': {'thid': req_id},
                'connection': {
                    'did': my_did,
                    'did_doc': {
                        "@context": "https://w3id.org/did/v1",
                        "id": my_did,
                        "publicKey": [{
                            "id": my_did + "#keys-1",
                            "type": "Ed25519VerificationKey2018",
                            "controller": my_did,
                            "publicKeyBase58": my_vk
                        }],
                        "service": [{
                            "id": my_did + ";indy",
                            "type": "IndyAgent",
                            "recipientKeys": [my_vk],
                            #"routingKeys": ["<example-agency-verkey>"],
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
                    '~thread',
                    'connection~sig'
                ],
                response
            )

        @staticmethod
        def validate(response: Message, req_id: str):
            validate_message(
                [
                    ('@type', Connection.Message.RESPONSE),
                    '~thread',
                    'connection'
                ],
                response
            )

            validate_message(
                [
                    ('thid', req_id)
                ],
                response['~thread']
            )

            validate_message(
                [
                    DIDDoc.DID,
                    DIDDoc.DID_DOC
                ],
                response[Connection.CONNECTION]
            )

            DIDDoc.validate(response[Connection.CONNECTION][DIDDoc.DID_DOC])

