import re
import base64
import uuid
from typing import Optional

from .message import Message
from .did_doc import DIDDoc
from test_suite.serializer import JSONSerializer as Serializer


class Connection(Message):

    FAMILY_NAME = "connections"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    CONNECTION = 'connection'
    INVITE = FAMILY + "invitation"
    REQUEST = FAMILY + "request"
    RESPONSE = FAMILY + "response"
    REQUEST_NOT_ACCEPTED = "request_not_accepted"

    # Problem codes
    # No corresponding connection request found
    RESPONSE_FOR_UNKNOWN_REQUEST = "response_for_unknown_request"

    # Verkey provided in response does not match expected key
    KEY_ERROR = "verkey_error"

    class Invite:
        @staticmethod
        def parse(invite_url: str) -> Message:
            matches = re.match('(.+)?c_i=(.+)', invite_url)
            assert matches, 'Improperly formatted invite url!'

            invite_msg = Serializer.unpack(
                base64.urlsafe_b64decode(matches.group(2)).decode('ascii')
            )

            invite_msg.check_for_attrs(
                [
                    ('@type', Connection.INVITE),
                    'label',
                    'recipientKeys',
                    'serviceEndpoint'
                ]
            )

            return invite_msg

        @staticmethod
        def build(label: str, connection_key: str, endpoint: str) -> str:
            msg = Message({
                '@type': Connection.INVITE,
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
                '@type': Connection.REQUEST,
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
            request.check_for_attrs(
                [
                    ('@type', Connection.REQUEST),
                    '@id',
                    'label',
                    Connection.CONNECTION
                ]
            )

            Message.check_for_attrs_in_message(
                [
                    DIDDoc.DID,
                    DIDDoc.DID_DOC
                ],
                request[Connection.CONNECTION]
            )

            DIDDoc.validate(request[Connection.CONNECTION][DIDDoc.DID_DOC])

    class Response:
        @staticmethod
        def build(req_id: str, my_did: str, my_vk: str, endpoint: str) -> Message:
            return Message({
                '@type': Connection.RESPONSE,
                '@id': str(uuid.uuid4()),
                '~thread': {Message.THREAD_ID: req_id, Message.SENDER_ORDER: 0},
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
            response.check_for_attrs(
                [
                    ('@type', Connection.RESPONSE),
                    '~thread',
                    'connection~sig'
                ]
            )

        @staticmethod
        def validate(response: Message, req_id: str):
            response.check_for_attrs(
                [
                    ('@type', Connection.RESPONSE),
                    '~thread',
                    'connection'
                ]
            )

            Message.check_for_attrs_in_message(
                [
                    (Message.THREAD_ID, req_id)
                ],
                response['~thread']
            )

            Message.check_for_attrs_in_message(
                [
                    DIDDoc.DID,
                    DIDDoc.DID_DOC
                ],
                response[Connection.CONNECTION]
            )

            DIDDoc.validate(response[Connection.CONNECTION][DIDDoc.DID_DOC])

    # TODO: Following 2 methods should be available on base Message.
    #  Or the context should have verkey and endpoint info so that an error message can be returned.
    @staticmethod
    def extract_verkey_endpoint(msg: Message) -> (Optional, Optional):
        """
        Extract verkey and endpoint that will be used to send message back to the sender of this message. Might return None.
        """
        vks = msg.get(Connection.CONNECTION, {}).get(DIDDoc.DID_DOC, {}).get('publicKey')
        vk = vks[0].get('publicKeyBase58') if vks and isinstance(vks, list) and len(vks) > 0 else None
        endpoints = msg.get(Connection.CONNECTION, {}).get(DIDDoc.DID_DOC, {}).get('service')
        endpoint = endpoints[0].get('serviceEndpoint') if endpoints and isinstance(endpoints, list) and len(
            endpoints) > 0 else None
        return vk, endpoint

    @staticmethod
    def extract_their_info(msg: Message):
        """
        Extract the other participant's DID, verkey and endpoint
        :param msg:
        :return: Return a 3-tuple of (DID, verkey, endpoint
        """
        their_did = msg[Connection.CONNECTION][DIDDoc.DID]
        # NOTE: these values are pulled based on the minimal connectathon format. Full processing
        #  will require full DIDDoc storage and evaluation.
        their_vk = msg[Connection.CONNECTION][DIDDoc.DID_DOC]['publicKey'][0]['publicKeyBase58']
        their_endpoint = msg[Connection.CONNECTION][DIDDoc.DID_DOC]['service'][0]['serviceEndpoint']
        return their_did, their_vk, their_endpoint
