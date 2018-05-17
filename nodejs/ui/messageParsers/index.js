'use strict';
const CONNECTION_MESSAGE_TYPES = require('../../indy/connections').MESSAGE_TYPES;
const connectionMessageParsers = require('./connections');

const messageParsers = {};
messageParsers[CONNECTION_MESSAGE_TYPES.REQUEST] = connectionMessageParsers.connectionRequest;
messageParsers[CONNECTION_MESSAGE_TYPES.RESPONSE] = connectionMessageParsers.connectionResponse;


module.exports = messageParsers;