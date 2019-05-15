from typing import Any


def error(msg: str, exc_type: Exception = Exception) -> Exception:
    """
    Wrapper to get around Python's distinction between statements and expressions
    Can be used in lambdas and expressions such as: a if b else error(c)

    :param msg: error message
    :param exc_type: type of exception to raise
    """
    raise exc_type(msg)


class BaseError(Exception):
    """Base exceptions class for exceptions"""

    @staticmethod
    def _prefix_msg(msg, prefix=None):
        return "{}{}".format(
            "" if prefix is None else "{}: ".format(prefix),
            msg
        )


class FieldTypeError(BaseError, TypeError):
    """Wrapper exception for TypeError

    Extends TypeError to provide formatted error message

    :param v_name: variable name
    :param v_value: variable value
    :param v_exp_t: expected variable type
    """
    def __init__(self, v_name: str, v_value: Any, v_exp_t: Any, *args,
                 prefix=None):
        super().__init__(
            self._prefix_msg(
                ("variable '{}', type {}, expected: {}"
                 .format(v_name, type(v_value), v_exp_t)),
                prefix),
            *args)


class FieldValueError(BaseError, ValueError):
    """Wrapper exception for ValueError

    Extends ValueError to provide formatted error message

    :param v_name: variable name
    :param v_value: variable value
    :param v_exp_value: expected variable value
    :param prefix: (optional) prefix for the message
    """
    def __init__(self, v_name: str, v_value: Any, v_exp_value: Any, *args,
                 prefix=None):
        super().__init__(
            self._prefix_msg(
                ("variable '{}', value {}, expected: {}"
                 .format(v_name, v_value, v_exp_value)),
                prefix),
            *args)


class ValidationException(Exception):
    def __init__(self, exception: Exception, error_code):
        self.exception = exception
        self.error_code = error_code
