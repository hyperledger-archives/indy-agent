import ipaddress
import json
from abc import ABCMeta, abstractmethod
from typing import Optional, Iterable

import base58
import dateutil.parser

from .errors import FieldTypeError, FieldValueError, error


class FieldValidator(metaclass=ABCMeta):
    """"
    Interface for field validators
    """

    optional = False

    @abstractmethod
    def validate(self, val):
        """
        Validates field value

        :param val: field value to check_for_attrs
        :return: error message or None
        """


class FieldBase(FieldValidator, metaclass=ABCMeta):
    """
    Base class for field validators
    """

    _base_types = ()

    def __init__(self, optional=False, nullable=False):
        self.optional = optional
        self.nullable = nullable

    # TODO: `check_for_attrs` should be renamed to `validation_error`
    def validate(self, val):
        """
        Performs basic validation of field value and then passes it for
        specific validation.

        :param val: field value to check_for_attrs
        :return: error message or None
        """

        if self.nullable and val is None:
            return
        type_er = self.__type_check(val)
        if type_er:
            return type_er

        spec_err = self._specific_validation(val)
        if spec_err:
            return spec_err

    @abstractmethod
    def _specific_validation(self, val):
        """
        Performs specific validation of field. Should be implemented in
        subclasses. Use it instead of overriding 'check_for_attrs'.

        :param val: field value to check_for_attrs
        :return: error message or None
        """

    def __type_check(self, val):
        if self._base_types is None:
            return  # type check is disabled
        for t in self._base_types:
            if isinstance(val, t):
                return
        return self._wrong_type_msg(val)

    def _wrong_type_msg(self, val):
        types_str = ', '.join(map(lambda x: x.__name__, self._base_types))
        return "expected types '{}', got '{}'" \
               "".format(types_str, type(val).__name__)


# TODO: The fields below should be singleton.


class AnyField(FieldBase):
    _base_types = (object,)

    def _specific_validation(self, _):
        return


class BooleanField(FieldBase):
    _base_types = (bool,)

    def _specific_validation(self, val):
        return


class IntegerField(FieldBase):
    _base_types = (int,)

    def _specific_validation(self, val):
        return


class NonEmptyStringField(FieldBase):
    _base_types = (str,)

    def _specific_validation(self, val):
        if not val:
            return 'empty string'


class LimitedLengthStringField(FieldBase):
    _base_types = (str,)

    def __init__(self, max_length: int, **kwargs):
        if not max_length > 0:
            raise FieldValueError('max_length', max_length, '> 0')
        super().__init__(**kwargs)
        self._max_length = max_length

    def _specific_validation(self, val):
        if not val:
            return 'empty string'
        if len(val) > self._max_length:
            val = val[:100] + ('...' if len(val) > 100 else '')
            return '{} is longer than {} symbols'.format(val, self._max_length)


class FixedLengthField(FieldBase):
    _base_types = (str, )

    def __init__(self, length: int, **kwargs):
        if not isinstance(length, int):
            error('length should be integer', TypeError)
        if length < 1:
            error('should be greater than 0', ValueError)
        self.length = length
        super().__init__(**kwargs)

    def _specific_validation(self, val):
        if len(val) != self.length:
            return '{} should have length {}'.format(val, self.length)


class SignatureField(LimitedLengthStringField):
    _base_types = (str, type(None))

    def _specific_validation(self, val):
        if val is None:
            # TODO do nothing because EmptySignature should be raised somehow
            return
        if len(val) == 0:
            return "signature can not be empty"
        return super()._specific_validation(val)


class RoleField(FieldBase):
    _base_types = (str, type(None))

    # TODO implement

    def _specific_validation(self, val):
        return


class NonNegativeNumberField(FieldBase):

    _base_types = (int, )

    def _specific_validation(self, val):
        if val < 0:
            return 'negative value'


class ConstantField(FieldBase):
    _base_types = None

    def __init__(self, value, **kwargs):
        super().__init__(**kwargs)
        self.value = value

    def _specific_validation(self, val):
        if val != self.value:
            return 'has to be equal {}'.format(self.value)


