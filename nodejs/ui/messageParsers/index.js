'use strict';
const CONNECTION_MESSAGE_TYPES = require('../../indy/connections').MESSAGE_TYPES;
const connectionMessageParsers = require('./connections');

const messageParsers = {};
messageParsers[CONNECTION_MESSAGE_TYPES.REQUEST] = connectionMessageParsers.connectionsRequest;
messageParsers[CONNECTION_MESSAGE_TYPES.RESPONSE] = connectionMessageParsers.connectionsResponse;


module.exports = messageParsers;