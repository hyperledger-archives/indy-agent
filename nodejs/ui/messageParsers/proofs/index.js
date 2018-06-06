'use strict';
const indy = require('../../../indy');

exports.request = async function(message) {
    let theirDid = message.message.origin;
    message.relationshipName = `${await indy.pairwise.getAttr(theirDid, 'first_name')} ${await indy.pairwise.getAttr(theirDid, 'last_name')}`;
    message.links = [
        {
            name: "Accept",
            href: "/api/proofs/accept",
            method: "POST",
            message: JSON.stringify({
                messageId: message.id
            })
        },
        {
            name: "Reject",
            href: "/api/messages/delete",
            method: "POST",
            message: JSON.stringify({
                messageId: message.id
            })
        }
    ];

    return Promise.resolve(message);
};