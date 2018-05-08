'use strict';
const indy = require('indy-sdk');
const uuid = require('uuid');
const utils = require('./utils');
const ledgerConfig = require('./ledgerConfig');
const common = require('./common');
const POOL_NAME = process.env.POOL_NAME || 'pool1';
const WALLET_NAME = process.env.WALLET_NAME || 'wallet';

exports.indy = indy;

exports.setupPool = async function() {
    let poolGenesisTxnPath = await ledgerConfig.getPoolGenesisTxnPath(POOL_NAME);
    let poolConfig = {
        "genesis_txn": poolGenesisTxnPath
    };
    try {
        await indy.createPoolLedgerConfig(POOL_NAME, poolConfig);
    } catch(e) {
        if(e.message !== "PoolLedgerConfigAlreadyExistsError") {
            throw e;
        }
    } finally {
        this.pool = await indy.openPoolLedger(POOL_NAME);
    }
};

exports.setupWallet = async function() {
    try {
        await indy.createWallet(POOL_NAME, WALLET_NAME);
    } catch(e) {
        if(e.message !== "WalletAlreadyExistsError") {
            throw e;
        }
    } finally {
        this.wallet = indy.openWallet(WALLET_NAME);
    }
};

exports.getWallet = function() {
    return this.wallet;
};

exports.createAndStoreMyDid = async function(didInfoParam) {
    let didInfo = didInfoParam || {};
    [this.did, this.key] = indy.createAndStoreMyDid(this.wallet, didInfo);
    return [this.did, this.key];
};

exports.connectWith = async function(host) {
    let [myDid, myKey] = await this.createAndStoreMyDid();
    await common.sendNym(this.pool, this.wallet, this.did, myDid, myKey, null);

    let connectionRequest = {
        did: myDid,
        nonce: uuid()
    };

    utils.send('government', 'CONNECTION_REQUEST', connectionRequest);

};
