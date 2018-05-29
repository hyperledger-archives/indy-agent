'use strict';

exports.credentialOffer = function (message) {
    message.links = [
        {
            name: "Accept",
            href: "/api/credentials/accept_offer",
            method: "POST",
            message: JSON.stringify({
                messageId: message.id
            })
        },
        {
            name: "Reject",
            href: "/api/credentials/reject_offer",
            method: "POST",
            message: JSON.stringify({
                messageId: message.id
            })
        }
    ];

    return Promise.resolve(message);
};