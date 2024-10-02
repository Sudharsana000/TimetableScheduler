const db = require('../db');

// Controller function to fetch labs
exports.getLabs = (req, res) => {
    const query = 'SELECT * FROM labs';
    db.query(query, (error, labs) => {
      if (error) {
        console.error('Error fetching labs:', error);
        return res.status(500).send('Error fetching labs');
      }
      // Send the labs data as JSON
      console.log(labs);
      res.json(labs);
    });
  };
  