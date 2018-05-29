'use strict';
const CONNECTION_MESSAGE_TYPES = require('../../indy/messageTypes').MESSAGE_TYPES;
const connectionMessageParsers = require('./connections');
const credentialMessageParsers = require('./credentials');

const messageParsers = {};
messageParsers[CONNECTION_MESSAGE_TYPES.REQUEST] = connectionMessageParsers.connectionsRequest;
messageParsers[CONNECTION_MESSAGE_TYPES.RESPONSE] = connectionMessageParsers.connectionsResponse;
messageParsers[CONNECTION_MESSAGE_TYPES.CREDENTIAL_OFFER] = credentialMessageParsers.credentialOffer;


module.exports = messageParsers;