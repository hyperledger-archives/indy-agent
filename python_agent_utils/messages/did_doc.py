from .message import Message


class DIDDoc(Message):
    DID = 'did'
    DID_DOC = 'did_doc'

    @staticmethod
    def validate(did_doc: Message):
        did_doc.validate(
            [
                '@context',
                'publicKey',
                'service'
            ]
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
