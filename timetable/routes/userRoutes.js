const express = require('express');
const router = express.Router();
const userModel = require('../models/userModel');

// User login
router.get('/', (req, res) => {
  res.render('index');
});


router.post('/home', (req, res) => {
  const { email, password } = req.body;
  userModel.login(email, password, (err, user) => {
    if (err) {
      res.status(500).json({ error: 'Login failed' });
    } else if (user.length === 0) {
      res.status(401).json({ error: 'Invalid credentials' });
    } else {
      res.render('home');
    }
  });
});

router.get('/homescreen', (req, res) => {
    res.render('home');
});


// Add a new user
router.post('/users', (req, res) => {
  const userData = req.body; // { user_id, email, password }
  userModel.addUser(userData, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to add user' });
    } else {
      res.json(result);
    }
  });
});

// Update user details
router.put('/users/:id', (req, res) => {
  const user_id = req.params.id;
  const updatedData = req.body; // { email, password }
  userModel.updateUser(user_id, updatedData, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to update user' });
    } else {
      res.json(result);
    }
  });
});

// Delete user
router.delete('/users/:id', (req, res) => {
  const user_id = req.params.id;
  userModel.deleteUser(user_id, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to delete user' });
    } else {
      res.json(result);
    }
  });
});

module.exports = router;
