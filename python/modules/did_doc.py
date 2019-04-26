from python.modules import Module


class DIDDoc(Module):
    DID = 'did'
    DID_DOC = 'did_doc'

    @staticmethod
    def validate(diddoc):
        Module.validate_message(
            [
                '@context',
                'publicKey',
                'service'
            ],
            diddoc
        )

        for publicKeyBlock in diddoc['publicKey']:
            Module.validate_message(
                [
                    'id',
                    'type',
                    'controller',
                    'publicKeyBase58'
                ],
                publicKeyBlock
            )

        for serviceBlock in diddoc['service']:
            Module.validate_message(
                [
                    ('type', 'IndyAgent'),
                    'recipientKeys',
                    'serviceEndpoint'
                ],
                serviceBlock
            )
