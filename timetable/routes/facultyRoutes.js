const express = require('express');
const router = express.Router();
const facultyModel = require('../models/facultyModel');
const db = require('../db');

// Get all faculties
router.get('/', (req, res) => {
  const query = 'SELECT * FROM faculty';
  db.query(query, (error, results) => {
    if (error) {
      console.error('Error fetching faculty:', error);
      return res.status(500).send('Error fetching faculties');
    }
    res.render('faculties', { faculties: results });
  });
});

// Add a new faculty
router.post('/add-faculty', (req, res) => {
  const facultyData = req.body.faculty;  // Extract only faculty data
  if (!facultyData) {
    return res.status(400).json({ error: "Faculty data is missing." });
  }

  facultyModel.addFaculty(facultyData, (err, result) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to add faculty' });
    }
    res.sendStatus(200);
  });
});


// Update faculty details
router.put('/faculties/:id', (req, res) => {
  const faculty_id = req.params.id;
  const updatedData = req.body; // { dept_id, name, email, designation }
  facultyModel.updateFaculty(faculty_id, updatedData, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to update faculty' });
    } else {
      res.json(result);
    }
  });
});

// Delete faculty
router.delete('/delete_faculty/:id', (req, res) => {
  const faculty_id = req.params.id;
  facultyModel.deleteFaculty(faculty_id, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to delete faculty' });
    } else {
      res.json(result);
    }
  });
});

module.exports = router;
