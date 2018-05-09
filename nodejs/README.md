# node.js implementation of the indy-agent
#### Note: The indy-agent is a work in progress and is not ready for use.

## Quick start guide
* `git clone https://github.com/hyperledger/indy-sdk.git` and follow [the instructions](https://github.com/hyperledger/indy-sdk/tree/master/doc) to build libindy for your system.
* Make sure the indy-sdk node module can access the built library by following [these instructions](https://www.npmjs.com/package/indy-sdk#installing).
* Make sure you have a running ledger by running these commands inside of the indy-sdk repository.

```
docker build -f ci/indy-pool.dockerfile -t indy_pool .
docker run -itd -p 9701-9708:9701-9708 indy_pool
```

* Then run the following commands to start the agent

```
git clone https:/github.com/hyperledger/indy-agent.git
cd indy-agent
npm install # This will fail if libindy is not accessible
npm start # Starts the node.js express server
```
* Then go to http://localhost:3000

## Basic Design Overview
The agent is a simple http server that can receive messages [POST](https://en.wikipedia.org/wiki/POST_(HTTP))ed to the /indy endpoint.  Those messages are stored for the user to make decisions on later through the UI. The UI is used to:

* Create new relationships
* Decide to accept new relationship requests
* Send and manage Credentials
* Make and request proofs

