const db = require('../db');

// User login
exports.login = (req, res) => {
  const { email, password } = req.body;
  const query = 'SELECT * FROM users WHERE email = ? AND pswd = ?';
  db.query(query, [email, password], (err, results) => {
    if (err) {
      console.error('Error during login:', err);
      return res.status(500).send('Error logging in');
    }
    if (results.length === 0) {
      return res.status(401).send('Invalid email or password');
    }
    res.render('home');
  });
};

// Fetch home page
exports.getHomePage = (req, res) => {
  res.render('home');
};
