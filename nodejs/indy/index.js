'use strict';
const sdk = require('indy-sdk');
const uuid = require('uuid');
const utils = require('./utils');
const ledgerConfig = require('./ledgerConfig');
const common = require('./common');
const POOL_NAME = process.env.POOL_NAME || 'pool1';
const WALLET_NAME = process.env.WALLET_NAME || 'wallet';
let publicDid;
let stewardDid;
let stewardKey;
let stewardWallet;
let wallet;
let pool;

exports.setupPool = async function() {
    let poolGenesisTxnPath = await ledgerConfig.getPoolGenesisTxnPath(POOL_NAME);
    let poolConfig = {
        "genesis_txn": poolGenesisTxnPath
    };
    try {
        await sdk.createPoolLedgerConfig(POOL_NAME, poolConfig);
    } catch(e) {
        if(e.message !== "PoolLedgerConfigAlreadyExistsError") {
            throw e;
        }
    } finally {
        pool = await sdk.openPoolLedger(POOL_NAME);
    }
};

exports.setupWallet = async function() {
    try {
        await sdk.createWallet(POOL_NAME, WALLET_NAME);
    } catch(e) {
        if(e.message !== "WalletAlreadyExistsError") {
            throw e;
        }
    } finally {
        wallet = await sdk.openWallet(WALLET_NAME);
    }
};

exports.createAndStoreMyDid = async function(didInfoParam) {
    let didInfo = didInfoParam || {};
    [this.did, this.key] = sdk.createAndStoreMyDid(this.wallet, didInfo);
    return [this.did, this.key];
};

// exports.connectWith = async function(host) {
//     let [myDid, myKey] = await this.createAndStoreMyDid();
//     await common.sendNym(this.pool, this.wallet, this.did, myDid, myKey, null);
//
//     let connectionRequest = {
//         did: myDid,
//         nonce: uuid()
//     };
//
//     utils.send('government', 'CONNECTION_REQUEST', connectionRequest);
// };

exports.publicKeyAnonDecrypt = async function(message) {
    return await this.anonDecrypt(publicDid, message);
};

exports.anonDecrypt = async function(did, message) {
    let verKey = await sdk.keyForLocalDid(wallet, did);
    let decryptedMessageBuffer = await sdk.cryptoAnonDecrypt(wallet, verKey, message);
    let buffer = Buffer.from(decryptedMessageBuffer).toString('utf8');
    return JSON.parse(buffer);
};

exports.anonCrypt = async function(did, message) {
    let verkey = await sdk.keyForDid(pool, wallet, did);
    return await sdk.cryptoAnonCrypt(verkey, Buffer.from(message, 'utf8'));
};

exports.createAndStorePublicDid = async function() {
    let endpoint = process.env.PUBLIC_DID_ENDPOINT;
    await setupSteward();

    let verkey;
    [publicDid, verkey] = await sdk.createAndStoreMyDid(wallet, {});

    await common.sendNym(pool, stewardWallet, stewardDid, publicDid, verkey, "TRUST_ANCHOR");

    let attributeRequest = await sdk.buildAttribRequest(publicDid, publicDid, null, {endpoint: {ha: endpoint}}, null);
    await sdk.signAndSubmitRequest(pool, wallet, publicDid, attributeRequest);
};

async function setupSteward() {
    let stewardWalletName = 'stewardWallet';
    try {
        await sdk.createWallet(POOL_NAME, stewardWalletName);
    } catch(e) {
        if(e.message !== "WalletAlreadyExistsError") {
            throw e;
        }
    } finally {
        stewardWallet = await sdk.openWallet(stewardWalletName);
    }

    let stewardDidInfo = {
        'seed': '000000000000000000000000Steward1'
    };

    [stewardDid, stewardKey] = await sdk.createAndStoreMyDid(stewardWallet, stewardDidInfo);

}

exports.getPublicDid = async function() {
    if(!publicDid) {
        await this.createAndStorePublicDid();
    }
    return publicDid;
};

exports.getEndpointForDid = async function (did) {
    let getAttrRequest = await sdk.buildGetAttribRequest(publicDid, did, 'endpoint', null, null);
    let res = await waitUntilApplied(pool, getAttrRequest, data => data['result']['data'] != null);
    return JSON.parse(res.result.data).endpoint.ha;
};

function sleep (ms) {
    return new Promise(function (resolve) {
        setTimeout(resolve, ms)
    })
}

async function waitUntilApplied (ph, req, cond) {
    for (let i = 0; i < 3; i++) {
        let res = await sdk.submitRequest(ph, req);

        if (cond(res)) {
            return res;
        }

        await sleep(5 * 1000);
    }
}
