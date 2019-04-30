# Desirable Tests

### General
* Messages with a minor version > current, but major version == current, are handled.
* Messages with a major version > current generate a graceful error.
* Problem reports contain useful fields and correct codes.
* Problem reports use localization correctly enough that machine translation could be applied.

### Decorators
* The ~thread decorator is handled correctly (including thid and received_order)
* The ~timing decorator is handled correctly.
* The ~please_ack decorator is handled correctly.

### Connection Protocol
* Agent can be either inviter or invitee.
* A public DID can be used as an implicit invitation.
* A connection resp that is not signed by the key used in the invitation generates a graceful error.
* A connection resp sent before a connection req generates a graceful error.
* A connection resp or connection req that uses a different thread from the previous message generates a graceful error.
* A connection resp or req that uses the same thread as previous, but an inconsistent state (e.g., different DID Doc or endpoint) is rejected.
* DID Docs with extra fields are handled.
* DID Docs lacking required fields are rejected.
* DID Docs lacking public keys of type Ed25519 are either handled fully, or generate a graceful error.
* A plaintext version of a connection request or connection response is gracefully rejected.

### Trust Ping Protocol
* Agents can be pingee.
* A trust ping that asks for no response elicits no response.
* A trust ping that asks for a delayed response elicits a delayed response.

### Protocol Discovery Protocol
* Agent can be a responder.
* Agent returns supported roles, not just supported protocols.
* Agent returns empty list when asked about nonexistent protocol.
* Agent returns one item when asked about the protocol discovery protocol itself.
* Agent supports wildcards.

