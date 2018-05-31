const express = require('express');
const router = express.Router();
const indy = require('../../indy/index');
const messageParsers = require('../messageParsers');
const messageTypes = {
    connections: indy.connections.MESSAGE_TYPES,
    credentials: indy.credentials.MESSAGE_TYPES
};

/* GET home page. */
router.get('/', async function (req, res, next) {
    let rawMessages = indy.store.messages.getAll();
    let messages = [];
    for (let message of rawMessages) {
        if (messageParsers[message.message.type]) {
            messages.push(await messageParsers[message.message.type](message));
        } else {
            messages.push(message);
        }
    }

    let credentials = await indy.credentials.getAll();
    res.render('index', {
        messages: messages,
        messageTypes: messageTypes,
        relationships: await indy.pairwise.getAll(),
        credentials: credentials,
        schemas: await indy.issuer.getSchemas(),
        credentialDefinitions: await indy.did.getPublicDidAttribute('credential_definitions'),
        publicDid: await indy.did.getPublicDid()
    });
});

module.exports = router;
