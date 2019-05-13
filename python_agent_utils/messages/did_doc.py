from .message import Message


class DIDDoc:
    DID = 'did'
    DID_DOC = 'did_doc'

    @staticmethod
    def validate(did_doc):
        Message.check_for_attrs_in_message(
            [
                '@context',
                'publicKey',
                'service'
            ],
            did_doc
        )

        for publicKeyBlock in did_doc['publicKey']:
            Message.check_for_attrs_in_message(
                [
                    'id',
                    'type',
                    'controller',
                    'publicKeyBase58'
                ],
                publicKeyBlock
            )

        for serviceBlock in did_doc['service']:
            Message.check_for_attrs_in_message(
                [
                    ('type', 'IndyAgent'),
                    'recipientKeys',
                    'serviceEndpoint'
                ],
                serviceBlock
            )
