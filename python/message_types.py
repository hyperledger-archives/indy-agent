""" Message Type Definitions, organized by class
"""


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
