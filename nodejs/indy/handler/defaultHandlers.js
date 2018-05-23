'use strict';
const store = require('../store');
const indy = require('../index.js');

exports.connectionResponse = async function(message) {
  let id = store.messages.write(null, message);
  await indy.acceptConnectionResponse(message.aud, message.message);
  store.messages.deleteMessage(id);
  return Promise.resolve();
};

exports.connectionAcknowledge = async function(message) {
  let id = store.messages.write(null, message);
  await indy.acceptConnectionAcknowledgement(message.aud, message.message);
  store.messages.deleteMessage(id);
  return Promise.resolve();
};