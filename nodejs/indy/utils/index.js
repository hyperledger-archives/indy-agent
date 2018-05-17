'use strict';
const request = require('request-promise');

exports.send = function(host, type, message) {
    let port = process.env.PORT || '3000';
    return request({
        method: 'POST',
        uri: `http://${host}:${port}/`,
        headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: {
            type: type,
            message: message
        }
    });
};

exports.messageTypes =