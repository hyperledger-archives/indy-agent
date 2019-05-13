import re
import uuid

import pytest
import random

from test_suite.tests import expect_message, pack, unpack, check_problem_report

from python_agent_utils.messages.basicmessage import BasicMessage
from python_agent_utils.messages.message import Message

pytestmark = [
    pytest.mark.features('basicmessage.manual', 'core.manual')
]

EXPECT_MESSAGE_TIMEOUT = 60

@pytest.mark.asyncio
async def test_basic_message(config, wallet_handle, transport, connection):
    possible_random_messages = ['donut', 'cake', 'milk', 'cookies', 'cupcake', 'pie']
    random_message = possible_random_messages[random.randint(0, 5)]
    msg = BasicMessage.build("Reply with: {}".format(random_message))

    print("\nSending Message:\n", msg.pretty_print())
    await transport.send(
        connection['their_endpoint'],
        await pack(
            wallet_handle,
            connection['my_vk'],
            connection['their_vk'],
            msg
        )
    )

    print("Awaiting BasicMessage response from tested agent...")
    response_bytes = await expect_message(transport, EXPECT_MESSAGE_TIMEOUT)

    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=connection['my_vk']
    )

    BasicMessage.validate(response)
    print("\nReceived Message:\n", response.pretty_print())

    assert response['content'] == random_message, 'Did not respond with {}!'.format(random_message)


async def send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           expected_problem_code, error_msg_regex=None):
    print("\nSending Message:\n", msg.pretty_print())
    packed = await pack(
        wallet_handle,
        connection['my_vk'],
        connection['their_vk'],
        msg
    )
    await transport.send(
        connection['their_endpoint'],
        packed
    )

    print("Awaiting BasicMessage response from tested agent...")
    response_bytes = await expect_message(transport, EXPECT_MESSAGE_TIMEOUT)

    response = await unpack(
        wallet_handle,
        response_bytes,
        expected_to_vk=connection['my_vk']
    )
    check_problem_report(response, expected_problem_code=expected_problem_code, error_msg_regex=error_msg_regex)


@pytest.mark.asyncio
async def test_message_with_bad_threading_data(config, wallet_handle, transport, connection):
    msg = BasicMessage.build("Reply with: {}".format('1'))

    # Negative sender_order
    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: str(uuid.uuid4()),
        Message.SENDER_ORDER: -1
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR, re.compile('.*negative.*'))

    # thread_id same as message id
    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: msg.id,
        Message.SENDER_ORDER: 0
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR, re.compile('.*cannot be equal to outer id.*'))

    # Negative received_orders
    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: str(uuid.uuid4()),
        Message.SENDER_ORDER: 0,
        Message.RECEIVED_ORDERS: {
            'did:sov:BzCbsNYhMrjHiqZDTUASHg': -2
        }
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR, re.compile('.*negative.*'))

    # Invalid DID in received_orders
    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: str(uuid.uuid4()),
        Message.SENDER_ORDER: 0,
        Message.RECEIVED_ORDERS: {
            'sov:BzCbsNYhMrjHiqZDTUASHg': 1
        }
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR, re.compile('.*Invalid DID.*'))

    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: str(uuid.uuid4()),
        Message.SENDER_ORDER: 0,
        Message.RECEIVED_ORDERS: {
            'did:unknown:BzCbsNYhMrjHiqZDTUASHg': 1
        }
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR, re.compile('.*Invalid DID.*'))

    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: str(uuid.uuid4()),
        Message.SENDER_ORDER: 0,
        Message.RECEIVED_ORDERS: {
            'did:sov:BzCbs': 1
        }
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR, re.compile('.*Invalid DID.*'))

    # received_orders as a list and not a dict
    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: str(uuid.uuid4()),
        Message.SENDER_ORDER: 0,
        Message.RECEIVED_ORDERS: [2, 5]
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR, re.compile('.*expected type.*'))

    # Parent thread id same as thread id
    tid = str(uuid.uuid4())
    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: tid,
        Message.SENDER_ORDER: 0,
        Message.PARENT_THREAD_ID: tid
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR,
                                           re.compile('.*must be different than thread id and outer id.*'))

    # Parent thread id same as message id
    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: str(uuid.uuid4()),
        Message.SENDER_ORDER: 0,
        Message.PARENT_THREAD_ID: msg.id
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR,
                                           re.compile('.*must be different than thread id and outer id.*'))

    # thread id is missing
    msg[Message.THREAD_DECORATOR] = {
        Message.SENDER_ORDER: 0
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR,
                                           re.compile('.*is missing.*'))

    # sender_order is missing
    msg[Message.THREAD_DECORATOR] = {
        Message.THREAD_ID: str(uuid.uuid4()),
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.THREADING_ERROR,
                                           re.compile('.*is missing.*'))


@pytest.mark.asyncio
async def test_message_with_bad_timing_data(config, wallet_handle, transport, connection):
    msg = BasicMessage.build("Reply with: {}".format('1'))

    iso_fields = [Message.IN_TIME, Message.OUT_TIME, Message.STALE_TIME, Message.EXPIRES_TIME, Message.WAIT_UNTIL_TIME]
    for f in iso_fields:
        msg[Message.TIMING_DECORATOR] = {
            f: 'Wed May 01 2019 18:43:56 GMT+0530',
        }
        await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                               Message.TIMING_ERROR, re.compile('.*invalid ISO.*'))
        msg[Message.TIMING_DECORATOR] = {
            f: 1542340700,
        }
        await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                               Message.TIMING_ERROR, re.compile('.*expected types \'str\'.*'))

    msg[Message.TIMING_DECORATOR] = {
        Message.DELAY_MILLI: 'Wed May 01 2019 18:43:56 GMT+0530',
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.TIMING_ERROR)
    msg[Message.TIMING_DECORATOR] = {
        Message.DELAY_MILLI: '2019-01-25 18:25Z',
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.TIMING_ERROR)
    msg[Message.TIMING_DECORATOR] = {
        Message.DELAY_MILLI: -3,
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.TIMING_ERROR)

    # In time cannot be greater than out time
    msg[Message.TIMING_DECORATOR] = {
        Message.IN_TIME: '2019-01-25 18:25Z',
        Message.OUT_TIME: '2019-01-25 18:24Z',
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.TIMING_ERROR, re.compile('.*cannot be greater than.*'))

    # Stale time cannot be greater than expires time
    msg[Message.TIMING_DECORATOR] = {
        Message.STALE_TIME: '2019-01-25 18:25Z',
        Message.EXPIRES_TIME: '2019-01-25 18:24Z',
    }
    await send_bad_msg_and_check_for_error(wallet_handle, transport, connection, msg,
                                           Message.TIMING_ERROR, re.compile('.*cannot be greater than.*'))
