""" Module containing router implementations.
    A base router is provided to show the basic interface of routers.
"""

from typing import Callable
from python_agent_utils.messages.message import Message


class BaseRouter:
    """ Router Base Class. Provide basic interface for additional routers.
    """

    async def register(self, msg_type: str, handler: Callable[[bytes], None]) -> None:
        """ Register a callback for messages with a given type.
        """
        raise NotImplementedError("`register` not implemented in BaseRouter!")

    async def route(self, msg: Message) -> None:
        """ Route a message to it's registered callback
        """
        raise NotImplementedError("`route` not implemented in BaseRouter!")


class RouteAlreadyRegisteredException(Exception):
    """ Route Already Registered Exception.

        Raised by router.register
    """
    pass


class UnparsableMessageFamilyException(Exception):
    pass
