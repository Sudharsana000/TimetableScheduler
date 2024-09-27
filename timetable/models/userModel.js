const db = require('../db');

// User login
exports.login = (email, password, callback) => {
  const query = 'SELECT * FROM users WHERE email = ? AND pswd = ?';
  db.query(query, [email, password], (err, results) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, results);
    }
  });
};

// Add a new user
exports.addUser = (userData, callback) => {
  const { user_id, email, password } = userData;
  const query = 'INSERT INTO users (user_id, email, pswd) VALUES (?, ?, ?)';
  db.query(query, [user_id, email, password], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};

// Update user details
exports.updateUser = (user_id, userData, callback) => {
  const { email, password } = userData;
  const query = 'UPDATE users SET email = ?, pswd = ? WHERE user_id = ?';
  db.query(query, [email, password, user_id], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};

// Delete user
exports.deleteUser = (user_id, callback) => {
  const query = 'DELETE FROM users WHERE user_id = ?';
  db.query(query, [user_id], (err, result) => {
    if (err) {
      callback(err, null);
    } else {
      callback(null, result);
    }
  });
};
