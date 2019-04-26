from typing import Iterable

from python.message import Message


class Module:
    PROBLEM_REPORT = 'problem_report'

    @staticmethod
    def validate_message(expected_attrs: Iterable, msg: Message):
        for attribute in expected_attrs:
            if isinstance(attribute, tuple):
                if attribute[0] not in msg:
                    raise KeyError('Attribute "{}" is missing from message: \n{}'.format(attribute[0], msg))
                if msg[attribute[0]] != attribute[1]:
                    raise KeyError('Message.{}: {} != {}'.format(attribute[0], msg[attribute[0]], attribute[1]))
            else:
                if attribute not in msg:
                    raise KeyError('Attribute "{}" is missing from message: \n{}'.format(attribute, msg))

    @staticmethod
    def build_problem_report_for_connections(family, problem_code, problem_str):
        return Message({
            "@type": "{}/problem_report".format(family),
            "problem-code": problem_code,
            "explain": problem_str
        })
