const { spawn } = require('child_process');
const express = require('express');
const router = express.Router();
const db = require('../db');

router.get('/generate', (req, res) => {
    const python = spawn('python', ['../timetable/python/mca2.py']);
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
  
// POST route to insert timetable data
router.post('/store', (req, res) => {

  const timetableData = req.body.timetable;

  // Query the labs database to retrieve the list of lab names
  db.query('SELECT lab_id FROM labs', (err, labResults) => {
    if (err) {
      console.error('Error querying labs database:', err);
      return res.status(500).send('Error querying labs database');
    }

    const labs = labResults.map(row => row.lab_id); // Extract lab names from results

    // Query the halls database to retrieve the list of hall names
    db.query('SELECT hall_id FROM classrooms', (err, hallResults) => {
      if (err) {
        console.error('Error querying halls database:', err);
        return res.status(500).send('Error querying halls database');
      }

      const halls = hallResults.map(row => row.hall_id); // Extract hall names from results

      // Loop through each programme (e.g., MCA)
      Object.keys(timetableData).forEach(programme => {
        // Loop through each semester (e.g., 1, 3)
        Object.keys(timetableData[programme]).forEach(semester => {
          // Determine programme_year based on semester
          const programme_year = (semester === '1' || semester === '2') ? 1 : 2;

          // Loop through each group (e.g., G1, G2)
          Object.keys(timetableData[programme][semester]).forEach(group => {
            // Loop through each day of the week
            Object.keys(timetableData[programme][semester][group]).forEach(day => {
              // Loop through each hour of the day
              Object.keys(timetableData[programme][semester][group][day]).forEach(hour => {
                const entry = timetableData[programme][semester][group][day][hour];

                // Ensure Course, Faculty, and Classroom are arrays
                let course_ids = Array.isArray(entry.Course) ? entry.Course : [entry.Course];
                let faculty_ids = Array.isArray(entry.Faculty) ? entry.Faculty : [entry.Faculty];
                let classrooms = Array.isArray(entry.Classroom) ? entry.Classroom : [entry.Classroom];

                // Prepare for lab/hall identification
                let hall_ids = [];
                let lab_ids = [];

                // Loop through each classroom to identify labs and halls
                classrooms.forEach(classroom => {
                  if (labs.includes(classroom)) {
                    lab_ids.push(classroom); // Add to lab_ids if it's a lab
                  } else if (halls.includes(classroom)) {
                    hall_ids.push(classroom); // Add to hall_ids if it's a hall
                  } else {
                    console.error(`Unknown classroom type: ${classroom}`);
                  }
                });

                // Determine programme_year dynamically based on the semester
                const programme_year = Math.ceil(semester / 2);

                // Construct the SQL insert query for each timetable entry
                const query = `
                  INSERT INTO timetable 
                  (semester, programme_year, programme_id, year_group, day, hour, course_ids, faculty_ids, hall_ids, lab_ids)
                  VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                `;

                // Execute the query with data from the entry
                db.query(query, 
                  [
                    semester,              // Semester from the loop
                    programme_year,        // Programme year determined above
                    programme,             // Programme (e.g., MCA) from the loop
                    group,                 // Group (e.g., G1, G2) from the loop
                    day,                   // Day from the loop
                    hour,                  // Hour from the loop
                    JSON.stringify(course_ids),   // Array of course IDs
                    JSON.stringify(faculty_ids),  // Array of faculty IDs
                    JSON.stringify(hall_ids),     // Array of hall IDs
                    JSON.stringify(lab_ids)       // Array of lab IDs
                  ], 
                  (err, result) => {
                    if (err) {
                      console.error('Error inserting data:', err);
                    }
                  });
              });
            });
          });
        });
      });
      res.status(200).send('Timetable entries added successfully');
    });
  });
});

// Express route to handle allocation submission
router.post('/allocation', (req, res) => {
  const { semesterType } = req.body;

  // If the selected semester is 'odd', delete all related timetable entries
  const deleteQuery = `DELETE FROM timetable WHERE semester % 2 = 1`; // Assuming odd semesters have odd numbers (1, 3, 5, etc.)
  
  db.query(deleteQuery, (err, result) => {
      if (err) {
          console.error('Error deleting timetable entries:', err);
          return res.status(500).send('Failed to delete timetable entries.');
      }

      // After deletion, update the season record
      const updateQuery = `UPDATE season SET sem_season = ?, status = 'open' WHERE id = 1`;

      db.query(updateQuery, [semesterType], (err, result) => {
          if (err) {
              console.error('Error updating allocation:', err);
              return res.status(500).send('Failed to submit allocation.');
          }
          res.status(200).send('Allocation submitted and timetable entries deleted successfully.');
      });
  });
});

router.post('/close-allocation', (req, res) => {
  // Update the season table to set the status to 'closed' for the given semester type
  const query = `
      UPDATE season
      SET status = 'closed'
      WHERE status = 'open';
  `;

  db.query(query, (err, result) => {
      if (err) {
          console.error('Error updating allocation status:', err);
          return res.status(500).send('Failed to close the allocation.');
      }
      if (result.affectedRows > 0) {
          res.send('Allocation closed successfully!');
      } else {
          res.status(400).send('No open allocation found to close.');
      }
  });
});

module.exports = router;
