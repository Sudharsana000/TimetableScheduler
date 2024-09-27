const db = require('../db');

// Fetch all departments
exports.getDepartments = (callback) => {
  const query = 'SELECT dept_id, dept_name FROM department';
  db.query(query, (err, results) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, results);
    }
  });
};

// Add a new department
exports.addDepartment = (deptData, callback) => {
  const { dept_id, dept_name } = deptData;
  const query = 'INSERT INTO department (dept_id, dept_name) VALUES (?, ?)';
  db.query(query, [dept_id, dept_name], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};

// Update department
exports.updateDepartment = (dept_id, dept_name, callback) => {
  const query = 'UPDATE department SET dept_name = ? WHERE dept_id = ?';
  db.query(query, [dept_name, dept_id], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};

// Delete department
exports.deleteDepartment = (dept_id, callback) => {
  const query = 'DELETE FROM department WHERE dept_id = ?';
  db.query(query, [dept_id], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};
