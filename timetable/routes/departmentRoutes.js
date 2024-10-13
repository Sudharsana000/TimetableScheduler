const express = require('express');
const router = express.Router();
const departmentModel = require('../models/departmentModel');
const db = require('../db');

// Get all departments
router.get('/alldept', (req, res) => {
  const query = 'SELECT dept_id, dept_name FROM department';
  db.query(query, (error, results) => {
    if (error) {
      console.error('Error fetching classrooms:', error);
      return res.status(500).send('Error fetching classrooms');
    }
    const departments = results.map(row => ({
        id: row.dept_id,
        name: row.dept_name
    }));
    res.json({ departments });
  });
});

// Get all departments
router.get('/', (req, res) => {
  const query = 'SELECT * FROM department';
  db.query(query, (error, results) => {
    if (error) {
      console.error('Error fetching faculty:', error);
      return res.status(500).send('Error fetching faculties');
    }
    res.render('departments', { departments: results });
  });
});

// Add a new department
router.post('/add', (req, res) => {
  const {dept_id, dept_name, block, floor} = req.body; 
  const query = 'INSERT INTO department (dept_id, dept_name, block, floor) VALUES (?, ?, ?, ?)';
  db.query(query, [dept_id, dept_name, block, floor], (err) => {
    if (err) {
      console.error('Error adding department:', err);
      return res.status(500).send('Failed to add department');
    }
    res.sendStatus(200);
});
});

