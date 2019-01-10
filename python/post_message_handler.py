""" Message receiver handlers. """

# pylint: disable=import-error
from aiohttp import web
import asyncio

class PostMessageHandler():
    """ Simple message queue interface for receiving messages.
    """
    def __init__(self, queue):
        self.msg_queue = queue

    async def handle_message(self, request):
        """ Put to message queue and return 202 to client.
        """
        if not request.app['agent'].initialized:
            raise web.HTTPUnauthorized()

        msg = await request.read()
        await self.msg_queue.put(msg)
        raise web.HTTPAccepted()
