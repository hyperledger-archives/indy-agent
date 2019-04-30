from .message import Message


class DIDDoc:
    DID = 'did'
    DID_DOC = 'did_doc'

    @staticmethod
    def validate(did_doc):
        Message.validate_message(
            [
                '@context',
                'publicKey',
                'service'
            ],
            did_doc
        )

        for publicKeyBlock in did_doc['publicKey']:
            Message.validate_message(
                [
                    'id',
                    'type',
                    'controller',
                    'publicKeyBase58'
                ],
                publicKeyBlock
            )

        for serviceBlock in did_doc['service']:
            Message.validate_message(
                [
                    ('type', 'IndyAgent'),
                    'recipientKeys',
                    'serviceEndpoint'
                ],
                serviceBlock
            )