// Updated Router to fetch and display all timetables
router.get('/:dept_id', (req, res) => {
  const deptId = req.params.dept_id;

  // Query to fetch department details (type, name, etc.)
  db.query('SELECT * FROM department WHERE dept_id = ?', [deptId], (err, departmentResult) => {
    if (err) {
      console.error('Error fetching department:', err);
      return res.status(500).send('Error fetching department details');
    }

    const department = departmentResult[0];
    if (!department) {
      return res.status(404).send('Department not found');
    }

    // Fetch faculties and labs
    db.query('SELECT * FROM faculty WHERE dept_id = ?', [deptId], (err, facultyResult) => {
      if (err) {
        console.error('Error fetching faculties:', err);
        return res.status(500).send('Error fetching faculties');
      }

      db.query('SELECT * FROM labs WHERE dept_id = ?', [deptId], (err, labResult) => {
        if (err) {
          console.error('Error fetching labs:', err);
          return res.status(500).send('Error fetching labs');
        }

        // Fetch programmes and related structure.
        db.query(`
          SELECT 
            p.programme_id, 
            p.programme_name, 
            yt.programme_year, 
            gt.year_group, 
            t.semester, 
            t.day, 
            t.hour, 
            t.course_ids, 
            t.faculty_ids, 
            t.hall_ids, 
            t.lab_ids
          FROM 
            programme p
          JOIN 
            yeartable yt ON p.programme_id = yt.programme_id
          JOIN 
            grouptable gt ON yt.programme_id = gt.programme_id AND yt.programme_year = gt.programme_year
          LEFT JOIN 
            timetable t ON t.programme_id = p.programme_id AND t.programme_year = yt.programme_year AND t.year_group = gt.year_group
          WHERE 
            p.dept_id = ?
        `, [deptId], (err, programmeResult) => {
          if (err) {
            console.error('Error fetching programmes:', err);
            return res.status(500).send('Error fetching programmes');
          }

          // Prepare the JSON structure for programmes.
          const programmes = {};

          programmeResult.forEach(entry => {
            const {
              programme_id,
              programme_year,
              year_group,
              semester,
              day,
              hour,
              course_ids,
              faculty_ids,
              hall_ids,
              lab_ids
            } = entry;

            // Initialize the structure for the programme if not already done.
            if (!programmes[programme_id]) {
              programmes[programme_id] = {};
            }

            // Initialize the structure for the year if not already done.
            if (!programmes[programme_id][programme_year]) {
              programmes[programme_id][programme_year] = {};
            }

            // Initialize the structure for the semester if not already done.
            if (!programmes[programme_id][programme_year][semester]) {
              programmes[programme_id][programme_year][semester] = {};
            }

            // Initialize the structure for the group if not already done.
            if (!programmes[programme_id][programme_year][semester][year_group]) {
              programmes[programme_id][programme_year][semester][year_group] = {};
            }

            // Parse JSON strings to arrays only if they are defined and not null.
            const courseArray = course_ids ? JSON.parse(course_ids) : [];
            const hallArray = hall_ids ? JSON.parse(hall_ids) : [];
            const labArray = lab_ids ? JSON.parse(lab_ids) : [];
            const facultyArray = faculty_ids ? JSON.parse(faculty_ids) : [];

            // Store timetable data for the given day and hour.
            if (day && hour !== undefined) {
              if (!programmes[programme_id][programme_year][semester][year_group][day]) {
                programmes[programme_id][programme_year][semester][year_group][day] = {};
              }

              programmes[programme_id][programme_year][semester][year_group][day][hour] = {
                course_ids: courseArray,
                faculty_ids: facultyArray,
                hall_ids: hallArray,
                lab_ids: labArray
              };
            }
          });

          // Prepare objects to store schedules for faculties and labs.
          const formattedFacultySchedules = {};
          const formattedLabSchedules = {};
          let remainingQueries = facultyResult.length + labResult.length;

          // Iterate through each faculty and query their timetable separately.
          facultyResult.forEach((faculty) => {
            const facultyId = faculty.faculty_id;

            db.query(`
              SELECT 
                day, 
                hour, 
                semester,
                programme_id,
                year_group,
                faculty_ids,
                course_ids,
                hall_ids,
                lab_ids
              FROM 
                timetable 
              WHERE 
                JSON_CONTAINS(faculty_ids, ?)
            `, [`"${facultyId}"`], (err, scheduleResult) => {
              if (err) {
                console.error(`Error fetching schedules for faculty ${facultyId}:`, err);
                return res.status(500).send('Error fetching schedules');
              }

              // Format the result for the current faculty.
              scheduleResult.forEach(schedule => {
                const {
                  semester,
                  programme_id,
                  year_group,
                  day,
                  hour,
                  course_ids,
                  hall_ids,
                  lab_ids,
                  faculty_ids,
                } = schedule;
              
                // Parse JSON strings to arrays only if they are defined and not null.
                const courseArray = course_ids ? JSON.parse(course_ids) : [];
                const hallArray = hall_ids ? JSON.parse(hall_ids) : [];
                const labArray = lab_ids ? JSON.parse(lab_ids) : [];
                const facultyArray = faculty_ids ? JSON.parse(faculty_ids) : [];
              
                // Find the index of the current facultyId in the facultyArray.
                const facultyIndex = facultyArray.indexOf(facultyId);
              
                // Ensure facultyIndex is valid before accessing arrays.
                const course_id = facultyIndex !== -1 ? courseArray[facultyIndex] || null : null;
                const classroom_id = facultyIndex !== -1
                  ? (labArray[facultyIndex] || hallArray[facultyIndex] || null)
                  : null;
              
                // Initialize the structure for this facultyId if it doesn't exist.
                if (!formattedFacultySchedules[facultyId]) {
                  formattedFacultySchedules[facultyId] = {};
                }
              
                // Initialize the structure for the day if it doesn't exist.
                if (!formattedFacultySchedules[facultyId][day]) {
                  formattedFacultySchedules[facultyId][day] = {};
                }
              
                // Store the schedule details under the specified day and hour.
                formattedFacultySchedules[facultyId][day][hour] = {
                  course_id,
                  classroom_id,
                  programme_id,
                  semester,
                  year_group,
                };
              });
              
              // Check if all queries have completed.
              remainingQueries -= 1;
              if (remainingQueries === 0) {
                // All schedule queries are complete, render the result.
                res.render('department-detail', {
                  department,
                  faculties: facultyResult,
                  labs: labResult,
                  facultySchedules: formattedFacultySchedules,
                  labSchedules: formattedLabSchedules,
                  programmes
                });
              }
            });
          });

          // Fetch lab schedules and format them similarly to faculty schedules.
          labResult.forEach((lab) => {
            const labId = lab.lab_id;

            db.query(`
              SELECT 
                day, 
                hour, 
                semester,
                programme_id,
                year_group,
                course_ids,
                lab_ids
              FROM 
                timetable 
              WHERE 
                JSON_CONTAINS(lab_ids, ?)
            `, [`"${labId}"`], (err, labScheduleResult) => {
              if (err) {
                console.error(`Error fetching schedules for lab ${labId}:`, err);
                return res.status(500).send('Error fetching lab schedules');
              }

              // Format the result for the current lab.
              labScheduleResult.forEach(schedule => {
                const {
                  semester,
                  programme_id,
                  year_group,
                  day,
                  hour,
                  course_ids,
                  lab_ids,
                } = schedule;
              
                // Parse JSON strings to arrays only if they are defined and not null.
                const courseArray = course_ids ? JSON.parse(course_ids) : [];
                const labArray = lab_ids ? JSON.parse(lab_ids) : [];
              
                // Iterate over all lab entries in the labArray.
                labArray.forEach((lab_id, index) => {
                  const course_id = courseArray[index] || null;

                  // Initialize the structure for this lab_id if it doesn't exist.
                  if (!formattedLabSchedules[lab_id]) {
                    formattedLabSchedules[lab_id] = {};
                  }
    
                  // Initialize the structure for the day if it doesn't exist.
                  if (!formattedLabSchedules[lab_id][day]) {
                    formattedLabSchedules[lab_id][day] = {};
                  }
    
                  // Store the schedule details under the specified day and hour for the lab.
                  formattedLabSchedules[lab_id][day][hour] = {
                    course_id,
                    programme_id,
                    year_group,
                    semester,
                  };
                });
              });

              // Check if all queries have completed.
              remainingQueries -= 1;
              if (remainingQueries === 0) {
                // All schedule queries are complete, render the result.
                res.render('department-detail', {
                  department,
                  faculties: facultyResult,
                  labs: labResult,
                  facultySchedules: formattedFacultySchedules,
                  labSchedules: formattedLabSchedules,
                  programmes
                });
              }
            });
          });
        });
      });
    });
  });
});

