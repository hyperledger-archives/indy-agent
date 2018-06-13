""" Handlers for web interface endpoints.
"""

# pylint: disable=import-error

import aiohttp_jinja2
from aiohttp import web
import aiohttp

def index(request):
    """ Handler for GET /

        Uses template index.html
    """
    raise web.HTTPFound('/index.bootstrap.html')

async def websocket_handler(request):

    ws = web.WebSocketResponse()
    await ws.prepare(request)
    request.app['agent'].ui_socket = ws
    print(request.app['agent'].ui_socket)

    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                await ws.send_str(msg.data + '/answer')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())
    
    request.app['agent'].ui_socket = None
    print('websocket connection closed')

    return ws

# Not sure if this is needed and it's causing problems
# with pylint. Commenting out for now.
#@aiohttp_jinja2.template('index.html')
#def request(request):
#    return {}


#@aiohttp_jinja2.template('index.html')
#def connections(request):
#    """ Return list of made connections.
#    """
#    pass

#@aiohttp_jinja2.template('index.html')
#def requests(request):
#    """ Return list of received requests.
#    """
#    print("handling requests")
#    reqs = request.app['agent'].received_requests
#    return {}


#@aiohttp_jinja2.template('index.html')
#def response(request):
#    print("handling response")
#    return {}
