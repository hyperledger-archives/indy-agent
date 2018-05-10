'use strict';
const sdk = require('indy-sdk');
const uuid = require('uuid');
const utils = require('./utils');
const ledgerConfig = require('./ledgerConfig');
const common = require('./common');
const POOL_NAME = process.env.POOL_NAME || 'pool1';
const WALLET_NAME = process.env.WALLET_NAME || 'wallet';
let publicDid;
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
    let verkey;
    [publicDid, verkey] = await sdk.createAndStoreMyDid(wallet, {});
    await sdk.setEndpointForDid(wallet, publicDid, process.env.PUBLIC_DID_ENDPOINT, verkey);
    await common.sendNym(pool, wallet, publicDid, publicDid, verkey);
};

exports.getPublicDid = async function() {
    if(!publicDid) {
        await this.createAndStorePublicDid();
    }
    return publicDid;
};

exports.getEndpointForDid = async function (did) {
    let [endpoint] = await sdk.getEndpointForDid(wallet, pool, did);
    return endpoint;
};

