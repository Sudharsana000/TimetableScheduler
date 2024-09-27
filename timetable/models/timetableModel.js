const timetableModel = require('../models/timetableModel');
const express = require('express');
const router = express.Router();

// For example, fetching timetable by group in a route
router.get('/timetable/:group', (req, res) => {
  const group = req.params.group;
  timetableModel.getTimetableByGroup(group, (err, timetable) => {
    if (err) {
      return res.status(500).json({ error: 'Failed to fetch timetable' });
    }
    res.json(timetable);
  });
});
