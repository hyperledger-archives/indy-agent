const express = require('express');
const router = express.Router();
const indy = require('../../indy/index');
const request = require('request-promise');
const indyStore = require('../../indy/store');

router.get('/', function (req, res, next) {
    res.send("Success");
});

router.post('/send_message', async function (req, res) {
    let message = JSON.parse(req.body.message);
    message.did = req.body.did;

    await indy.sendAnonCryptedMessage(req.body.did, message);
    res.redirect('/');
});

router.post('/send_connection_request', async function (req, res) {
    let name = req.body.name;
    let theirPublicDid = req.body.did;
    let connectionRequest = await indy.prepareConnectionRequest(name, theirPublicDid);

    await indy.sendAnonCryptedMessage(theirPublicDid, connectionRequest);
    res.redirect('/');
});

router.post('/issuer/create_schema', async function (req, res) {
    await indy.createSchema(req.body.name_of_schema, req.body.version, req.body.attributes);
    res.redirect('/');
});

router.post('/issuer/create_cred_def', async function (req, res) {
    await indy.createCredDef(req.body.schema_id, req.body.tag);
    res.redirect('/');
});

router.post('/issuer/send_credential_offer', async function (req, res) {
    await indy.sendCredentialOffer(req.body.their_relationship_did, req.body.cred_def_id);
});

router.put('/connections/request', async function (req, res) {
    let name = req.body.name;
    let messageId = req.body.messageId;
    let message = indyStore.messages.getMessage(messageId);
    await indy.acceptConnectionRequest(name, message.message.message.publicDid, message.message.message.did, message.message.message.nonce);
    indyStore.messages.deleteMessage(messageId);
    res.sendStatus(204);
});

router.delete('connections/request', async function (req, res) {
    if (req.body.messageId) {
        indyStore.messages.deleteMessage(req.body.messageId);
    }
    res.sendStatus(204);
});

module.exports = router;
