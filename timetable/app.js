const express = require('express');
const mysql = require('mysql');
const bodyParser = require('body-parser');
const path = require('path');
const { spawn } = require('child_process');

const app = express();
app.set('view engine', 'ejs');
app.use(bodyParser.json());

// Serve static files from the 'public' directory
app.use(express.static(path.join(__dirname, 'public')));

// Create a connection to the database
const db = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'chuchu',
  database: 'timetable_db'
});

// Connect to the database
db.connect((err) => {
  if (err) {
    console.error('error connecting:', err);
    return;
  }
  console.log('connected to database');
});

// Use body-parser to parse form data
app.use(bodyParser.urlencoded({ extended: true }));
app.use(bodyParser.json());

// Serve your main HTML file
app.get('/', (req, res) => {
  try {
    res.render("index");
  } catch (err) {
    console.log(err);
  }
});

// Create a route for the form submission
app.post('/home', (req, res) => {
  const { email, password } = req.body;

  const query = `SELECT * FROM users WHERE email = ? AND pswd = ?`;
  db.query(query, [email, password], (err, results) => {
    if (err) {
      console.error('error running query:', err);
      res.status(500).send('Error logging in');
    } else if (results.length === 0) {
      console.log('Login failed!');
      res.status(401).send('Invalid email or password');
    } else {
      console.log('Login successful!');
      res.render("home");
    }
  });
});

//fetch home page
app.get('/home', (req, res) => {
  try {
    res.render("home");
  } catch (err) {
    console.log(err);
  }
});

//fetch rooms page
app.get('/rooms', (req, res) => {
  const query = 'SELECT * FROM classrooms';
  db.query(query, (error, results) => {
      if (error) throw error;
      res.render('rooms', { classrooms: results });
  });
});

// Route to add a new classroom
app.post('/rooms', (req, res) => {
  const { hall_id, block, floor, capacity, facility } = req.body;
  const query = 'INSERT INTO classrooms (hall_id, block, floor, capacity, facility) VALUES (?, ?, ?, ?, ?)';
  db.query(query, [hall_id, block, floor, capacity, JSON.stringify(facility)], (error, results) => {
      if (error) {
          return res.status(500).send('Failed to add classroom');
      }
      res.sendStatus(200);
  });
});

// Update an existing classroom
app.put('/rooms/:hall_id', async (req, res) => {
  const hall_id = req.params.hall_id;
  const { block, floor, capacity, facility } = req.body;

  const query = 'UPDATE classrooms SET block = ?, floor = ?, capacity = ?, facility = ? WHERE hall_id = ?';
  const values = [block, floor, capacity, JSON.stringify(facility), hall_id];

  db.query(query, values, (error, results) => {
      if (error) {
          console.error('Error updating classroom:', error);
          return res.sendStatus(500);
      }

      if (results.affectedRows === 0) {
          // If no rows were affected, send a 404 status
          res.sendStatus(404);
      } else {
          // Send a 200 status if the update was successful
          res.sendStatus(200);
      }
  });
});

// delete classrooms
app.delete('/rooms/:hall_id', (req, res) => {
  const hall_id = req.params.hall_id;
  const query = 'DELETE FROM classrooms WHERE hall_id = ?';
  db.query(query, [hall_id], (error, results) => {
      if (error) {
          return res.status(500).send('Failed to delete classroom');
      }
      res.sendStatus(200);
  });
});

//##############################          FACULTY           #################################################//
// Fetch and display faculty list
app.get('/faculties', (req, res) => {
  const query = `
    SELECT f.faculty_id, f.dept_id, f.name, f.email, f.designation, 
           c.course_name
    FROM faculty f
    LEFT JOIN course_faculty cf ON f.faculty_id = cf.faculty_id
    LEFT JOIN courses c ON cf.course_id = c.course_id
    ORDER BY f.faculty_id;
  `;

  db.query(query, (error, results) => {
      if (error) {
          console.error('Error fetching faculties:', error);
          return res.status(500).json({ error: 'Internal Server Error' });
      }

      const faculties = [];

      // Group by faculty_id
      results.forEach(row => {
          let faculty = faculties.find(f => f.faculty_id === row.faculty_id);
          if (!faculty) {
              faculty = {
                  faculty_id: row.faculty_id,
                  dept_id: row.dept_id,
                  name: row.name,
                  email: row.email,
                  designation: row.designation,
                  handling_paper_preferences: []
              };
              faculties.push(faculty);
          }
          if (row.course_name) {
              faculty.handling_paper_preferences.push(row.course_name);
          }
      });

      res.render('faculties', { faculties });
  });
});

//get departments
app.get('/get_departments', (req, res) => {
  const query = 'SELECT dept_id, dept_name FROM department';

  db.query(query, (err, results) => {
      if (err) {
          console.error('Error fetching departments:', err);
          res.status(500).json({ error: 'Failed to fetch departments' });
      } else {
          const departments = results.map(row => ({
              id: row.dept_id,
              name: row.dept_name
          }));
          res.json({ departments });
      }
  });
});

