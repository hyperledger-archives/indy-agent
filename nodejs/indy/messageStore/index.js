'use strict';
const fs = require('fs');
const uuid = require('uuid');
const homedir = require('home-dir');
const PATH = homedir('/.indy_client/messageStore.json');

/*
    This works for now, but these messages need to be encrypted at rest.
    Message Structure: {
        id:
        timestamp:
        message:
    }
 */

exports.getOldestMessage = function() {
    let messages = this.getMessages();
    let oldestMessage = null;
    for(let message of messages) {
        if(oldestMessage === null) {
            oldestMessage = message;
        } else if(oldestMessage.timestamp > message.timestamp) {
            oldestMessage = message;
        }
    }
    return oldestMessage;
};

exports.getMessageById = function(id) {
    let messages = this.getMessages();
    for(let message of messages) {
        if(message.id === id) {
            return message;
        }
    }
    return null;
};

exports.deleteMessage = function(id) {
    let messages = this.getMessages();
    for(let i = 0; i < messages.length; i++) {
        if(messages[i].id === id) {
            messages.splice(i, 1);
        }
    }
    fs.writeFileSync(PATH, JSON.stringify(messages));
};

exports.getMessages = function() {
    if(!this.store) {
        if(!fs.existsSync(PATH)) {
            fs.writeFileSync(PATH, JSON.stringify([]));
        }
        this.store = JSON.parse(fs.readFileSync(PATH));
    }
    return this.store;
};

exports.writeMessage = function(did, message) {
    let messages = this.getMessages();
    messages.push({
        id: uuid(),
        did: did,
        timestamp: new Date(),
        message: message
    });
    fs.writeFileSync(PATH, JSON.stringify(messages));
};

exports.clear = function() {
    this.store = null;
    try {
        fs.unlinkSync(PATH);
    } catch(e) {
        if(e.code !== 'ENOENT') {
            throw e;
        }
    }
};