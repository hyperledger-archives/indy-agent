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
    res.redirect('/#messages');
});

router.post('/send_connection_request', async function (req, res) {
    let name = req.body.name;
    let theirPublicDid = req.body.did;
    let connectionRequest = await indy.prepareConnectionRequest(name, theirPublicDid);

    await indy.sendAnonCryptedMessage(theirPublicDid, connectionRequest);
    res.redirect('/#relationships');
});

router.post('/issuer/create_schema', async function (req, res) {
    await indy.createSchema(req.body.name_of_schema, req.body.version, req.body.attributes);
    res.redirect('/#issuing');
});

router.post('/issuer/create_cred_def', async function (req, res) {
    await indy.createCredDef(req.body.schema_id, req.body.tag);
    res.redirect('/#issuing');
});

router.post('/issuer/send_credential_offer', async function (req, res) {
    await indy.sendCredentialOffer(req.body.their_relationship_did, req.body.cred_def_id);
    res.redirect('/#issuing');
});

router.post('/credentials/accept_offer', async function(req, res) {
    let message = indyStore.messages.getMessage(req.body.messageId);
    await indy.sendCredentialRequest(message.message.origin, message.message.message);
    indyStore.messages.deleteMessage(req.body.messageid);
    res.redirect('/#messages');
});

router.post('/credentials/reject_offer', async function(req, res) {
    // FIXME: Not yet implemented
    // await indy.rejectCredentialOffer();
    res.redirect('/');
});

router.put('/connections/request', async function (req, res) {
    let name = req.body.name;
    let messageId = req.body.messageId;
    let message = indyStore.messages.getMessage(messageId);
    await indy.acceptConnectionRequest(name, message.message.message.publicDid, message.message.message.did, message.message.message.nonce);
    indyStore.messages.deleteMessage(messageId);
    res.redirect('/#relationships');
});

router.delete('connections/request', async function (req, res) {
    // FIXME: Are we actually passing in the messageId yet?
    if (req.body.messageId) {
        indyStore.messages.deleteMessage(req.body.messageId);
    }
    res.redirect('/#relationships');
});

module.exports = router;
