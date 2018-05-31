'use strict';
const sdk = require('indy-sdk');
const indy = require('../../index.js');
const config = require('../../../config');
let publicDid;
let stewardDid;
let stewardKey;
let stewardWallet;

exports.createDid = async function (didInfoParam) {
    let didInfo = didInfoParam || {};
    return await sdk.createAndStoreMyDid(await indy.wallet.get(), didInfo);
};

exports.getPublicDid = async function() {
    if(!publicDid) {
        let dids = await sdk.listMyDidsWithMeta(await indy.wallet.get());
        for (let didinfo of dids) {
            let meta = JSON.parse(didinfo.metadata);
            if (meta && meta.primary) {
                publicDid = didinfo.did;
            }
        }
        if(!publicDid) {
            await exports.createPublicDid();
        }
    }
    return publicDid;
};

exports.createPublicDid = async function () {
    await setupSteward();

    let verkey;
    [publicDid, verkey] = await sdk.createAndStoreMyDid(await indy.wallet.get(), {});
    let didMeta = JSON.stringify({
        primary: true,
        schemas: [],
        credential_definitions: []
    });
    await sdk.setDidMetadata(await indy.wallet.get(), publicDid, didMeta);

    await indy.pool.sendNym(await indy.pool.get(), stewardWallet, stewardDid, publicDid, verkey, "TRUST_ANCHOR");
    await indy.pool.setEndpointForDid(publicDid, config.publicDidEndpoint);
};

exports.setPublicDidAttribute = async function (attribute, item) {
    let metadata = await sdk.getDidMetadata(await indy.wallet.get(), publicDid);
    metadata = JSON.parse(metadata);
    metadata[attribute] = item;
    await sdk.setDidMetadata(await indy.wallet.get(), publicDid, JSON.stringify(metadata));
};


exports.pushPublicDidAttribute = async function (attribute, item) {
    let metadata = await sdk.getDidMetadata(await indy.wallet.get(), publicDid);
    metadata = JSON.parse(metadata);
    if (!metadata[attribute]) {
        metadata[attribute] = [];
    }
    metadata[attribute].push(item);
    await sdk.setDidMetadata(await indy.wallet.get(), publicDid, JSON.stringify(metadata));
};

exports.getPublicDidAttribute = async function (attribute) {
    let metadata = await sdk.getDidMetadata(await indy.wallet.get(), publicDid);
    metadata = JSON.parse(metadata);
    return metadata[attribute];
};

exports.getTheirPublicDid = async function (theirDid) {
    let pairwise = await sdk.getPairwise(await indy.wallet.get(), theirDid);
    let metadata = JSON.parse(pairwise.metadata);
    return metadata.theirPublicDid;
};

async function setupSteward() {
    let stewardWalletName = 'stewardWallet';
    try {
        await sdk.createWallet(config.poolName, stewardWalletName);
    } catch (e) {
        if (e.message !== "WalletAlreadyExistsError") {
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