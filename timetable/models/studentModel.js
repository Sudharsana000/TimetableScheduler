const db = require('../db'); // Assuming you have a db connection const db = require('../db');

const studentModel = {};

// Function to fetch student details by roll number (email)
studentModel.getStudentByRollNo = (rollno, callback) => {
  const query = 'SELECT rollno, student_name, year_of_joining, programme_id, `group` FROM students WHERE rollno = ?';
  db.query(query, [rollno], (err, results) => {
    if (err) {
      return callback(err, null);
    }
    callback(null, results);
  });
};

module.exports = studentModel;
