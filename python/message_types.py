""" Message Type Definitions, organized by class
"""


class UI:
    BASE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/sovrin.org/ui/1.0/"

    STATE = BASE + "state"
    STATE_REQUEST = BASE + "state_request"
    INITIALIZE = BASE + "initialize"

    SEND_INVITE = BASE + "send_invite"
    INVITE_SENT = BASE + "invite_sent"
    INVITE_RECEIVED = BASE + "invite_received"

    REQUEST_RECEIVED = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/request"
    RESPONSE_RECEIVED = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/response"
    MESSAGE_RECEIVED = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/message"

    SEND_REQUEST = BASE + "send_request"
    REQUEST_SENT = BASE + "request_sent"

    SEND_RESPONSE = BASE + "send_response"
    RESPONSE_SENT = BASE + "response_sent"

    SEND_MESSAGE = BASE + "send_message"
    MESSAGE_SENT = BASE + "message_sent"


class CONN:
    BASE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/connections/1.0/"

    SEND_INVITE = BASE + "send_invite"
    SEND_REQUEST = BASE + "request"
    SEND_RESPONSE = BASE + "response"
    SEND_MESSAGE = BASE + "message"


class FORWARD:
    BASE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/routing/1.0/"

    FORWARD_TO_KEY = BASE + "forward_to_key"
    FORWARD = BASE + "forward"
