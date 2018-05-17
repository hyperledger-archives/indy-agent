'use strict';
const store = require('../store');
const handlers = require('./defaultHandlers');
const indy = require('../index.js');
const connections = require('../connections');

module.exports = function(config) { //factory function creates object and returns it.
    const factory = {};
    const messageHandlerMap = {};

    if(!config) {
        config = {};
    }

    factory.defineHandler = function(messageType, handler) {
        if(!messageType || typeof messageType !== 'string') {
            throw Error("Invalid message type: messageType must be a non-empty string");
        }
        if(!handler || typeof handler !== 'function') {
            throw Error("Invalid message handler: handler must be a function");
        }
        if(messageHandlerMap.hasOwnProperty(messageType)) {
            throw Error(`Duplicate message handler: handler already exists for message type ${messageType}`);
        }
        messageHandlerMap[messageType] = handler;
    };

    factory.middleware = async function(req, res) {
        try {
            let buffer = Buffer.from(req.body.message, 'base64');
            let decryptedMessage = await indy.publicKeyAnonDecrypt(buffer);
            if(messageHandlerMap[decryptedMessage.type]) {
                let handler = messageHandlerMap[decryptedMessage.type];
                if(handler.length === 2) { // number of parameters
                    handler(decryptedMessage, function(err) {
                        if(err) {
                            console.error(err.stack);
                            throw err;
                        } else {
                            res.status(202).send("Accepted");
                        }
                    })
                } else {
                    handler(decryptedMessage)
                        .then((data) => {
                            res.status(202).send("Accepted");
                        })
                        .catch((err) => {
                            console.error(err.stack);
                            throw err;
                        })
                }
            } else {
                store.messages.write(null, decryptedMessage);
                res.status(202).send("Accepted");
            }
        } catch(err) {
            console.error(err.stack);
            if(err.message === "Invalid Request") {
                res.status(400).send(e.message);
            } else {
                res.status(500).send("Internal Server Error");
            }
        }
    };

    if(config.defaultHandlers) {
        factory.defineHandler(connections.MESSAGE_TYPES.RESPONSE, handlers.connectionResponse);
        factory.defineHandler(connections.MESSAGE_TYPES.ACKNOWLEDGE, handlers.connectionAcknowledge);
    }

    return factory;
};