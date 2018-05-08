const express = require('express');
const router = express.Router();
const store = require('../indy/messageStore');

/* GET home page. */
router.get('/', function(req, res, next) {
      res.render('index', { title: 'Express', messages: store.getMessages() });
});

module.exports = router;

