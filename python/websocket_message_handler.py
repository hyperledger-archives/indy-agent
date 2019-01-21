import asyncio
import aiohttp
from aiohttp import web

class WebSocketMessageHandler(object):
    def __init__(self, inbound_queue, outbound_queue):
        self.recv_q = inbound_queue
        self.send_q = outbound_queue
        self.ws = None

    async def ws_handler(self, request):

        self.ws = web.WebSocketResponse()
        await self.ws.prepare(request)

        _, unfinished = await asyncio.wait(
            [
                self._websocket_receive(),
                self._websocket_send()
            ],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in unfinished:
            task.cancel()

        ws = self.ws
        self.ws = None
        return ws

    async def _websocket_receive(self):
        async for websocket_message in self.ws:
            if websocket_message.type == aiohttp.WSMsgType.TEXT:
                if websocket_message.data == 'close':
                    await self.ws.close()
                else:
                    print('Received "{}"'.format(websocket_message.data))
                    await self.recv_q.put(websocket_message.data)
            elif websocket_message.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      self.ws.exception())

        print('websocket connection closed')

    async def _websocket_send(self):
        while True:
            msg_to_send = await self.send_q.get()
            print('Sending "{}"'.format(msg_to_send))
            await self.ws.send_str(msg_to_send)
