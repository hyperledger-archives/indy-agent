'use strict';
const sdk = require('indy-sdk');
const uuid = require('uuid');
const request = require('request-promise');
const utils = require('./utils');
const ledgerConfig = require('./ledgerConfig');
const common = require('./common');
const store = require('./store');
const connections = require('./connections');
const POOL_NAME = process.env.POOL_NAME || 'pool1';
const WALLET_NAME = process.env.WALLET_NAME || 'wallet';
let publicDid;
let stewardDid;
let stewardKey;
let stewardWallet;
let wallet;
let pool;
let endpoint;

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
    let buffer = await sdk.cryptoAnonCrypt(verkey, Buffer.from(message, 'utf8'));
    return Buffer.from(buffer).toString('base64')
};

exports.createAndStorePublicDid = async function() {
    endpoint = process.env.PUBLIC_DID_ENDPOINT;
    await setupSteward();

    let verkey;
    [publicDid, verkey] = await sdk.createAndStoreMyDid(wallet, {});
    let didMeta = JSON.stringify({
        primary: true
    });
    await sdk.setDidMetadata(wallet, publicDid, didMeta);

    await common.sendNym(pool, stewardWallet, stewardDid, publicDid, verkey, "TRUST_ANCHOR");
    await this.setEndpointForDid(publicDid, endpoint);

};

exports.setEndpointForDid = async function(did, endpoint) {
    let attributeRequest = await sdk.buildAttribRequest(publicDid, did, null, {endpoint: {ha: endpoint}}, null);
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

exports.getRelationships = async function() {
    let relationships = await sdk.listPairwise(wallet);
    return relationships;
};

// FIXME: Assumption: Their public did has an endpoint attribute
exports.anonCryptMessage = async function(did, message) {
    message = JSON.stringify(message);
    let endpoint = await this.getEndpointForDid(did);
    let encryptedMessage = await this.anonCrypt(did, message);
    await this.sendMessage(endpoint, encryptedMessage);
};

exports.sendMessage = function(endpoint, message) {
    let requestOptions = {
        uri: `http://${endpoint}/indy`,
        method: 'POST',
        body: {
            message: message
        },
        json: true
    };
    return request(requestOptions);
};

exports.prepareConnectionRequest = async function(nameOfRelationship, theirPublicDid) {
    let [myNewDid, myNewVerkey] = await sdk.createAndStoreMyDid(wallet, {});
    await common.sendNym(pool, wallet, publicDid, myNewDid, myNewVerkey, null);

    let nonce = uuid();
    store.pendingRelationships.write(nameOfRelationship, myNewDid, theirPublicDid, nonce);

    return {
        type: connections.MESSAGE_TYPES.REQUEST,
        message: {
            did: myNewDid,
            publicDid: publicDid,
            nonce: nonce
        }
    }
};

exports.acceptConnectionRequest = async function(nameOfRelationship, theirPublicDid, theirDid, requestNonce) {
    //FIXME: Check to see if pairwise exists
    let [myDid, myVerkey] = await sdk.createAndStoreMyDid(wallet, {});

    let theirVerkey = await indy.keyForDid(pool, wallet, theirDid);

    await sdk.storeTheirDid(wallet, {
        did: theirDid,
        verkey: theirVerkey
    });

    let meta = JSON.stringify({
        name: nameOfRelationship,
        theirPublicDid: theirPublicDid
    });
    await sdk.createPairwise(wallet, theirDid, myDid, meta);

    // Send connection response
    let connectionResponse = {
        did: myDid,
        verkey: myVerkey,
        nonce: requestNonce
    };
    let message = {
        aud: theirDid,
        type: connections.MESSAGE_TYPES.RESPONSE,
        message: await this.anonCrypt(theirDid, connectionResponse)
    };
    await this.anonCryptMessage(theirPublicDid, connectionResponse);
};

exports.acceptConnectionResponse = async function(theirPublicDid, theirDid, theirVerkey, requestNonce) {
    let pendingRelationships = store.pendingRelationships.getAll();
    let relationship;
    for(let entry of pendingRelationships) {
        if(entry.theirPublicDid === theirPublicDid) {
            relationship = entry;
        }
    }
    if(!relationship) {
        throw Error("RelationshipNotFound");
    } else {
        if(relationship.nonce !== requestNonce) {
            throw Error("NoncesDontMatch");
        } else {
            await sdk.storeTheirDid(wallet, {
                did: theirDid,
                verkey: theirVerkey
            });

            let meta = JSON.stringify({
                name: relationship.name,
                theirPublicDid: theirPublicDid
            });
            await sdk.createPairwise(wallet, theirDid, relationship.myNewDid, meta);

            // send acknowledge
            this.sendAuthcryptedMessage(relationship.myNewDid, theirDid, "Success");
        }
    }
};

exports.authCrypt = async function(myDid, theirDid, message) {
    let myVerkey = await sdk.keyForLocalDid(wallet, myDid);
    let theirVerkey = await sdk.keyForLocalDid(wallet, theirDid);
    let buffer = await sdk.cryptoAuthCrypt(wallet, myDid, theirDid, Buffer.from(message, 'utf8'));
    return Buffer.from(buffer).toString('base64')
};

exports.sendAuthcryptedMessage = async function(myDid, theirDid, message) {

    //FIXME: Is their endpoint in the wallet yet?
    let endpoint = await sdk.getEndpointForDid(wallet, pool, theirDid);
    let authcryptedMessage = await this.authCrypt(myDid, theirDid, message);
    this.sendMessage(endpoint, authcryptedMessage);
};


