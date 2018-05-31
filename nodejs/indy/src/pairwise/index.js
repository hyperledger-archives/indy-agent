'use strict';
const sdk = require('indy-sdk');
const indy = require('../../index.js');
const config = require('../../../config');

exports.getAll = async function () {
    let relationships = await sdk.listPairwise(await indy.wallet.get());
    for (let relationship of relationships) {
        relationship.metadata = JSON.parse(relationship.metadata);
    }
    return relationships;
};

exports.getMyDid = async function(theirDid) {
    let pairwise = await sdk.getPairwise(await indy.wallet.get(), theirDid);
    return pairwise.my_did;
};