'use strict';
const indy = require('../../indy');
const connectionMessageParsers = require('./connections');
const credentialMessageParsers = require('./credentials');

const messageParsers = {};
messageParsers[indy.connections.MESSAGE_TYPES.REQUEST] = connectionMessageParsers.connectionsRequest;
messageParsers[indy.connections.MESSAGE_TYPES.RESPONSE] = connectionMessageParsers.connectionsResponse;
messageParsers[indy.credentials.MESSAGE_TYPES.OFFER] = credentialMessageParsers.credentialOffer;


module.exports = messageParsers;