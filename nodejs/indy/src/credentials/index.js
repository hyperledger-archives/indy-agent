'use strict';
const sdk = require('indy-sdk');
const indy = require('../../index.js');

const MESSAGE_TYPES = {
    OFFER: "urn:sovrin:agent:message_type:sovrin.org/credential_offer",
    REQUEST: "urn:sovrin:agent:message_type:sovrin.org/credential_request",
    CREDENTIAL: "urn:sovrin:agent:message_type:sovrin.org/credential"
};
exports.MESSAGE_TYPES = MESSAGE_TYPES;

exports.handlers = require('./handlers');

exports.getAll = async function () {
    return await sdk.proverGetCredentials(await indy.wallet.get(), {});
};

exports.sendOffer = async function (theirDid, credentialDefinitionId) {
    let credOffer = await sdk.issuerCreateCredentialOffer(await indy.wallet.get(), credentialDefinitionId);
    await indy.store.pendingCredentialOffers.write(credOffer);
    let pairwise = await sdk.getPairwise(await indy.wallet.get(), theirDid);
    let myDid = pairwise.my_did;
    let message = await indy.crypto.buildAuthcryptedMessage(myDid, theirDid, MESSAGE_TYPES.OFFER, credOffer);
    let meta = JSON.parse(pairwise.metadata);
    let theirPublicDid = meta.theirPublicDid;
    return indy.crypto.sendAnonCryptedMessage(theirPublicDid, message);
};

exports.sendRequest = async function (theirDid, encryptedMessage) {
    let myDid = await indy.pairwise.getMyDid(theirDid);
    let credentialOffer = await indy.crypto.authDecrypt(myDid, encryptedMessage);
    let [, credentialDefinition] = await indy.issuer.getCredDef(await indy.pool.get(), myDid, credentialOffer.cred_def_id);
    let masterSecretId = await indy.did.getPublicDidAttribute('master_secret_id');
    let [credRequestJson, credRequestMetadataJson] = await sdk.proverCreateCredentialReq(await indy.wallet.get(), myDid, credentialOffer, credentialDefinition, masterSecretId);
    indy.store.pendingCredentialRequests.write(credRequestJson, credRequestMetadataJson);
    let message = await indy.crypto.buildAuthcryptedMessage(myDid, theirDid, MESSAGE_TYPES.REQUEST, credRequestJson);
    let theirPublicDid = await indy.did.getTheirPublicDid(theirDid);
    return indy.crypto.sendAnonCryptedMessage(theirPublicDid, message);
};

exports.acceptRequest = async function(theirDid, encryptedMessage) {
    let myDid = await indy.pairwise.getMyDid(theirDid);
    let credentialRequest = await indy.crypto.authDecrypt(myDid, encryptedMessage,);
    let [, credDef] = await indy.issuer.getCredDef(await indy.pool.get(), await indy.did.getPublicDid(), credentialRequest.cred_def_id);

    let credentialOffer;
    let pendingCredOfferId;
    let pendingCredOffers = indy.store.pendingCredentialOffers.getAll();
    for(let pendingCredOffer of pendingCredOffers) {
        if(pendingCredOffer.offer.cred_def_id === credDef.id) {
            pendingCredOfferId = pendingCredOffer.id;
            credentialOffer = pendingCredOffer.offer;
        }
    }
    let schema = await indy.issuer.getSchema(credentialOffer.schema_id);
    let credentialValues = {};
    for(let attr of schema.attrNames) {
        let value;
        switch(attr) {
            case "first_name":
                value = {"raw": await indy.pairwise.getAttr(theirDid, 'first_name') || "Alice", "encoded": "1139481716457488690172217916278103335"};
                break;
            case "last_name":
                value = {"raw": await indy.pairwise.getAttr(theirDid, 'last_name') || "Alice", "encoded": "5321642780241790123587902456789123452"};
                break;
            case "degree":
                value = {"raw": "Bachelor of Science, Marketing", "encoded": "12434523576212321"};
                break;
            case "status":
                value = {"raw": "graduated", "encoded": "2213454313412354"};
                break;
            case "ssn":
                value = {"raw": "123-45-6789", "encoded": "3124141231422543541"};
                break;
            case "year":
                value = {"raw": "2015", "encoded": "2015"};
                break;
            case "average":
                value = {"raw": "5", "encoded": "5"};
                break;
            default:
                value = {"raw": "someValue", "encoded": "someValue"};
        }
        credentialValues[attr] = value;
    }
    console.log(credentialValues);

    let [credential] = await sdk.issuerCreateCredential(await indy.wallet.get(), credentialOffer, credentialRequest, credentialValues);
    let message = await indy.crypto.buildAuthcryptedMessage(myDid, theirDid, MESSAGE_TYPES.CREDENTIAL, credential);
    let theirPublicDid = await indy.did.getTheirPublicDid(theirDid);
    await indy.crypto.sendAnonCryptedMessage(theirPublicDid, message);
    indy.store.pendingCredentialOffers.delete(pendingCredOfferId);
};

exports.acceptCredential = async function(theirDid, encryptedMessage) {
    let myDid = await indy.pairwise.getMyDid(theirDid);
    let credential = await await indy.crypto.authDecrypt(myDid, encryptedMessage);

    let credentialRequestMetadata;
    let pendingCredentialRequests = indy.store.pendingCredentialRequests.getAll();
    for(let pendingCredReq of pendingCredentialRequests) {
        if(pendingCredReq.credRequestJson.cred_def_id === credential.cred_def_id) { // FIXME: Check for match
            credentialRequestMetadata = pendingCredReq.credRequestMetadataJson;
        }
    }

    let [, credentialDefinition] = await indy.issuer.getCredDef(await indy.pool.get(), await indy.did.getPublicDid(), credential.cred_def_id);
    await sdk.proverStoreCredential(await indy.wallet.get(), null, credentialRequestMetadata, credential, credentialDefinition);
    let credentials = await indy.credentials.getAll();
    console.log(credentials);
};