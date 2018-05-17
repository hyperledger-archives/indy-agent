'use strict';
const fs = require('fs');
const uuid = require('uuid');
const homedir = require('home-dir');

const PATH = homedir('/.indy_client/store.json');
const BASE = JSON.stringify({
    pendingMessages: [],
    pendingRelationships: []
});

let store;

function init() {
    if(!store) {
        if(!fs.existsSync(PATH)) {
            fs.writeFileSync(PATH, BASE);
        }
        store = JSON.parse(fs.readFileSync(PATH));
    }
}

function syncChanges() {
    fs.writeFileSync(PATH, JSON.stringify(store));
}

exports.clear = function() {
    store.messages.clear();
    store.pendingRelationships.clear();
};

exports.messages = {
    getAll: function() {
        init();
        return store.pendingMessages;
    },
    write: function(did, message) {
        init();
        store.pendingMessages.push({
            id: uuid(),
            timestamp: new Date(),
            did: did,
            message: message
        });
        syncChanges();
    },
    clear: function() {
        init();
        store.pendingMessages = [];
        syncChanges();
    }
};

exports.pendingRelationships = {
    getAll: function() {
        init();
        return store.pendingRelationships;
    },
    write: function(name, myNewDid, theirPublicDid, nonce) {
        init();
        store.pendingRelationships.push({
            id: uuid(),
            timestamp: new Date(),
            name: name,
            myNewDid: myNewDid,
            theirPublicDid: theirPublicDid,
            nonce: nonce
        });
        syncChanges();
    },
    clear: function() {
        init();
        store.pendingRelationships = [];
        syncChanges();
    }
};

// exports.getOldestMessage = function() {
//     let messages = `.getMessages();
//     let oldestMessage = null;
//     for(let message of messages) {
//         if(oldestMessage === null) {
//             oldestMessage = message;
//         } else if(oldestMessage.timestamp > message.timestamp) {
//             oldestMessage = message;
//         }
//     }
//     return oldestMessage;
// };

// exports.getMessageById = function(id) {
//     let messages = this.getMessages();
//     for(let message of messages) {
//         if(message.id === id) {
//             return message;
//         }
//     }
//     return null;
// };

// exports.deleteMessage = function(id) {
//     let messages = this.getMessages();
//     for(let i = 0; i < messages.length; i++) {
//         if(messages[i].id === id) {
//             messages.splice(i, 1);
//         }
//     }
//     fs.writeFileSync(PATH, JSON.stringify(messages));
// };