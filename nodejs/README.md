# Run the node.js reference agent

## Migration Notice

**The work of creating interoperable Agents has moved to the Hyperledger Aries Project. This agent implementation is
currently unmaintained. The protocols used here are no longer up-to-date with the standards discussed in the Hyperledger
Aries Project.**

Refer to [the main README][2] for more information on the other components of the Indy Agent repository.

#### Superseding Project(s)
No codebase yet exists that directly supersedes the Node.js agent. However, discussion around creating a Node.js Agent
Framework are being held in the Aries Community. Direct questions about these efforts to the [Hyperledger Rocket.Chat
Aries channel][1].

#### Other questions?
Direct any other questions you may have about this repository to the [Aries channel][1].

[1]: https://chat.hyperledger.org/channel/aries
[2]: ../README.md


## Quick start Instructions

Run this repository by running through [`docker-compose`](https://docs.docker.com/compose/).

```
docker-compose build
docker-compose up
```

### Access the agents in a web browser:

To open an agent instance, in a web browser navigate to:
* `localhost:3000` for Government
* `localhost:3001` for Alice
* `localhost:3002` for Bob
* `localhost:3003` for Faber University
* `localhost:3004` for Acme Corporation
* `localhost:3005` for Thrift Bank 
