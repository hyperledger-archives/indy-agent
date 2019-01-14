import aiohttp_jinja2
import jinja2
import json
from indy import did, wallet, non_secrets, pairwise

from router.simple_router import SimpleRouter
from agent import Agent
from message import Message
from . import Module

class Admin(Module):
    FAMILY_NAME = "admin"
    VERSION = "1.0"
    FAMILY = "did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/" + FAMILY_NAME + "/" + VERSION + "/"

    STATE = FAMILY + "state"
    STATE_REQUEST = FAMILY + "state_request"

    def __init__(self, agent):
        self.agent = agent
        self.router = SimpleRouter()
        self.router.register(self.STATE_REQUEST, self.state_request)

    async def route(self, msg: Message) -> Message:
        return await self.router.route(msg)

    async def state_request(self, _) -> Message:
        print("Processing state_request")

        invitations = []
        if self.agent.initialized:
            search_handle = await non_secrets.open_wallet_search(self.agent.wallet_handle, "invitations",
                                                                 json.dumps({}),
                                                                 json.dumps({'retrieveTotalCount': True}))
            results = await non_secrets.fetch_wallet_search_next_records(self.agent.wallet_handle, search_handle, 100)

            for r in json.loads(results)["records"] or []: # records is None if empty
                d = json.loads(r['value'])
                d["_id"] = r["id"] # include record id for further reference.
                invitations.append(d)
            #TODO: fetch in loop till all records are processed
            await non_secrets.close_wallet_search(search_handle)

            # load up pairwise connections
            pairwise_records = []
            agent_pairwises_list_str = await pairwise.list_pairwise(self.agent.wallet_handle)
            agent_pairwises_list = json.loads(agent_pairwises_list_str)
            for agent_pairwise_str in agent_pairwises_list:
                pairwise_record = json.loads(agent_pairwise_str)
                pairwise_record['metadata'] = json.loads(pairwise_record['metadata'])
                pairwise_records.append(pairwise_record)

            await self.agent.send_admin_message(
                Message({
                    '@type': self.STATE,
                    'content': {
                        'initialized': self.agent.initialized,
                        'agent_name': self.agent.owner,
                        'invitations': invitations,
                        'pairwise_connections': pairwise_records,
                    }
                })
            )
        else:
            await self.agent.send_admin_message(
                Message({
                    '@type': self.STATE,
                    'content': {
                        'initialized': self.agent.initialized,
                        }
                    })
            )


@aiohttp_jinja2.template('index.html')
async def root(request):
    print(request)
    agent = request.app['agent']
    agent.offer_endpoint = request.url.scheme + '://' + request.url.host
    print(agent.offer_endpoint)
    agent.endpoint = request.url.scheme + '://' + request.url.host
    if request.url.port is not None:
        agent.endpoint += ':' + str(request.url.port) + '/indy'
        agent.offer_endpoint += ':' + str(request.url.port) + '/offer'
    else:
        agent.endpoint += '/indy'
        agent.offer_endpoint += '/offer'
    return {'ui_token': agent.ui_token}
