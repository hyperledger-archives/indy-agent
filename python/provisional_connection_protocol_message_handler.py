""" A message handler for the provisional connection protocol.
    Specifically, this handler will handle the connection offer.

    This is essentially identical to the post message handler and will be
    refactored out as soon as the new connection protocol is implemented.
"""

from aiohttp import web
import asyncio

class ProvisionalConnectionProtocolMessageHandler():
    def __init__(self, queue):
        self.msg_queue = queue

    async def handle_message(self, request):
        """ Put connection offer onto the mssage queue and return 202.
        """
        if not request.app['agent'].initialized:
            raise web.HTTPUnauthorized()

        msg = await request.read()
        await self.msg_queue.put(msg)
        raise web.HTTPAccepted()
