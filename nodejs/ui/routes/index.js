const express = require('express');
const router = express.Router();
const store = require('../../indy/store/index');
const indy = require('../../indy/index');
const messageParsers = require('../messageParsers');

/* GET home page. */
router.get('/', async function(req, res, next) {
    let rawMessages = store.messages.getAll();
    let messages = [];
    for(let message of rawMessages) {
        if(messageParsers[message.type]) {
            messages.push(await messageParsers[message.type](message));
        } else {
            throw Error(`messageParser not found for messages of type ${message.type}`);
        }
    }
    res.render('index', {
        messages: messages,
        relationships: await indy.getRelationships(),
        publicDid: await indy.getPublicDid()
    });
});

module.exports = router;

