import asyncio
import aiohttp
from aiohttp import web


class WebSocketMessageHandler:
    def __init__(self, inbound_queue, outbound_queue):
        self.recv_q = inbound_queue
        self.send_q = outbound_queue
        self.ws = None

    async def ws_handler(self, request):

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        if self.ws is not None:
            await self.ws.close()

        self.ws = ws

        _, unfinished = await asyncio.wait(
            [
                self._websocket_receive(ws),
                self._websocket_send(ws)
            ],
            return_when=asyncio.FIRST_COMPLETED
        )
        for task in unfinished:
            task.cancel()

        return ws

    async def _websocket_receive(self, ws):
        async for websocket_message in ws:
            if websocket_message.type == aiohttp.WSMsgType.TEXT:
                if websocket_message.data == 'close':
                    await ws.close()
                else:
                    print('Received "{}"'.format(websocket_message.data))
                    await self.recv_q.put(websocket_message.data)
            elif websocket_message.type == aiohttp.WSMsgType.ERROR:
                print('ws connection closed with exception %s' %
                      ws.exception())

        print('websocket connection closed')

    async def _websocket_send(self, ws):
        while True:
            msg_to_send = await self.send_q.get()
            if ws.closed:
                # avoid sending to closed socket and route the message to concurrent instance
                await self.send_q.put(msg_to_send)
                break
            print('Sending "{}"'.format(msg_to_send))
            await ws.send_str(msg_to_send)
