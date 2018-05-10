'use strict';
const store = require('../messageStore');
const handlers = require('./handlers');
const indy = require('../index.js');

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
                store.writeMessage(null, decryptedMessage);
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
        factory.defineHandler("CONNECTION_REQUEST", handlers.connectionRequest);
        factory.defineHandler("CONNECTION_RESPONSE", handlers.connectionResponse);
    }

    return factory;
};

/*
module.exports = function(req, res) {
    try {
        let messageType = req.body.type;

        // Do something with the message if it shouldn't be stored. else
        store.writeMessage(req.body);
        res.status(202).send("Accepted");
    } catch(e) {
        if(e.message === "Invalid Request") {
            res.status(400).send(e.message);
        } else {
            res.send(500).send("Internal Server Error");
        }
    }

};
*/