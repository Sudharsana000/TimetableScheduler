const express = require('express');
const router = express.Router();
const controller = require('../controllers/labController');

// Route to get labs data
router.get('/getLabs', controller.getLabs);
router.post('/addLabs', controller.addLabs);

module.exports = router;