// display courses
app.get('/get_courses/:dept_id', (req, res) => {
  const deptId = req.params.dept_id;

  const query = `SELECT course_id, course_name FROM courses WHERE dept_id = ?`
  // Assuming you have a function to get courses by department ID
  db.query(query, deptId, (err, results) => {
      if (err) {
          console.error('Error fetching Courses:', err);
          res.status(500).json({ error: 'Failed to fetch Courses' });
      } else {
          const courses = results.map(row => ({
              id: row.course_id,
              name: row.course_name
          }));
          res.json({ courses });
      }
  });
});

// Add Faculty Route
app.post('/add-faculty', (req, res) => {
  const { faculty_id, dept_id, name, email, designation, handling_paper_preferences } = req.body;
  // Start a transaction
  db.beginTransaction((err) => {
    if (err) {
      console.error('Transaction error:', err);
      return res.status(500).send('Failed to add faculty member');
    }

    // Insert into faculty table
    const facultyQuery = 'INSERT INTO faculty (faculty_id, dept_id, name, email, designation) VALUES (?, ?, ?, ?, ?)';
    db.query(facultyQuery, [faculty_id, dept_id, name, email, designation], (facultyError, facultyResults) => {
      if (facultyError) {
        console.error('Error adding faculty member:', facultyError);
        return db.rollback(() => {
          res.status(500).send('Failed to add faculty member');
        });
      }
      res.sendStatus(200);

      // Insert handling paper preferences into faculty_preferences table
      const preferencesQuery = 'INSERT INTO course_faculty (faculty_id, course_id) VALUES ?';
      const preferencesData = handling_paper_preferences.map(course_id => [faculty_id, course_id]);

      db.query(preferencesQuery, [preferencesData], (preferencesError, preferencesResults) => {
        if (preferencesResults) {
          res.status(200);
        }
        if (preferencesError) {
          console.error('Error adding faculty preferences:', preferencesError);
          return db.rollback(() => {
            res.status(500).send('Failed to add faculty preferences');
          });
        }
        res.status(200);

        // Commit the transaction
        db.commit((commitError) => {
          if (commitError) {
            console.error('Commit error:', commitError);
            return db.rollback(() => {
              res.status(500).send('Failed to commit transaction');
            });
          }
          // Redirect to the faculty list page or render a success message
          res.status(200);
        });
      });
    });
  });
});


app.put('/faculties/:facultyId', (req, res) => {
  const facultyId = req.params.facultyId;
  const {
      faculty_id,
      dept_id,
      name,
      email,
      designation,
      handling_paper_preferences
  } = req.body;

  const query = `
      UPDATE faculty
      SET faculty_id = ?, dept_id = ?, name = ?, email = ?, designation = ?, handling_paper_preferences = ?
      WHERE faculty_id = ?
  `;

  db.query(query, [faculty_id, dept_id, name, email, designation, JSON.stringify(handling_paper_preferences), facultyId], (err, results) => {
      if (err) {
          console.error('Error updating faculty data:', err);
          return res.status(500).json({ error: 'Failed to update faculty data' });
      }

      res.status(200).json({ message: 'Faculty data updated successfully' });
  });
});

app.delete('/delete_faculty/:faculty_id', async (req, res) => {
  const faculty_id = req.params.faculty_id;
  // Query to delete entries from course_faculty table
  const deleteCourseFacultyQuery = 'DELETE FROM course_faculty WHERE faculty_id = ?';
  // Query to delete entry from faculty table
  const deleteFacultyQuery = 'DELETE FROM faculty WHERE faculty_id = ?';

  try {
      // Delete from course_faculty table first
      await db.query(deleteCourseFacultyQuery, [faculty_id]);

      // Delete from faculty table
      await db.query(deleteFacultyQuery, [faculty_id]);

      // If both queries are successful, send a 200 status code
      res.sendStatus(200);
  } catch (error) {
      // If there's an error, send a 500 status code with an error message
      console.error('Failed to delete faculty:', error);
      res.status(500).send('Failed to delete faculty');
  }
});

//###################################### DEPARTMENTS ###########################################//
// Assuming you're using MySQL and have already set up your connection
app.get('/departments', (req, res) => {
  const sql = 'SELECT dept_id, dept_name FROM department';
  db.query(sql, (err, results) => {
      if (err) {
          console.error('Database query failed:', err);
          return res.status(500).send('Internal Server Error');
      }
      // Passing the fetched departments (both dept_id and dept_name) to the EJS template
      res.render('departments', { departments: results });
  });
});

//#####################################  TimeTable Generation  #######################################//
app.get('/generate', (req, res) => {
  const python = spawn('python', ['../timetable/python/mca2.py']);

  python.stdout.on('data', (data) => {
      res.json(JSON.parse(data));
  });

  python.stderr.on('data', (data) => {
      console.error(`stderr: ${data}`);
  });

  python.on('close', (code) => {
      console.log(`Process exited with code ${code}`);
  });
});

// Start the server
const port = 3000;
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});