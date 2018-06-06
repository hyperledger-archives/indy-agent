import json

async def edge_connect(msg, agent):
    return json.dumps({'type': 'AGENT_STATE', 'data': {'agent_name': agent.owner}})
