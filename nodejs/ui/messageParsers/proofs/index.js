'use strict';
const indy = require('../../../indy');

exports.request = async function(message) {
    let theirDid = message.message.origin;
    let firstName = await indy.pairwise.getAttr(theirDid, 'first_name');
    let lastName = await indy.pairwise.getAttr(theirDid, 'last_name');
    let publicDid = await indy.did.getTheirPublicDid(theirDid);
    if(firstName && lastName) {
        message.relationshipName = `${firstName} ${lastName}`;
    } else if (publicDid) {
        message.relationshipName = `Public DID: ${publicDid}`
    }
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