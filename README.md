# Indy Agents

Agents come in all varieties. Some are simple and static; these
might be appropriate for IoT use cases that are hard-wired for
a single connection. Others are complex and cloud-based, suitable
for enterprise use. Still others run on mobile devices for
individual users. For more information about general agent theory
or about agent categories, see the [Agents Explainer HIPE](
https://github.com/hyperledger/indy-hipe/blob/4696f162/text/0002-agents/README.md).

This repo contains a handful of reference agents. To run them,
you must have a build of libindy plus a running ledger.  If you
are just trying them out, we recommend [running a ledger locally
using docker](https://github.com/hyperledger/indy-sdk/blob/master/docs/build-guides/ubuntu-build.md).
See the README in each implementation directory for more
details.

The repo also has some useful tools for agent developers--especially
a test suite that can exercise agent interoperability.

## Known Agent Implementations

The following agents are known to the general community. If you
would like to list your agent here, please submit a pull request.

|Name|Source|Use Cases|Interop Results from Test Suite|More Info|
|----|------|---------|-------------------------------|---------|
|python ref agent|community / Sovrin Foundation (see github contributors)|cloud (web-based)|not yet published on the web, but 100% passed in Feb 2019|see [python/README.md](python/README.md) in this repo|
|node.js ref agent|community / BYU (see github contributors)|cloud (web-based)|not yet tested|see [nodejs/README.md](nodejs/README.md) in this repo|
|Sovrin Connector|Sovrin Foundation|mobile app (assumes cloud support)|not yet tested|[github.com/ sovrin-foundation/ connector-app](https://github.com/sovrin-foundation/connector-app)|
|IndyCat|Government of British Columbia|Cloud for institutions (besides agent, includes drive to enable injection of business rules in messaging protocols)|100% passed in Feb 2019|[https://github.com/bcgov/indy-catalyst/](https://github.com/bcgov/indy-catalyst/tree/master/agent)|
|StreetCred|StreetCred|commercial mobile app + .NET framework for agents of all types|not yet published on the web, but X% passed in Feb 2019|[github.com/ streetcred-id/ agent-framework](https://github.com/streetcred-id/agent-framework)|
|Verity|Evernym|commercial enterprise agent, focused on credential issuance and proving for login and onboarding|not yet tested|[evernym.com](https://evernym.com)|
|Connect.Me|Evernym|commercial mobile agent for individuals (free but requires SaaS subscription for supporting cloud agent)|not yet tested|Android or iOS App Store|

## Related Topics

If you are interested in developing indy-sdk,
please visit the [indy-sdk repository](https://github.com/hyperledger/indy-sdk/)
and follow the Getting Started Guide there.


