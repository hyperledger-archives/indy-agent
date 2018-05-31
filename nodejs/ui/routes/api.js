const express = require('express');
const router = express.Router();
const indy = require('../../indy/index');

router.get('/', function (req, res, next) {
    res.send("Success");
});

router.post('/send_message', async function (req, res) {
    let message = JSON.parse(req.body.message);
    message.did = req.body.did;

    await indy.crypto.sendAnonCryptedMessage(req.body.did, message);
    res.redirect('/#messages');
});

router.post('/send_connection_request', async function (req, res) {
    let name = req.body.name;
    let theirPublicDid = req.body.did;
    let connectionRequest = await indy.connections.prepareRequest(name, theirPublicDid);

    await indy.crypto.sendAnonCryptedMessage(theirPublicDid, connectionRequest);
    res.redirect('/#relationships');
});

router.post('/issuer/create_schema', async function (req, res) {
    await indy.issuer.createSchema(req.body.name_of_schema, req.body.version, req.body.attributes);
    res.redirect('/#issuing');
});

router.post('/issuer/create_cred_def', async function (req, res) {
    await indy.issuer.createCredDef(req.body.schema_id, req.body.tag);
    res.redirect('/#issuing');
});

router.post('/issuer/send_credential_offer', async function (req, res) {
    await indy.credentials.sendOffer(req.body.their_relationship_did, req.body.cred_def_id);
    res.redirect('/#issuing');
});

router.post('/credentials/accept_offer', async function(req, res) {
    let message = indy.store.messages.getMessage(req.body.messageId);
    indy.store.messages.deleteMessage(req.body.messageId);
    await indy.credentials.sendRequest(message.message.origin, message.message.message);
    res.redirect('/#messages');
});

router.post('/credentials/reject_offer', async function(req, res) {
    indy.store.messages.deleteMessage(req.body.messageId);
    res.redirect('/');
});

router.put('/connections/request', async function (req, res) {
    let name = req.body.name;
    let messageId = req.body.messageId;
    let message = indy.store.messages.getMessage(messageId);
    await indy.connections.acceptRequest(name, message.message.message.publicDid, message.message.message.did, message.message.message.nonce);
    indy.store.messages.deleteMessage(messageId);
    res.redirect('/#relationships');
});

router.delete('connections/request', async function (req, res) {
    // FIXME: Are we actually passing in the messageId yet?
    if (req.body.messageId) {
        indy.store.messages.deleteMessage(req.body.messageId);
    }
    res.redirect('/#relationships');
});

module.exports = router;
