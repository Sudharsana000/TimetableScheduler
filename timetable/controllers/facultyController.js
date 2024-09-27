const db = require('../db');

// Fetch all faculties
exports.getFaculties = (req, res) => {
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
      return res.status(500).send('Internal Server Error');
    }

    const faculties = [];
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
};

// Add a new faculty
exports.addFaculty = (req, res) => {
  const { faculty_id, dept_id, name, email, designation, handling_paper_preferences } = req.body;
  db.beginTransaction(err => {
    if (err) {
      console.error('Transaction error:', err);
      return res.status(500).send('Failed to add faculty member');
    }

    const query = 'INSERT INTO faculty (faculty_id, dept_id, name, email, designation) VALUES (?, ?, ?, ?, ?)';
    db.query(query, [faculty_id, dept_id, name, email, designation], (facultyError) => {
      if (facultyError) {
        console.error('Error adding faculty:', facultyError);
        return db.rollback(() => res.status(500).send('Failed to add faculty'));
      }

      const preferencesQuery = 'INSERT INTO course_faculty (faculty_id, course_id) VALUES ?';
      const preferencesData = handling_paper_preferences.map(course_id => [faculty_id, course_id]);
      db.query(preferencesQuery, [preferencesData], (prefError) => {
        if (prefError) {
          console.error('Error adding faculty preferences:', prefError);
          return db.rollback(() => res.status(500).send('Failed to add preferences'));
        }

        db.commit(commitError => {
          if (commitError) {
            console.error('Commit error:', commitError);
            return db.rollback(() => res.status(500).send('Failed to commit transaction'));
          }
          res.sendStatus(200);
        });
      });
    });
  });
};

// Update faculty
exports.updateFaculty = (req, res) => {
  const { faculty_id, dept_id, name, email, designation } = req.body;
  const query = 'UPDATE faculty SET dept_id = ?, name = ?, email = ?, designation = ? WHERE faculty_id = ?';
  db.query(query, [dept_id, name, email, designation, faculty_id], (err, results) => {
    if (err) {
      console.error('Error updating faculty:', err);
      return res.status(500).json({ error: 'Failed to update faculty' });
    }
    res.status(200).json({ message: 'Faculty updated successfully' });
  });
};

// Delete faculty
exports.deleteFaculty = (req, res) => {
  const faculty_id = req.params.faculty_id;
  const deleteCourseFacultyQuery = 'DELETE FROM course_faculty WHERE faculty_id = ?';
  const deleteFacultyQuery = 'DELETE FROM faculty WHERE faculty_id = ?';

  db.query(deleteCourseFacultyQuery, [faculty_id], (err) => {
    if (err) {
      console.error('Error deleting from course_faculty:', err);
      return res.status(500).send('Failed to delete faculty from course_faculty');
    }

    db.query(deleteFacultyQuery, [faculty_id], (err2) => {
      if (err2) {
        console.error('Error deleting faculty:', err2);
        return res.status(500).send('Failed to delete faculty');
      }
      res.sendStatus(200);
    });
  });
};