class IterableField(FieldBase):
    _base_types = (list, tuple)

    def __init__(self, inner_field_type: FieldValidator, min_length=None,
                 max_length=None, **kwargs):

        if not isinstance(inner_field_type, FieldValidator):
            raise FieldTypeError(
                'inner_field_type', inner_field_type, FieldValidator)

        for k in ('min_length', 'max_length'):
            m = locals()[k]
            if m is not None:
                if not isinstance(m, int):
                    raise FieldTypeError(k, m, int)
                if not m > 0:
                    raise FieldValueError(k, m, '> 0')

        self.inner_field_type = inner_field_type
        self.min_length = min_length
        self.max_length = max_length
        super().__init__(**kwargs)

    def _specific_validation(self, val):
        if self.min_length is not None:
            if len(val) < self.min_length:
                return 'length should be at least {}'.format(self.min_length)
        if self.max_length is not None:
            if len(val) > self.max_length:
                return 'length should be at most {}'.format(self.max_length)

        for v in val:
            check_er = self.inner_field_type.validate(v)
            if check_er:
                return check_er


class MapField(FieldBase):
    _base_types = (dict,)

    def __init__(self, key_field: FieldValidator,
                 value_field: FieldValidator,
                 **kwargs):
        super().__init__(**kwargs)
        self.key_field = key_field
        self.value_field = value_field

    def _specific_validation(self, val):
        for k, v in val.items():
            key_error = self.key_field.validate(k)
            if key_error:
                return key_error
            val_error = self.value_field.validate(v)
            if val_error:
                return val_error


class AnyMapField(FieldBase):
    # A map where key and value can be of arbitrary types
    _base_types = (dict,)

    def _specific_validation(self, _):
        return


class NetworkPortField(FieldBase):
    _base_types = (int,)

    def _specific_validation(self, val):
        if val <= 0 or val > 65535:
            return 'network port out of the range 0-65535'


class NetworkIpAddressField(FieldBase):
    _base_types = (str,)
    _non_valid_addresses = ('0.0.0.0', '0:0:0:0:0:0:0:0', '::')

    def _specific_validation(self, val):
        invalid_address = False
        try:
            ipaddress.ip_address(val)
        except ValueError:
            invalid_address = True
        if invalid_address or val in self._non_valid_addresses:
            return 'invalid network ip address ({})'.format(val)


class ChooseField(FieldBase):
    _base_types = None

    def __init__(self, values, **kwargs):
        self._possible_values = values
        super().__init__(**kwargs)

    def _specific_validation(self, val):
        if val not in self._possible_values:
            return "expected one of '{}', unknown value '{}'" \
                .format(', '.join(map(str, self._possible_values)), val)


class MessageField(FieldBase):
    _base_types = None

    def __init__(self, message_type, **kwargs):
        self._message_type = message_type
        super().__init__(**kwargs)

    def _specific_validation(self, val):
        if isinstance(val, self._message_type):
            return
        try:
            self._message_type(**val)
        except TypeError as ex:
            return "value {} cannot be represented as {} due to: {}" \
                .format(val, self._message_type.typename, ex)


