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
    poolName: process.env.POOL_NAME || 'pool1',

    // This information is used to issue your "Government ID"
    personalInformation: {
        first_name: process.env.FIRST_NAME || "Alice",
        middle_name: process.env.MIDDLE_NAME || "Rebecca",
        last_name: process.env.LAST_NAME || "Garcia",
        age: process.env.AGE || "38",
        gender: process.env.GENDER || "F",
        ssn: "123-45-6789"
    },

    loginInformation: {
        username: 'test',
        password: 'abc'
    },

    sessionSecret: "YUYFDISYFSIUOFYERTEWRTEWTWETRNNNMNJHKHFASDdyfiudayDAYIUSDFYASIOFOOASIUDFYEREAHLSKJFE57894502354354HJKAFDDFS"
};

module.exports = config;