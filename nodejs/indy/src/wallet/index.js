'use strict';
const sdk = require('indy-sdk');
const indy = require('../../index.js');
const config = require('../../../config');
let wallet;

exports.get = async function() {
    if(!wallet) {
        await exports.setup();
    }
    return wallet;
};

exports.setup = async function () {
    try {
        await sdk.createWallet(config.poolName, config.walletName);
    } catch (e) {
        if (e.message !== "WalletAlreadyExistsError") {
            throw e;
        }
    } finally {
        wallet = await sdk.openWallet(config.walletName);
    }
};

