const express = require('express');
const router = express.Router();
const indy = require('../../indy/index');
const request = require('request-promise');

router.get('/', function(req, res, next) {
    res.send("Success");
});

router.post('/send_message', async function(req, res) {
    let message = JSON.parse(req.body.message);
    message.did = req.body.did;

    await indy.anonCryptMessage(req.body.did, message);
    res.redirect('/');
});

router.post('/send_connection_request', async function(req, res) {
    let name = req.body.name;
    let theirPublicDid = req.body.did;
    let connectionRequest = await indy.prepareConnectionRequest(name, theirPublicDid);

    await indy.anonCryptMessage(theirPublicDid, connectionRequest);
});

// router.post('/connection_request/accept')

module.exports = router;