// Updated Router to fetch and display all timetables
router.get('/:dept_id/timetable', (req, res) => {
  try {
    // Query to select all timetables from the database
    const query = 'SELECT year_group, timetable_data FROM timetable';
    db.query(query, (err, result) => {
        if (err) {
            console.error('Error fetching timetables:', err);
            return res.status(500).send('Error fetching timetables');
        }

        // If no timetables are found
        if (result.length === 0) {
            return res.status(404).send('No timetables found');
        }

        // Parse the JSON timetable data for each entry
        const timetables = result.map(row => ({
            year_group: row.year_group,
            timetable_data: JSON.parse(row.timetable_data)
        }));

        // Render the timetables using the 'timetables.ejs' view
        res.render('timetable', { timetables });
        });
    } catch (error) {
        console.error('Error:', error);
        res.status(500).send('Server error');
    }
});

// Update department
router.put('/departments/:id', (req, res) => {
  const dept_id = req.params.id;
  const dept_name = req.body.dept_name;
  departmentModel.updateDepartment(dept_id, dept_name, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to update department' });
    } else {
      res.json(result);
    }
  });
});

// Delete department
router.delete('/departments/:id', (req, res) => {
  const dept_id = req.params.id;
  departmentModel.deleteDepartment(dept_id, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to delete department' });
    } else {
      res.json(result);
    }
  });
});

module.exports = router;
