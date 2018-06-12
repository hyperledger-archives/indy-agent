import json

async def ui_connect(msg, agent):
    return {
            'type': 'AGENT_STATE',
            'did': None,
            'data': {
                'agent_name': agent.owner,
                'connections': [conn for _, conn in agent.connections.items()]
                }
            }
