'use strict';
const sdk = require('indy-sdk');
const indy = require('../../index.js');

exports.createSchema = async function (name, version, attributes) {
    let [id, schema] = await sdk.issuerCreateSchema(await indy.did.getPublicDid(), name, version, attributes);
    let schemaRequest = await sdk.buildSchemaRequest(await indy.did.getPublicDid(), schema);
    await sdk.signAndSubmitRequest(await indy.pool.get(), await indy.wallet.get(), await indy.did.getPublicDid(), schemaRequest);
    await indy.did.pushPublicDidAttribute('schemas', id);
};

exports.getSchemas = async function () {
    let metadata = JSON.parse(await sdk.getDidMetadata(await indy.wallet.get(), await indy.did.getPublicDid()));
    let schemas = [];
    for (let schemaId of metadata.schemas) {
        let schema = await indy.issuer.getSchema(schemaId);
        schemas.push(schema);
    }
    return schemas;
};

exports.createCredDef = async function (schemaId, tag) {
    let schema = await exports.getSchema(schemaId);
    let [credDefId, credDefJson] = await sdk.issuerCreateAndStoreCredentialDef(await indy.wallet.get(), await indy.did.getPublicDid(), schema, tag, 'CL', '{"support_revocation": false}');
    let credDefRequest = await sdk.buildCredDefRequest(await indy.did.getPublicDid(), credDefJson);
    await sdk.signAndSubmitRequest(await indy.pool.get(), await indy.wallet.get(), await indy.did.getPublicDid(), credDefRequest);
    await indy.did.pushPublicDidAttribute('credential_definitions', credDefJson);
};

exports.sendSchema = async function(poolHandle, walletHandle, Did, schema) {
    let schemaRequest = await sdk.buildSchemaRequest(Did, schema);
    await sdk.signAndSubmitRequest(poolHandle, walletHandle, Did, schemaRequest)
};

exports.sendCredDef = async function (poolHandle, walletHandle, did, credDef) {
    let credDefRequest = await sdk.buildCredDefRequest(did, credDef);
    await sdk.signAndSubmitRequest(poolHandle, walletHandle, did, credDefRequest);
};

exports.getSchema = async function(schemaId) {
    let getSchemaRequest = await sdk.buildGetSchemaRequest(await indy.did.getPublicDid(), schemaId);
    let getSchemaResponse = await sdk.submitRequest(await indy.pool.get(), getSchemaRequest);
    let [, schema] = await sdk.parseGetSchemaResponse(getSchemaResponse);
    return schema;
};

exports.getCredDef = async function(poolHandle, did, credDefId) {
    let getCredDefRequest = await sdk.buildGetCredDefRequest(did, credDefId);
    let getCredDefResponse = await sdk.submitRequest(poolHandle, getCredDefRequest);
    return await sdk.parseGetCredDefResponse(getCredDefResponse);
};

exports.getCredDefByTag = async function(credDefTag) {
    let credDefs = await indy.did.getPublicDidAttribute('credential_definitions');
    for(let credDef of credDefs) {
        if(credDef.tag === credDefTag) {
            return credDef;
        }
    }
};