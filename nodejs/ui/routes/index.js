const express = require('express');
const router = express.Router();
const store = require('../../indy/store/index');
const indy = require('../../indy/index');
const messageParsers = require('../messageParsers');
const connectionMessageTypes = require('../../indy/messageTypes').MESSAGE_TYPES;
const messageTypes = {connections: connectionMessageTypes};

/* GET home page. */
router.get('/', async function (req, res, next) {
    let rawMessages = store.messages.getAll();
    let messages = [];
    for (let message of rawMessages) {
        if (messageParsers[message.message.type]) {
            messages.push(await messageParsers[message.message.type](message));
        } else {
            messages.push(message);
        }
    }

    // Temporary until we have credentials to show

    let credentials = await indy.getCredentials();
    credentials.push({});

    let credDefs = await indy.getPublicDidAttribute('credential_definitions');
    res.render('index', {
        messages: messages,
        messageTypes: messageTypes,
        relationships: await indy.getRelationships(),
        credentials: credentials,
        schemas: await indy.getSchemas(),
        credentialDefinitions: credDefs,
        publicDid: await indy.getPublicDid()
    });
});

module.exports = router;
