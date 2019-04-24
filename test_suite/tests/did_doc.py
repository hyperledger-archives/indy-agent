from test_suite.tests import validate_message


class DIDDoc:
    DID = 'did'
    DID_DOC = 'did_doc'

    @staticmethod
    def validate(diddoc):
        validate_message(
            [
                '@context',
                'publicKey',
                'service'
            ],
            diddoc
        )

        for publicKeyBlock in diddoc['publicKey']:
            validate_message(
                [
                    'id',
                    'type',
                    'controller',
                    'publicKeyBase58'
                ],
                publicKeyBlock
            )

        for serviceBlock in diddoc['service']:
            validate_message(
                [
                    ('type', 'IndyAgent'),
                    'recipientKeys',
                    'serviceEndpoint'
                ],
                serviceBlock
            )
