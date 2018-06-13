import json
from aiohttp import web

async def ui_connect(_, agent):
    return {
            'type': 'AGENT_STATE',
            'did': None,
            'data': {
                'initialized': agent.initialized,
                'agent_name': agent.owner,
                'connections': [conn for _, conn in agent.connections.items()]
                }
            }

async def root(request):
    agent = request.app['agent']
    agent.endpoint = request.url.scheme + '://' + request.url.host
    if request.url.port is not None:
        agent.endpoint += ':' + str(request.url.port) + '/indy'
    else:
        agent.endpoint += '/indy'
    return web.FileResponse('view/res/index.bootstrap.html')
