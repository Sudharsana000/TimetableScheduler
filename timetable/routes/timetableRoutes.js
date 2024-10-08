const { spawn } = require('child_process');
const express = require('express');
const router = express.Router();
const db = require('../db');

router.get('/generate', (req, res) => {
    const python = spawn('python', ['../timetable/python/trail.py']);
    let dataBuffer = '';

    // Listen for data from the Python script
    python.stdout.on('data', (data) => {
        dataBuffer += data.toString(); // Accumulate data chunks
    });

    // Handle error events
    python.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    // Handle the close event after the Python script finishes execution
    python.on('close', (code) => {
        console.log(`Process exited with code ${code}`);
        
        try {
            // Parse the complete buffered data as JSON
            const parsedData = JSON.parse(dataBuffer);
            res.json(parsedData);
        } catch (error) {
            console.error('Error parsing JSON data:', error);
            res.status(500).json({ error: 'Failed to parse JSON data from Python script' });
        }
    });
});
  
// Route to add timetable data
router.post('/store', async (req, res) => {
  const timetablesData = req.body; // This will contain the 'timetable' key
  
    // Check if timetablesData['timetable'] exists and is an object
    if (!timetablesData || !timetablesData['timetable'] || typeof timetablesData['timetable'] !== 'object') {
      return res.status(400).send('Invalid data format, please ensure the JSON object contains a valid timetable structure');
    }
  
    // Query for inserting or updating a timetable
    const query = 'INSERT INTO timetable (year_group, timetable_data) VALUES (?, ?) ON DUPLICATE KEY UPDATE timetable_data = ?';
  
    // Process each year_group entry in the timetablesData['timetable']
    const promises = Object.keys(timetablesData['timetable']).map((year_group) => {
    const timetable = timetablesData['timetable'][year_group]; // The timetable for the current year_group

    return new Promise((resolve, reject) => {
      // Store the timetable data as a JSON string in the database
      db.query(query, [year_group, JSON.stringify(timetable), JSON.stringify(timetable)], (err, result) => {
        if (err) {
          return reject(err);
        }
        resolve(result);
      });
    });
  });
  
  // Execute all database operations in parallel
  Promise.all(promises)
    .then(() => {
      res.send('Timetables added/updated successfully');
    })
    .catch((err) => {
      console.error('Error inserting/updating timetables:', err.message);
      res.status(500).send('Error inserting/updating timetables');
    });
});
  

module.exports = router;
