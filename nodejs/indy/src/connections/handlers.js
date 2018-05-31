'use strict';
const indy = require('../../index.js');

exports.response = function (message) {
    return indy.connections.acceptResponse(message.aud, message.message);
};

exports.acknowledge = function (message) {
    return indy.connections.acceptAcknowledgement(message.aud, message.message);
};