Indy-agent implementation in Python
===================================

This is an implementation of indy-agent written in Python.

This agent seeks to be as simple as possible while accurately representing
the Sovrin protocol. See [Scope](scope.md) for goal and scope details.

Requirements
------------
- Python 3.6
- Latest `libindy` from https://github.com/hyperledger/indy-sdk

Quickstart
----------
There are two ways to run the agent (tested on Ubuntu 16.04).

Change your current folder to `indy-agent/python`

1. **Using Docker**
    * Make sure you have Docker installed.
    * Build docker image: `$ make build`
    * In one instance of your terminal: `$ make start PORT=8094` and don't close it.
    * In another instance of your terminal: `$ make start PORT=8095` and don't close it.

    At this moment we have two instances of agents running (on ports 8094 and 8095). In order to interact with them we have to know their assigned IP's.
    * Under Linux :
      * Do `$ sudo iptables -L` and find `Chain DOCKER` table. Info you need is stored at the `destination` column. (in my case I had 172.17.0.2 and 172.17.0.3)
    * Under MacOs :
      * Run `make getip PORT=8094` to get the ID address of the first container (in my case I had 172.17.0.2)
      * And run `make getip PORT=8095` to get the ID address of the second container (in my case I had 172.17.0.3)
  
    Now you can open your browser :
    * Open up your browser, with two tabs opened: 172.17.0.2:8094 (agent A) and 172.17.0.3:8095 (agent B).

2. **Using dev mode**

    * Make sure you have Python virtual environment installed and running.
    * Install requirements: `$ pip install -r requirements.txt`
    * In one instance of your terminal: `$ python indy-agent 8094` and don't close it.
    * In another instance of your terminal: `$ python indy-agent 8095` and don't close it.
    * Open up your browser, with two tabs opened: localhost:8094 (agent A) and localhost:8095 (agent B).

To this point I hope you have properly launched the agents. In each terminal, 
after browser tabs opened, you can see the "offer endpoint" usefull for
the following scenario (in my case `Agent Offer Endpoint : "http://172.17.0.3:8095/offer"`)

To do the DEMO (**using both 1 and 2 ways of running the agent**):
* In agent A browser tab type: `Alice` and any password.
* In agent B browser tab type: `Bob` and any password.
* In agent A browser tab click button send connection offer. Type `AliceToBobConnection` and `/offer` path of the second agent (in my case it was http://172.17.0.3:8095/offer), click `send connection offer`
* In agent B browser tab click on the `view` button and check the received message. Click `send request`
* In agent A browser tab click on the `view` button and check the received message. Click `send response`
* In agent B browser tab click on the `view` button and check the received message.

Alternatively, the python indy-agent accepts commandline arguments for the wallet name and wallet passphrase (e.g. `Alice` and `1234`). To do this after entering the port number in the command line arguments add in the wallet name and wallet passphrase `python indy-agent 8094 --wallet Alice 1234`.

During development, it is useful to use an ephemeral wallet that is created new each time. To do so, provide a name and a passphrase on the command line, and add the `--ephemeralwallet` argument. Example: `python indy-agent 8094 --wallet Alice 1234 --ephemeralwallet`. Note: ephemeral wallets will not overwrite normal wallets.