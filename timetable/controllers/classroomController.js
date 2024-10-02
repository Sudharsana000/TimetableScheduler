const db = require('../db');

// Fetch classrooms
exports.getClassrooms = (req, res) => {
  const query = 'SELECT * FROM classrooms';
  db.query(query, (error, results) => {
    if (error) {
      console.error('Error fetching classrooms:', error);
      return res.status(500).send('Error fetching classrooms');
    }
    res.render('rooms', { classrooms: results });
  });
};

// Add classroom
exports.addClassroom = (req, res) => {
  const { hall_id, block, floor, capacity, facility } = req.body;
  const query = 'INSERT INTO classrooms (hall_id, block, floor, capacity, facility) VALUES (?, ?, ?, ?, ?)';
  db.query(query, [hall_id, block, floor, capacity, JSON.stringify(facility)], (error, results) => {
    if (error) {
      console.error('Error adding classroom:', error);
      return res.status(500).send('Failed to add classroom');
    }
    res.sendStatus(200);
  });
};

// Update classroom
exports.updateClassroom = (req, res) => {
  const hall_id = req.params.hall_id;
  const { block, floor, capacity, facility } = req.body;
  const query = 'UPDATE classrooms SET block = ?, floor = ?, capacity = ?, facility = ? WHERE hall_id = ?';
  db.query(query, [block, floor, capacity, JSON.stringify(facility), hall_id], (error, results) => {
    if (error) {
      console.error('Error updating classroom:', error);
      return res.status(500).send('Failed to update classroom');
    }
    if (results.affectedRows === 0) return res.sendStatus(404);
    res.sendStatus(200);
  });
};

// Delete classroom
exports.deleteClassroom = (req, res) => {
  const hall_id = req.params.hall_id;
  const query = 'DELETE FROM classrooms WHERE hall_id = ?';
  db.query(query, [hall_id], (error, results) => {
    if (error) {
      console.error('Error deleting classroom:', error);
      return res.status(500).send('Failed to delete classroom');
    }
    res.sendStatus(200);
  });
};