'use strict';
const fs = require('fs');
const uuid = require('uuid');
const homedir = require('home-dir');
const config = require('../../config');

const PATH = homedir('/.indy_client/' + config.walletName + '_store.json');
const BASE = JSON.stringify({
  pendingMessages: [],
  pendingRelationships: []
});

let store;

function init() {
  if (!store) {
    if (!fs.existsSync(PATH)) {
      fs.writeFileSync(PATH, BASE);
    }
    store = JSON.parse(fs.readFileSync(PATH));
  }
}

function syncChanges() {
  fs.writeFileSync(PATH, JSON.stringify(store));
}

exports.clear = function () {
  store.messages.clear();
  store.pendingRelationships.clear();
};

exports.messages = {
  getAll: function () {
    init();
    return store.pendingMessages;
  },
  write: function (did, message) {
    init();
    let id = uuid();
    store.pendingMessages.push({
      id: id,
      timestamp: new Date(),
      did: did,
      message: message
    });
    syncChanges();
    return id;
  },
  clear: function () {
    init();
    store.pendingMessages = [];
    syncChanges();
  },
  getMessage: function (id) {
    init();
    for (let message of store.pendingMessages) {
      if (message.id === id) {
        return message;
      }
    }
    return null;
  },
  deleteMessage: function (id) {
    for (let i = 0; i < store.pendingMessages.length; i++) {
      if (store.pendingMessages[i].id === id) {
        store.pendingMessages.splice(i, 1);
      }
    }
    syncChanges();
  }
};

exports.pendingRelationships = {
  getAll: function () {
    init();
    return store.pendingRelationships;
  },
  write: function (name, myNewDid, theirPublicDid, nonce) {
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
  delete: function (id) {
    init();
    for (let i = 0; i < store.pendingRelationships.length; i++) {
      if (store.pendingRelationships[i].id === id) {
        store.pendingRelationships.splice(i, 1);
        break;
      }
    }
    syncChanges();
  },
  clear: function () {
    init();
    store.pendingRelationships = [];
    syncChanges();
  }
};