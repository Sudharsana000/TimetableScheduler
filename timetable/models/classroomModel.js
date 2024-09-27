const db = require('../db');

exports.getClassrooms = (callback) => {
  const query = 'SELECT * FROM classrooms';
  db.query(query, (err, results) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, results);
    }
  });
};

exports.addClassroom = (classroomData, callback) => {
  const { hall_id, block, floor, capacity, facility } = classroomData;
  const query = 'INSERT INTO classrooms (hall_id, block, floor, capacity, facility) VALUES (?, ?, ?, ?, ?)';
  db.query(query, [hall_id, block, floor, capacity, JSON.stringify(facility)], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};

exports.updateClassroom = (hall_id, classroomData, callback) => {
  const { block, floor, capacity, facility } = classroomData;
  const query = 'UPDATE classrooms SET block = ?, floor = ?, capacity = ?, facility = ? WHERE hall_id = ?';
  db.query(query, [block, floor, capacity, JSON.stringify(facility), hall_id], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};

exports.deleteClassroom = (hall_id, callback) => {
  const query = 'DELETE FROM classrooms WHERE hall_id = ?';
  db.query(query, [hall_id], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};
