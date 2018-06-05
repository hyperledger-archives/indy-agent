'use strict';
const sdk = require('indy-sdk');
const indy = require('../../index.js');
const config = require('../../../config');
let publicDid;
let publicVerkey;
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

    [publicDid, publicVerkey] = await sdk.createAndStoreMyDid(await indy.wallet.get(), {});
    let didMeta = JSON.stringify({
        primary: true,
        schemas: [],
        credential_definitions: []
    });
    await sdk.setDidMetadata(await indy.wallet.get(), publicDid, didMeta);

    await indy.pool.sendNym(await indy.pool.get(), stewardWallet, stewardDid, publicDid, publicVerkey, "TRUST_ANCHOR");
    await indy.pool.setEndpointForDid(publicDid, config.publicDidEndpoint);
    await indy.crypto.createMasterSecret();

    await issueGovernmentIdCredential();
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
    let stewardWalletName = `stewardWalletFor:${config.walletName}`;
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

async function issueGovernmentIdCredential() {
    let schemaName = 'Government-ID';
    let schemaVersion = '1.0';
    let signatureType = 'CL';
    let [govIdSchemaId, govIdSchema] = await sdk.issuerCreateSchema(stewardDid, schemaName, schemaVersion, [
        'first_name',
        'middle_name',
        'last_name',
        'age',
        'gender',
        'ssn'
    ]);

    await indy.issuer.sendSchema(await indy.pool.get(), stewardWallet, stewardDid, govIdSchema);

    let [govIdCredDefId, govIdCredDef] = await sdk.issuerCreateAndStoreCredentialDef(stewardWallet, stewardDid, govIdSchema, 'GOVID', signatureType, '{"support_revocation": false}');

    await indy.issuer.sendCredDef(await indy.pool.get(), stewardWallet, stewardDid, govIdCredDef);

    let govIdCredOffer = await sdk.issuerCreateCredentialOffer(stewardWallet, govIdCredDefId);
    let [govIdCredRequest, govIdRequestMetadata] = await sdk.proverCreateCredentialReq(await indy.wallet.get(), publicDid, govIdCredOffer, govIdCredDef, await indy.did.getPublicDidAttribute('master_secret_id'));

    let govIdValues = {
        "first_name": {"raw": config.personalInformation.first_name, "encoded": "12345678987654321"},
        "middle_name": {"raw": config.personalInformation.middle_name, "encoded": "12345678987654321"},
        "last_name": {"raw": config.personalInformation.last_name, "encoded": "12345678987654321"},
        "age": {"raw": config.personalInformation.age, "encoded": "12345678987654321"},
        "gender": {"raw": config.personalInformation.gender, "encoded": "12345678987654321"},
        "ssn": {"raw": config.personalInformation.ssn, "encoded": "12345678987654321"}
    };

    let [govIdCredential] = await sdk.issuerCreateCredential(stewardWallet, govIdCredOffer, govIdCredRequest, govIdValues);
    await sdk.proverStoreCredential(await indy.wallet.get(), null, govIdRequestMetadata, govIdCredential, govIdCredDef);
}