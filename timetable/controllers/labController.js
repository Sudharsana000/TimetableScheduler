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
      res.json(labs);
    });
  };
  
exports.addLabs = (req, res) => {
  const { lab_id, lab_name, dept_id, block, floor, capacity, equipment, lab_type } = req.body;
  const query = `INSERT INTO labs (lab_id, lab_name, dept_id, block, floor, capacity, equipment, lab_type)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?)`;

  db.query(query, [lab_id, lab_name, dept_id, block, floor, capacity, JSON.stringify(equipment), JSON.stringify(lab_type)], (err, result) => {
      if (err) {
          console.error('Error inserting data:', err);
          res.status(500).send('Error inserting data into the database');
      } else {
          res.status(200).send('Lab data added successfully');
      }
  });
}