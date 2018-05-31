'use strict';
const sdk = require('indy-sdk');
const indy = require('../../index.js');
const uuid = require('uuid');

const MESSAGE_TYPES = {
    OFFER : "urn:sovrin:agent:message_type:sovrin.org/connection_offer",
    REQUEST : "urn:sovrin:agent:message_type:sovrin.org/connection_request",
    RESPONSE : "urn:sovrin:agent:message_type:sovrin.org/connection_response",
    ACKNOWLEDGE : "urn:sovrin:agent:message_type:sovrin.org/connection_acknowledge"
};
exports.MESSAGE_TYPES = MESSAGE_TYPES;

exports.handlers = require('./handlers');

exports.prepareRequest = async function (nameOfRelationship, theirPublicDid) {
    let [myNewDid, myNewVerkey] = await sdk.createAndStoreMyDid(await indy.wallet.get(), {});
    await indy.pool.sendNym(await indy.pool.get(), await indy.wallet.get(), await indy.did.getPublicDid(), myNewDid, myNewVerkey);

    let nonce = uuid();
    indy.store.pendingRelationships.write(nameOfRelationship, myNewDid, theirPublicDid, nonce);

    return {
        type: MESSAGE_TYPES.REQUEST,
        message: {
            did: myNewDid,
            publicDid: await indy.did.getPublicDid(),
            nonce: nonce
        }
    }
};

exports.acceptRequest = async function (nameOfRelationship, theirPublicDid, theirDid, requestNonce) {
    let [myDid, myVerkey] = await sdk.createAndStoreMyDid(await indy.wallet.get(), {});

    let theirVerkey = await sdk.keyForDid(await indy.pool.get(), await indy.wallet.get(), theirDid);

    await sdk.storeTheirDid(await indy.wallet.get(), {
        did: theirDid,
        verkey: theirVerkey
    });

    let meta = JSON.stringify({
        name: nameOfRelationship,
        theirPublicDid: theirPublicDid
    });

    //FIXME: Check to see if pairwise exists
    await sdk.createPairwise(await indy.wallet.get(), theirDid, myDid, meta);

    // Send connections response
    let connectionResponse = {
        did: myDid,
        verkey: myVerkey,
        nonce: requestNonce
    };
    let message = {
        aud: theirDid,
        type: MESSAGE_TYPES.RESPONSE,
        message: await indy.crypto.anonCrypt(theirDid, JSON.stringify(connectionResponse))
    };
    await indy.crypto.sendAnonCryptedMessage(theirPublicDid, message);
};

exports.acceptResponse = async function (myDid, rawMessage) {
    let pendingRelationships = indy.store.pendingRelationships.getAll();
    let relationship;
    for (let entry of pendingRelationships) {
        if (entry.myNewDid === myDid) {
            relationship = entry;
        }
    }
    if (!relationship) {
        throw Error("RelationshipNotFound");
    } else {
        // base64 decode
        let base64DecodedMessage = Buffer.from(rawMessage, 'base64');
        // anon decrypt
        let message = await indy.crypto.anonDecrypt(myDid, base64DecodedMessage);
        // retrieve theirPublicDid, theirDid, connection_request_nonce
        let theirDid = message.did;
        let theirVerKey = message.verkey;

        if (relationship.nonce !== message.nonce) {
            throw Error("NoncesDontMatch");
        } else {
            await sdk.storeTheirDid(await indy.wallet.get(), {
                did: theirDid,
                verkey: theirVerKey
            });

            let meta = JSON.stringify({
                name: relationship.name,
                theirPublicDid: relationship.theirPublicDid
            });
            await sdk.createPairwise(await indy.wallet.get(), theirDid, relationship.myNewDid, meta);

            // send acknowledge
            await exports.sendAcknowledgement(relationship.myNewDid, theirDid, relationship.theirPublicDid);
            indy.store.pendingRelationships.delete(relationship.id);
        }
    }
};

exports.sendAcknowledgement = async function (myDid, theirDid, theirPublicDid) {
    let acknowledgementMessage = {
        aud: theirDid,
        type: MESSAGE_TYPES.ACKNOWLEDGE,
        message: await indy.crypto.authCrypt(myDid, theirDid, "Success")
    };

    await indy.crypto.sendAnonCryptedMessage(theirPublicDid, acknowledgementMessage);
};

exports.acceptAcknowledgement = async function (myDid, encryptedMessage) {
    let theirDid;
    let pairwiseList = await sdk.listPairwise(await indy.wallet.get());
    for (let pair of pairwiseList) {
        if (pair.my_did === myDid) {
            theirDid = pair.their_did;
        }
    }
    let message = await indy.crypto.authDecrypt(myDid, theirDid, encryptedMessage);
    // FIXME: Not finished. Validate message.
};