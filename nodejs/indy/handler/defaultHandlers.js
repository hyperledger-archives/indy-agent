'use strict';
const store = require('../store');
const indy = require('../index.js');

exports.connectionResponse = function (message) {
    return indy.acceptConnectionResponse(message.aud, message.message);
};

exports.connectionAcknowledge = function (message) {
    return indy.acceptConnectionAcknowledgement(message.aud, message.message);
};

exports.credentialRequest = function (message) {
    return indy.acceptCredentialRequest(message.origin, message.message);
};

