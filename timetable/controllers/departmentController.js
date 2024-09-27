const db = require('../db');

// Fetch all departments
exports.getDepartments = (req, res) => {
  const query = 'SELECT * FROM department';
  db.query(query, (err, results) => {
    if (err) {
      console.error('Error fetching departments:', err);
      return res.status(500).send('Failed to fetch departments');
    }
    res.render('departments', { departments: results });
  });
};

// Add a new department
exports.addDepartment = (req, res) => {
  const { dept_id, dept_name, block, floor } = req.body;
  console.log({ dept_id, dept_name, block, floor });
  const query = 'INSERT INTO department (dept_id, dept_name, block, floor) VALUES (?, ?, ?, ?)';
  db.query(query, [dept_id, dept_name, block, floor], (err) => {
    if (err) {
      console.error('Error adding department:', err);
      return res.status(500).send('Failed to add department');
    }
    res.sendStatus(200);
  });
};

// Update department
exports.updateDepartment = (req, res) => {
  const { dept_id, dept_name } = req.body;
  const query = 'UPDATE department SET dept_name = ? WHERE dept_id = ?';
  db.query(query, [dept_name, dept_id], (err) => {
    if (err) {
      console.error('Error updating department:', err);
      return res.status(500).send('Failed to update department');
    }
    res.sendStatus(200);
  });
};

// Delete department
exports.deleteDepartment = (req, res) => {
  const dept_id = req.params.dept_id;
  const query = 'DELETE FROM department WHERE dept_id = ?';
  db.query(query, [dept_id], (err) => {
    if (err) {
      console.error('Error deleting department:', err);
      return res.status(500).send('Failed to delete department');
    }
    res.sendStatus(200);
  });
};
