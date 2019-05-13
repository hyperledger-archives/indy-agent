""" Module defining the Message class that is used as base structure for all
    received messages.
"""
import json
from collections import UserDict
from typing import Iterable

import uuid

from python_agent_utils.messages.errors import ValidationException
from python_agent_utils.messages.fields import NonNegativeNumberField, MapField, DIDField, ISODatetimeStringField


class Message(UserDict):
    """ Data Model for messages.
    """
    ID = '@id'
    TYPE = '@type'

    THREAD_DECORATOR = '~thread'
    THREAD_ID = 'thid'
    PARENT_THREAD_ID = 'pthid'
    SENDER_ORDER = 'sender_order'
    RECEIVED_ORDERS = 'received_orders'
    THREADING_ERROR = 'threading_error'
    TIMING_ERROR = 'timing_error'

    TIMING_DECORATOR = '~timing'
    IN_TIME = 'in_time'
    OUT_TIME = 'out_time'
    STALE_TIME = 'stale_time'
    EXPIRES_TIME = 'expires_time'
    DELAY_MILLI = 'delay_milli'
    WAIT_UNTIL_TIME = 'wait_until_time'

    def __init__(self, *args, **kwargs):
        """ Create a Message object

        @type: string denoting the message type. Standardization efforts are in progress.
        @id: identifier for message. Usually a nonce or a DID. This combined with the type
            tell us how to interpret the message.
        other things: ambiguous data. Interpretation defined by type and id.

        """
        UserDict.__init__(self,*args, **kwargs)
        self.context = {}
        # Assign it an ID
        if '@id' not in self.data:
            self.data['@id'] = str(uuid.uuid4())

    def to_dict(self):
        return self.data

    @property
    def type(self):
        return self.data["@type"]

    @property
    def id(self):
        return self.data["@id"]

    class MessageEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Message):
                return obj.to_dict()
            return json.JSONEncoder.default(self, obj)

    def as_json(self):
        return json.dumps(self, cls=Message.MessageEncoder)

    def pretty_print(self):
        return json.dumps(self, sort_keys=True, indent=2, cls=Message.MessageEncoder)

    def check_for_attrs(self, expected_attrs: Iterable):
        Message.check_for_attrs_in_message(expected_attrs, self)

    @staticmethod
    def check_for_attrs_in_message(expected_attrs: Iterable, msg):
        for attribute in expected_attrs:
            if isinstance(attribute, tuple):
                if attribute[0] not in msg:
                    raise KeyError('Attribute "{}" is missing from message: \n{}'.format(attribute[0], msg))
                if msg[attribute[0]] != attribute[1]:
                    raise KeyError('Message.{}: {} != {}'.format(attribute[0], msg[attribute[0]], attribute[1]))
            else:
                if attribute not in msg:
                    raise KeyError('Attribute "{}" is missing from message: \n{}'.format(attribute, msg))

    def validate_common_blocks(self):
        """
        Validate blocks of message like threading, timing, etc
        :return:
        """
        try:
            self.validate_thread_block()
        except Exception as e:
            raise ValidationException(e, Message.THREADING_ERROR)

        try:
            self.validate_timing_block()
        except Exception as e:
            raise ValidationException(e, Message.TIMING_ERROR)

    # This should be validated for all messages
    def validate_thread_block(self):
        self._validate_thread_block(self)

    def validate_timing_block(self):
        self._validate_timing_block(self)

    @staticmethod
    def _validate_thread_block(msg):
        if Message.THREAD_DECORATOR in msg:
            thread = msg[Message.THREAD_DECORATOR]
            Message.check_for_attrs_in_message([
                Message.THREAD_ID,
                Message.SENDER_ORDER
            ], thread)

            thread_id = thread[Message.THREAD_ID]
            if msg.get(Message.ID) and thread_id == msg[Message.ID]:
                raise ValueError('Thread id {} cannot be equal to outer id {}'.format(thread_id, msg[Message.ID]))
            if thread.get(Message.PARENT_THREAD_ID) and thread[Message.PARENT_THREAD_ID] in (thread_id, msg[Message.ID]):
                raise ValueError('Parent thread id {} must be different than thread id and outer id'.format(thread[Message.PARENT_THREAD_ID]))

            # Creating objects has cost but since this codebase is meant to run only for test suite and possibly ref agent, its fine.
            non_neg_num = NonNegativeNumberField()
            err = non_neg_num.validate(thread[Message.SENDER_ORDER])
            if not err:
                if Message.RECEIVED_ORDERS in thread and thread[Message.RECEIVED_ORDERS]:
                    recv_ords = thread[Message.RECEIVED_ORDERS]
                    err = MapField(DIDField(), non_neg_num).validate(recv_ords)
            if err:
                raise ValueError(err)

    @staticmethod
    def _validate_timing_block(msg):
        if Message.TIMING_DECORATOR in msg:
            timing = msg[Message.TIMING_DECORATOR]
            non_neg_num = NonNegativeNumberField()
            iso_data = ISODatetimeStringField()
            expected_iso_fields = [Message.IN_TIME, Message.OUT_TIME, Message.STALE_TIME, Message.EXPIRES_TIME, Message.WAIT_UNTIL_TIME]
            for f in expected_iso_fields:
                if f in timing:
                    err = iso_data.validate(timing[f])
                    if err:
                        raise ValueError(err)
            if Message.DELAY_MILLI in timing:
                err = non_neg_num.validate(timing[Message.DELAY_MILLI])
                if err:
                    raise ValueError(err)

            # In time cannot be greater than out time
            if Message.IN_TIME in timing and Message.OUT_TIME in timing:
                t_in = iso_data.parse_func(timing[Message.IN_TIME])
                t_out = iso_data.parse_func(timing[Message.OUT_TIME])

                if t_in > t_out:
                    raise ValueError('{} cannot be greater than {}'.format(Message.IN_TIME, Message.OUT_TIME))

            # Stale time cannot be greater than expires time
            if Message.STALE_TIME in timing and Message.EXPIRES_TIME in timing:
                t_stale = iso_data.parse_func(timing[Message.STALE_TIME])
                t_exp = iso_data.parse_func(timing[Message.EXPIRES_TIME])

                if t_stale > t_exp:
                    raise ValueError('{} cannot be greater than {}'.format(Message.STALE_TIME, Message.EXPIRES_TIME))
