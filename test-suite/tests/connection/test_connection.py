import asyncio
import pytest
import re
import base64
from message import Message
from serializer import JSONSerializer as Serializer
from tests import expect_message, validate_message
from indy import did

@pytest.mark.asyncio
async def test_connection_started_by_tested_agent(config, transport):
    invite_url = input('Input generated connection invite: ')

    matches = re.match('(.+)?c_i=(.+)', invite_url)
    assert matches, 'Improperly formatted invite url!'

    invite_msg = Serializer.unpack(
        base64.urlsafe_b64decode(matches.group(2)).decode('utf-8')
    )

    validate_message(
        [
            '@type',
            'label',
            'key',
            'endpoint'
        ],
        invite_msg
    )
