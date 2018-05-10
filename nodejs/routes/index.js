const express = require('express');
const router = express.Router();
const store = require('../indy/messageStore');
const indy = require('../indy');

/* GET home page. */
router.get('/', async function(req, res, next) {
      res.render('index', { messages: store.getMessages(), publicDid: await indy.getPublicDid() });
});

module.exports = router;

