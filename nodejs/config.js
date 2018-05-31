'use strict';

const config = {

    // Change to your public did's endpoint
    publicDidEndpoint: process.env.PUBLIC_DID_ENDPOINT,

    // IP Address of the running ledger
    testPoolIp: process.env.TEST_POOL_IP || '127.0.0.1',

    // the port to run the agent server on
    port: process.env.PORT || 3000,

    // Optional: Give your wallet a unique name
    walletName: process.env.WALLET_NAME || 'wallet',

    // Optional: Give your pool config a unique name
    poolName: process.env.POOL_NAME || 'pool1'
};

module.exports = config;