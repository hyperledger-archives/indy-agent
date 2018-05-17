'use strict';
const store = require('../store');

// exports.connectionRequest = function(msg) {
//     msg.links = [];
//     msg.links.push({
//         name: "Accept",
//         request: {
//             uri: '/api/connection_request/accept',
//             method: 'POST'
//         }
//     });
//     msg.links.push({
//         name: "Reject",
//         request: {
//             uri: '/api/connection_request/reject',
//             method: 'POST'
//         }
//     });
//     store.messages.write(null, msg);
// };

exports.connectionResponse = function(msg) {
    // ...
    store.messages.write(null, msg);
};

exports.connectionAcknowledge = function(msg) {
    // ...

};