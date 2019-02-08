const path = require('path');
const uuid = require('uuid');
const express = require('express');
const prettyStringify = require('json-stringify-pretty-compact');
const router = express.Router();
const indy = require('../../indy/index');
const config = require('../../config');
const messageParsers = require('../messageParsers');
const auth = require('../authentication');
const messageTypes = {
    connections: indy.connections.MESSAGE_TYPES,
    credentials: indy.credentials.MESSAGE_TYPES,
    proofs: indy.proofs.MESSAGE_TYPES
};

/* GET home page. */
router.get('/', auth.isLoggedIn, async function (req, res) {
    // res.sendFile(path.join(__dirname + '/../views/index.html'));
    let rawMessages = indy.store.messages.getAll();
    let messages = [];
    for (let message of rawMessages) {
        if (messageParsers[message.message.type]) {
            messages.push(await messageParsers[message.message.type](message));
        } else {
            messages.push(message);
        }
    }

    let proofRequests = await indy.proofs.getProofRequests();
    for(let prKey of Object.keys(proofRequests)) {
        proofRequests[prKey].string = prettyStringify(proofRequests[prKey]);
    }

    let credentials = await indy.credentials.getAll();
    let relationships = await indy.pairwise.getAll();

    res.render('index', {
        messages: messages,
        messageTypes: messageTypes,
        relationships: relationships,
        credentials: credentials,
        schemas: await indy.issuer.getSchemas(),
        credentialDefinitions: await getEnrichedCredentialDefinitions(),
        endpointDid: await indy.did.getEndpointDid(),
        proofRequests: proofRequests,
        name: config.userInformation.name
    });

    for(let prKey of Object.keys(proofRequests)) {
        delete proofRequests[prKey].string;
    }
});

async function getEnrichedCredentialDefinitions() {
  try {
    let credDefs = await indy.did.getEndpointDidAttribute('credential_definitions');
    for (let credDef of credDefs) {
      // Create generic credential data for credential from credential definition
      let credentialData = {};
      let schema = await indy.issuer.getSchema(credDef.schemaId_long);
      // Iterate over attributes defined in credential definition and set to empty data
      for (let attr of schema.attrNames) {
          credentialData[attr] = "";
      }
      credDef.credentialData = credentialData;
    }
    return credDefs;
  } catch (e) {
    console.log(e);
  }
}

router.get('/login', function(req, res) {
   res.render('login', {
       name: config.userInformation.name
   });
});

router.post('/login', async function(req, res) {
    if(req.body.username === config.userInformation.username &&
    req.body.password === config.userInformation.password) {
        let token = uuid();
        req.session.token = token;
        req.session.save((err) => {
            auth.validTokens.push(token);
            res.redirect('/');
        });
    } else {
        res.redirect('/login?msg=Authentication Failed. Please try again.');
    }
});

router.get('/logout', async function(req, res, next) {
    for(let i = 0; i < auth.validTokens.length; i++) {
        if(auth.validTokens[i] === req.session.token) {
            auth.validTokens.splice(i, 1);
        }
    }
    req.session.destroy(function(err) {
        if(err) {
            console.error(err);
        } else {
            auth.session = null;
            res.redirect('/login');
        }
    });
});

module.exports = router;