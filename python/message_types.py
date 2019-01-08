""" Message Type Definitions, organized by class
"""


class BASICMESSAGE:
    FAMILY = "basicmessage"
    VERSION = "1.0"
    BASE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY + "/" + VERSION + "/"

    MESSAGE = BASE + "message"

class ADMIN_BASICMESSAGE:
    FAMILY = "admin_basicmessage"
    VERSION = "1.0"
    BASE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY + "/" + VERSION + "/"

    MESSAGE_RECEIVED = BASE + "message_received"
    SEND_MESSAGE = BASE + "send_message"
    MESSAGE_SENT = BASE + "message_sent"
    GET_MESSAGES = BASE + "get_messages"
    MESSAGES = BASE + "messages"

class ADMIN_WALLETCONNECTION:
    FAMILY = "admin_walletconnection"
    VERSION = "1.0"
    BASE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY + "/" + VERSION + "/"

    CONNECT = BASE + "connect"
    DISCONNECT = BASE + "disconnect"
    USER_ERROR = BASE + "user_error"

class FORWARD:
    BASE = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/routing/1.0/"

    FORWARD_TO_KEY = BASE + "forward_to_key"
    FORWARD = BASE + "forward"
