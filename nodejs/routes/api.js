const express = require('express');
const router = express.Router();
const indy = require('../indy');
const request = require('request-promise');

router.get('/', function(req, res, next) {
    res.send("Success");
});

router.post('/send_message', async function(req, res, next) {
    let endpoint = await indy.getEndpointForDid(req.body.did);
    let encryptedMessage = await indy.anonCrypt(req.body.did, req.body.message);
    let requestOptions = {
        uri: endpoint,
        method: 'POST',
        body: {
            message: Buffer.from(encryptedMessage).toString('base64')
        },
        json: true
    };
    await request(requestOptions);
    res.redirect('/');
});

module.exports = router;
