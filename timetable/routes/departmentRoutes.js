const express = require('express');
const router = express.Router();
const departmentModel = require('../models/departmentModel');
const db = require('../db');

// Get all departments
router.get('/alldept', (req, res) => {
  const query = 'SELECT dept_id, dept_name FROM department';
  db.query(query, (error, results) => {
    if (error) {
      console.error('Error fetching classrooms:', error);
      return res.status(500).send('Error fetching classrooms');
    }
    const departments = results.map(row => ({
        id: row.dept_id,
        name: row.dept_name
    }));
    res.json({ departments });
  });
});

// Get all departments
router.get('/', (req, res) => {
  const query = 'SELECT * FROM department';
  db.query(query, (error, results) => {
    if (error) {
      console.error('Error fetching faculty:', error);
      return res.status(500).send('Error fetching faculties');
    }
    res.render('departments', { departments: results });
  });
});

// Add a new department
router.post('/add', (req, res) => {
  const {dept_id, dept_name, block, floor} = req.body; 
  const query = 'INSERT INTO department (dept_id, dept_name, block, floor) VALUES (?, ?, ?, ?)';
  db.query(query, [dept_id, dept_name, block, floor], (err) => {
    if (err) {
      console.error('Error adding department:', err);
      return res.status(500).send('Failed to add department');
    }
    res.sendStatus(200);
});
});

// Updated Router to fetch and display all timetables
router.get('/:dept_id/timetable', (req, res) => {
  try {
    // Query to select all timetables from the database
    const query = 'SELECT year_group, timetable_data FROM timetable';
    db.query(query, (err, result) => {
        if (err) {
            console.error('Error fetching timetables:', err);
            return res.status(500).send('Error fetching timetables');
        }

        // If no timetables are found
        if (result.length === 0) {
            return res.status(404).send('No timetables found');
        }

        // Parse the JSON timetable data for each entry
        const timetables = result.map(row => ({
            year_group: row.year_group,
            timetable_data: JSON.parse(row.timetable_data)
        }));

        // Render the timetables using the 'timetables.ejs' view
        res.render('timetable', { timetables });
        });
    } catch (error) {
        console.error('Error:', error);
        res.status(500).send('Server error');
    }
});

// Update department
router.put('/departments/:id', (req, res) => {
  const dept_id = req.params.id;
  const dept_name = req.body.dept_name;
  departmentModel.updateDepartment(dept_id, dept_name, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to update department' });
    } else {
      res.json(result);
    }
  });
});

// Delete department
router.delete('/departments/:id', (req, res) => {
  const dept_id = req.params.id;
  departmentModel.deleteDepartment(dept_id, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to delete department' });
    } else {
      res.json(result);
    }
  });
});

module.exports = router;
