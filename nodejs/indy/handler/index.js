'use strict';
const store = require('../messageStore');

module.exports = function(req, res) {
    try {
        let messageType = req.body.type;

        // Do something with the message if it shouldn't be stored. else
        store.writeMessage(req.body);
        res.status(202).send("Accepted");
    } catch(e) {
        if(e.message === "Invalid Request") {
            res.status(400).send(e.message);
        } else {
            res.send(500).send("Internal Server Error");
        }
    }

};