class Base58Field(FieldBase):
    _base_types = (str,)
    _alphabet = set(base58.alphabet.decode("utf-8"))

    def __init__(self, byte_lengths: Optional[Iterable] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.byte_lengths = byte_lengths

    def _specific_validation(self, val):
        invalid_chars = set(val) - self._alphabet
        if invalid_chars:
            # only 10 chars to shorten the output
            # TODO: Why does it need to be sorted
            to_print = sorted(invalid_chars)[:10]
            return 'should not contain the following chars {}{}'.format(
                to_print, ' (truncated)' if len(to_print) < len(invalid_chars) else '')
        if self.byte_lengths is not None:
            # TODO could impact performance, need to check
            b58len = len(base58.b58decode(val))
            if b58len not in self.byte_lengths:
                return 'b58 decoded value length {} should be one of {}' \
                    .format(b58len, list(self.byte_lengths))


class FullVerkeyField(FieldBase):
    _base_types = (str,)
    _validator = Base58Field(byte_lengths=(32,))

    def _specific_validation(self, val):
        # full base58
        return self._validator.validate(val)


class AbbreviatedVerkeyField(FieldBase):
    _base_types = (str,)
    _validator = Base58Field(byte_lengths=(16,))

    def _specific_validation(self, val):
        if not val.startswith('~'):
            return 'should start with a ~'
        # abbreviated base58
        return self._validator.validate(val[1:])


# TODO: think about making it a subclass of Base58Field
class VerkeyField(FieldBase):
    _base_types = (str,)
    _b58abbreviated = AbbreviatedVerkeyField()
    _b58full = FullVerkeyField()

    def _specific_validation(self, val):
        err_ab = self._b58abbreviated.validate(val)
        err_fl = self._b58full.validate(val)
        if err_ab and err_fl:
            return 'Neither a full verkey nor an abbreviated one. One of ' \
                   'these errors should be resolved:\n {}\n{}'.\
                format(err_ab, err_fl)


class HexField(FieldBase):
    _base_types = (str,)

    def __init__(self, length=None, **kwargs):
        super().__init__(**kwargs)
        self._length = length

    def _specific_validation(self, val):
        try:
            int(val, 16)
        except ValueError:
            return "invalid hex number '{}'".format(val)
        if self._length is not None and len(val) != self._length:
            return "length should be {} length".format(self._length)


class MerkleRootField(Base58Field):
    _base_types = (str,)

    def __init__(self, *args, **kwargs):
        super().__init__(byte_lengths=(32,), *args, **kwargs)


class TimestampField(FieldBase):
    _base_types = (int,)
    _oldest_time = 1499906902

    def _specific_validation(self, val):
        if val < self._oldest_time:
            return 'should be greater than {} but was {}'. \
                format(self._oldest_time, val)


class ISODatetimeStringField(FieldBase):
    _base_types = (str,)
    parse_func = dateutil.parser.isoparse

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _specific_validation(self, val):
        try:
            self.parse_func(val)
        except Exception:
            return "{} is an invalid ISO".format(val)


class JsonField(LimitedLengthStringField):
    _base_types = (str,)

    def _specific_validation(self, val):
        # TODO: Need a mechanism to ensure a non-empty JSON if needed
        lim_str_err = super()._specific_validation(val)
        if lim_str_err:
            return lim_str_err
        try:
            json.loads(val)
        except json.decoder.JSONDecodeError:
            return 'should be a valid JSON string'


class SerializedValueField(FieldBase):
    _base_types = (bytes, str)

    def _specific_validation(self, val):
        if not val and not self.nullable:
            return 'empty serialized value'


class VersionField(LimitedLengthStringField):
    _base_types = (str,)

    def __init__(self, components_number=(3,), **kwargs):
        super().__init__(**kwargs)
        self._comp_num = components_number

    def _specific_validation(self, val):
        lim_str_err = super()._specific_validation(val)
        if lim_str_err:
            return lim_str_err
        parts = val.split(".")
        if len(parts) not in self._comp_num:
            return "version consists of {} components, but it should contain {}".format(
                len(parts), self._comp_num)
        for p in parts:
            if not p.isdigit():
                return "version component should contain only digits"
        return None


class AnyValueField(FieldBase):
    """
    Stub field validator
    """
    _base_types = None

    def _specific_validation(self, val):
        pass


class StringifiedNonNegativeNumberField(NonNegativeNumberField):
    """
    This validator is needed because of json limitations: in some cases
    numbers being converted to strings.
    """
    # TODO: Probably this should be solved another way

    _base_types = (str, int)
    _num_validator = NonNegativeNumberField()

    def _specific_validation(self, val):
        try:
            return self._num_validator.validate(int(val))
        except ValueError:
            return "stringified int expected, but was '{}'" \
                .format(val)


class DIDField(FieldBase):
    # check_for_attrs the DID to be in a proper format like did:<sov/peer>:<the did>

    _base_types = (str,)
    _valid_domains = ['sov', 'peer']

    def _specific_validation(self, val):
        did_parts = val.split(':')
        if len(did_parts) == 3 and did_parts[0] == 'did' and did_parts[1] in self._valid_domains:
            validator = Base58Field(byte_lengths=(16,))
            if not validator.validate(did_parts[2]):
                return None
        return 'Invalid DID {}'.format(val)
