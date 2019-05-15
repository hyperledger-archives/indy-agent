from python_agent_utils.messages.errors import ValidationException
from python_agent_utils.messages.message import Message


class Module:
    PROBLEM_REPORT = 'problem_report'

    @staticmethod
    def build_problem_report_for_connections(family, problem_code, problem_str):
        return Message({
            "@type": "{}/problem_report".format(family),
            "problem-code": problem_code,
            "explain": problem_str
        })

    async def validate_common_message_blocks(self, msg, family):
        """
        Validate threading, timing blocks in messages and return error message to sender when invalid
        """
        try:
            msg.validate_common_blocks()
            return 1
        except ValidationException as e:
            their_did = msg.context.get('from_did')
            if their_did:
                err_msg = self.build_problem_report_for_connections(family,
                                                                    e.error_code, str(e.exception))
                await self.agent.send_message_to_agent(their_did, err_msg)
            print('Validation error while parsing message: {}', msg)
            return 0
        except Exception as g:
            print('Validation error while parsing message: {}', g)
            return 0
