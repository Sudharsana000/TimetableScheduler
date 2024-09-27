const db = require('../db');

// Fetch all faculties
exports.getFaculties = (callback) => {
  const query = `
    SELECT f.faculty_id, f.dept_id, f.name, f.email, f.designation, c.course_name
    FROM faculty f
    LEFT JOIN course_faculty cf ON f.faculty_id = cf.faculty_id
    LEFT JOIN courses c ON cf.course_id = c.course_id
    ORDER BY f.faculty_id;
  `;
  db.query(query, (err, results) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, results);
    }
  });
};

// Add a new faculty
exports.addFaculty = (facultyData, callback) => {
  const { faculty_id, dept_id, name, email, designation } = facultyData;
  const insertFacultyQuery = `
    INSERT INTO faculty (faculty_id, dept_id, name, email, designation)
    VALUES (?, ?, ?, ?, ?)
  `;

  db.query(insertFacultyQuery, [faculty_id, dept_id, name, email, designation], (err, result) => {
    if (err) {
      return callback(err, null); // Call the callback with error
    }
    callback(null, result); // Call the callback with the result
  });
};


// Update faculty
exports.updateFaculty = (faculty_id, updatedData, callback) => {
  const { dept_id, name, email, designation } = updatedData;
  const query = 'UPDATE faculty SET dept_id = ?, name = ?, email = ?, designation = ? WHERE faculty_id = ?';
  db.query(query, [dept_id, name, email, designation, faculty_id], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};

// Delete faculty
exports.deleteFaculty = (faculty_id, callback) => {
  const deleteCourseFacultyQuery = 'DELETE FROM course_faculty WHERE faculty_id = ?';
  const deleteFacultyQuery = 'DELETE FROM faculty WHERE faculty_id = ?';

  db.query(deleteCourseFacultyQuery, [faculty_id], (err) => {
    if (err) return callback(err, null);

    db.query(deleteFacultyQuery, [faculty_id], (err2, result) => {
      if (err2) {
        callback(err2, null);
      } else {
        callback(null, result);
      }
    });
  });
};
