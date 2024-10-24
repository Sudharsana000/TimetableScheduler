const express = require('express');
const router = express.Router();
const userModel = require('../models/userModel');
const db = require('../db');
const studentModel = require('../models/studentModel');
const facultyModel = require('../models/facultyModel');

// User login
router.get('/', (req, res) => {
  res.render('index');
});

// Function to fetch department data, including all faculties, groups, and workload
const fetchDepartmentData = (deptId, callback) => {
  // SQL query to fetch all programs in the given department
  const fetchProgramsQuery = `
    SELECT programme_id, programme_name 
    FROM programme
    WHERE dept_id = ?;
  `;

    const fetchCoursesQuery = `
    WITH current_season AS (
      SELECT sem_season 
      FROM season 
      WHERE status = 'open' 
      LIMIT 1
    )
    SELECT course_id, course_name, course_type, hours_per_week, programme_id, semester_number 
    FROM course
    WHERE programme_id IN (
      SELECT programme_id 
      FROM programme 
      WHERE dept_id = ?
    )
    AND (
      MOD(semester_number, 2) = (
        CASE 
          WHEN (SELECT sem_season FROM current_season) = 'odd' THEN 1
          WHEN (SELECT sem_season FROM current_season) = 'even' THEN 0
        END
      )
      OR semester_number IS NULL
    )
    ORDER BY semester_number;
  `;



  // SQL query to fetch all faculties and their workload based on designation
  const fetchFacultiesQuery = `
    SELECT f.faculty_id, f.name, d.max_workload
    FROM faculty f
    JOIN designation d ON f.designation = d.designation
    WHERE f.dept_id = ?;
  `;

  // SQL query to fetch all faculties for electives (from all departments)
  const fetchAllFacultiesQuery = `
    SELECT faculty_id, name 
    FROM faculty;
  `;

  const fetchElectiveDetailsQuery = `
  WITH current_season AS (
    SELECT sem_season 
    FROM season 
    WHERE status = 'open' 
    LIMIT 1
  )
  SELECT programme_id, semester_number, number_of_electives
  FROM elective_details
  WHERE programme_id IN (
    SELECT programme_id 
    FROM programme 
    WHERE dept_id = ?
  )
  AND MOD(semester_number, 2) = (
    CASE 
      WHEN (SELECT sem_season FROM current_season) = 'odd' THEN 1
      WHEN (SELECT sem_season FROM current_season) = 'even' THEN 0
    END
  )
  ORDER BY semester_number;
`;


  // SQL query to fetch number of groups in each program and semester
  const fetchGroupDetailsQuery = `
    SELECT programme_id, programme_year, COUNT(*) as number_of_groups
    FROM grouptable
    WHERE programme_id IN (
      SELECT programme_id FROM programme WHERE dept_id = ?
    )
    GROUP BY programme_id, programme_year;
  `;

  // Fetch programs
  db.query(fetchProgramsQuery, [deptId], (err, programs) => {
    if (err) {
      return callback(err);
    }

    // Fetch courses
    db.query(fetchCoursesQuery, [deptId], (err, courses) => {
      if (err) {
        return callback(err);
      }

      // Fetch faculties and workload
      db.query(fetchFacultiesQuery, [deptId], (err, faculties) => {
        if (err) {
          return callback(err);
        }

        // Fetch all faculties for electives
        db.query(fetchAllFacultiesQuery, (err, allFaculties) => {
          if (err) {
            return callback(err);
          }

          // Fetch elective details
          db.query(fetchElectiveDetailsQuery, [deptId], (err, electives) => {
            if (err) {
              return callback(err);
            }

            // Fetch group details
            db.query(fetchGroupDetailsQuery, [deptId], (err, groups) => {
              if (err) {
                return callback(err);
              }

              // Combine the fetched data into a single object
              const departmentData = {
                programs: programs,
                courses: courses,
                faculties: faculties,
                electives: electives,
                allFaculties: allFaculties, // Adding all faculties for elective selection
                groups: groups, // Adding group details
              };

              // Return the final department data
              callback(null, departmentData);
            });
          });
        });
      });
    });
  });
};

// Handle the login and department data fetching
router.post('/home', (req, res) => {
  const { email, password } = req.body;

  // User login function
  userModel.login(email, password, (err, user) => {
    if (err) {
      console.error('Login failed:', err);
      res.status(500).json({ error: 'Login failed' });
    } else if (user.length === 0) {
      res.status(401).json({ error: 'Invalid credentials' });
    } else {
      const userType = user[0].usertype;
      const deptId = user[0].dept_id; // Assuming dept_id is part of the user object

      // Handle based on user type
      if (userType === 'admin') {
        const query = `SELECT * FROM season`;

        db.query(query, (err, results) => {
            if (err) {
                console.error('Error fetching season data:', err);
                return res.status(500).send('Failed to fetch season data.');
            }
            // Render the home view, passing the fetched season data
            res.render('home', { seasonData: results });
        });
      } else if (userType === 'faculty_incharge') {
        // Fetch season status to check if allocations are open
        fetchSeasonStatus((err, seasonStatus) => {
            if (err) {
                console.error('Failed to fetch season status:', err);
                res.status(500).json({ error: 'Failed to fetch season status' });
            } else if (seasonStatus === 'closed') {
              // Season is closed, but we still render the allotment page with a message
              fetchDepartmentData(deptId, (err, departmentData) => {
                if (err) {
                  console.error('Failed to fetch department data:', err);
                  return res.status(500).json({ error: 'Failed to fetch department data' });
                }
    
                fetchFacultyAllocation((err, facultyAllocations) => {
                  if (err) {
                    console.error('Failed to fetch faculty allocation data:', err);
                    return res.status(500).json({ error: 'Failed to fetch faculty allocation data' });
                  }
    
                  fetchElectiveAllocation(deptId, (err, electiveAllocations) => {
                    if (err) {
                      console.error('Failed to fetch elective allocation data:', err);
                      return res.status(500).json({ error: 'Failed to fetch elective allocation data' });
                    }
    
                    // Render the page with a message stating the timetable allotment is closed
                    res.render('allotment', {
                      userID: email,
                      email: email,
                      password : password,
                      deptId: deptId,
                      seasonClosed: true, // Pass seasonClosed as true
                      message: 'Timetable allotment for this semester has been closed.'
                    });
                  });
                });
              });
            } else {
                // Fetch department programs, courses, faculties, group details, and workload if the user is a faculty in-charge
                fetchDepartmentData(deptId, (err, departmentData) => {
                    if (err) {
                        console.error('Failed to fetch department data:', err);
                        res.status(500).json({ error: 'Failed to fetch department data' });
                    } else {
                        // Fetch faculty allocation details
                        fetchFacultyAllocation((err, facultyAllocations) => {
                            if (err) {
                                console.error('Failed to fetch faculty allocation data:', err);
                                res.status(500).json({ error: 'Failed to fetch faculty allocation data' });
                            } else {
                                // Fetch elective allocation details
                                fetchElectiveAllocation(deptId, (err, electiveAllocations) => {
                                    if (err) {
                                        console.error('Failed to fetch elective allocation data:', err);
                                        res.status(500).json({ error: 'Failed to fetch elective allocation data' });
                                    } else {
                                        console.log(electiveAllocations);
                                        // Pass departmentData, facultyAllocations, and electiveAllocations to the render function
                                        res.render('allotment', {
                                            userID: email,
                                            departmentData,
                                            allFaculties: departmentData.allFaculties,
                                            facultyAllocations,  // Pass the faculty allocation data
                                            electiveAllocations,  // Pass the elective allocation data
                                            email: email,
                                            password : password,
                                            deptId: deptId,
                                            seasonClosed: false,
                                            message: ''
                                        });
                                    }
                                });
                            }
                        });
                    }
                });
            }
        });
    } else if (userType === 'student') {
        // Fetch student details
        studentModel.getStudentByRollNo(email, (err, student) => {
          if (err) {
            console.error('Error fetching student details:', err);
            res.status(500).json({ error: 'Error fetching student details' });
          } else if (student.length === 0) {
            res.status(404).json({ error: 'Student not found' });
          } else {
            const studentData = student[0];
            const currentYear = new Date().getFullYear();
            const programmeYear = currentYear - studentData.year_of_joining + 1; // Calculate the year difference
            console.log(programmeYear);
      
            // Calculate the odd semester based on the programme year (e.g., 1st year => 1st semester, 2nd year => 3rd semester, etc.)
            const oddSemester = (programmeYear * 2) - 1;
      
            // Fetch timetable for the student based on programme and group and only odd semester
            const query = `
              SELECT 
                t.semester, 
                t.day, 
                t.hour, 
                t.course_ids, 
                t.faculty_ids, 
                t.hall_ids, 
                t.lab_ids
              FROM 
                timetable t
              WHERE 
                t.programme_id = ? 
                AND t.programme_year = ? 
                AND t.semester = ?
                AND t.year_group = ?
            `;
            db.query(query, [studentData.programme_id, programmeYear, oddSemester, studentData.group], (err, timetableResult) => {
              if (err) {
                console.error('Error fetching timetable:', err);
                res.status(500).json({ error: 'Error fetching timetable' });
              } else {
                // Process the timetable and send it to the client
                const timetable = {};
      
                timetableResult.forEach(entry => {
                  const { semester, day, hour, course_ids, faculty_ids, hall_ids, lab_ids } = entry;
      
                  // Initialize the structure for the semester if not already done
                  if (!timetable[semester]) {
                    timetable[semester] = {};
                  }
      
                  // Initialize the structure for the day if not already done
                  if (!timetable[semester][day]) {
                    timetable[semester][day] = {};
                  }
      
                  // Store timetable data for the given day and hour
                  timetable[semester][day][hour] = {
                    courses: JSON.parse(course_ids),
                    faculties: JSON.parse(faculty_ids),
                    halls: JSON.parse(hall_ids),
                    labs: JSON.parse(lab_ids),
                  };
                });
                console.log(timetable);
                res.render('student-timetable', { student: studentData, timetable });
              }
            });
          } 
        });
      } else if (userType === 'faculty') {
        const facultyId = email; // Assuming facultyId is derived from email or session
      
        // Fetch faculty details by facultyId
        facultyModel.getFacultyById(facultyId, (err, faculty) => {
          if (err) {
            console.error('Error fetching faculty details:', err);
            res.status(500).json({ error: 'Error fetching faculty details' });
          } else if (faculty.length === 0) {
            res.status(404).json({ error: 'Faculty not found' });
          } else {
            const facultyData = faculty[0];
      
            // Fetch timetable for the faculty
            facultyModel.getFacultyTimetable(facultyId, (err, timetableResult) => {
              if (err) {
                console.error('Error fetching timetable:', err);
                res.status(500).json({ error: 'Error fetching timetable' });
              } else {
                const timetable = {};
      
                timetableResult.forEach(entry => {
                  const { programme_id, semester, year_group, day, hour, course_name, hall_ids } = entry;
      
                  // Initialize timetable structure
                  if (!timetable[semester]) {
                    timetable[semester] = {};
                  }
      
                  if (!timetable[semester][day]) {
                    timetable[semester][day] = {};
                  }
      
                  // Store timetable data for the day and hour
                  timetable[semester][day][hour] = {
                    programme: `${programme_id}-${semester}-${year_group}`,
                    course: course_name,
                    halls: JSON.parse(hall_ids).join(', '), // Convert hall_ids from JSON array to string
                  };
                });
      
                // Render the timetable view
                res.render('faculty-timetable', { faculty: facultyData, timetable });
              }
            });
          }
        });
      } else {
        res.status(403).json({ error: 'Unauthorized access' });
      }
    }
  });
});

function fetchSeasonStatus(callback) {
  const query = `SELECT status FROM season WHERE id = 1 LIMIT 1`;

  db.query(query, (err, results) => {
      if (err) {
          return callback(err, null);
      }

      if (results.length > 0) {
          return callback(null, results[0].status);  // 'open' or 'closed'
      } else {
          return callback(new Error('Season data not found'), null);
      }
  });
}


// Function to fetch faculty allocation details
function fetchFacultyAllocation(callback) {
  // First, check whether the current season is odd or even from the 'season' table
  const seasonQuery = `SELECT sem_season FROM season WHERE status = 'open' LIMIT 1`;

  db.query(seasonQuery, (err, seasonResult) => {
      const query = `
          SELECT faculty_id, course_id 
          FROM faculty_allocation
      `;

      db.query(query, (err, results) => {
          if (err) {
              return callback(err, null);
          }
          console.log(results);
          return callback(null, results);
      });
  });
}


function fetchElectiveAllocation(deptId, callback) {
  const query = 'SELECT * FROM elective_allocation';
  db.query(query, [deptId], (err, results) => {
      if (err) {
          callback(err, null);
      } else {
          callback(null, results);
      }
  });
}

router.get('/homescreen', (req, res) => {
  const query = `SELECT * FROM season`;

  db.query(query, (err, results) => {
      if (err) {
          console.error('Error fetching season data:', err);
          return res.status(500).send('Failed to fetch season data.');
      }

      // Render the home view, passing the fetched season data
      res.render('home', { seasonData: results });
  });
});

// Add a new user
router.post('/users', (req, res) => {
  const userData = req.body; // { user_id, email, password }
  userModel.addUser(userData, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to add user' });
    } else {
      res.json(result);
    }
  });
});

// Update user details
router.put('/users/:id', (req, res) => {
  const user_id = req.params.id;
  const updatedData = req.body; // { email, password }
  userModel.updateUser(user_id, updatedData, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to update user' });
    } else {
      res.json(result);
    }
  });
});

router.post('/addAllotments', async (req, res) => {
  const allocationData = req.body;

  try {
    const program = allocationData.program;
    const coreCourses = allocationData.coreCourses;
    const electives = allocationData.electives;

    // Delete existing faculty and elective allocations for the given program before inserting new data
    await deleteExistingAllocations(program);

    // Faculty allocation for core courses
    if (coreCourses && Object.keys(coreCourses).length > 0) {
      for (const courseId in coreCourses) {
        const faculties = coreCourses[courseId];

        for (const facultyId of faculties) {
          // Insert into faculty_allocation (for core courses)
          await insertFacultyAllocation(facultyId, courseId);
        }
      }
    }

    // Faculty and elective allocation for elective courses
    if (electives && Object.keys(electives).length > 0) {
      for (const semester in electives) {
        const electiveDetails = electives[semester];

        for (const electiveName in electiveDetails) {
          // Extract the numeric part from 'Elective 1', 'Elective 2', etc.
          const electiveNo = electiveName.match(/\d+/)[0];  // This will extract '1' from 'Elective 1'

          const courses = electiveDetails[electiveName];

          for (const courseId in courses) {
            const faculties = courses[courseId].faculty;
            const strength = parseInt(courses[courseId].strength);

            for (const facultyId of faculties) {
              // Insert into faculty_allocation (for electives)
              await insertFacultyAllocation(facultyId, courseId);
            }

            // Insert into elective_allocation (only for electives)
            await insertElectiveAllocation(courseId, program, electiveNo, semester, strength);
          }
        }
      }
    }
    // If all insertions are successful, send response back
    res.status(200).json({ message: 'Data received and processed.' });
  } catch (error) {
    console.error('Error processing data:', error);
    res.status(500).json({ message: 'Error processing data' });
  }
});

// // Delete existing allocations before inserting new data
// async function deleteExistingAllocations(programId) {
//   // Execute the query and get the courses
//   const result = await db.query('SELECT course_id FROM course WHERE programme_id = ?', [programId]);

//   // Check if the result contains rows
//   const courses = result[0]; // Assuming the first item contains the rows in some query systems
//   // If it's in the structure of result.rows, use: const courses = result.rows;

//   // Check if courses is an array
//   if (Array.isArray(courses) && courses.length > 0) {
//     const courseIds = courses.map(course => course.course_id);

//     if (courseIds.length > 0) {
//       // Delete from faculty_allocation for the identified course_ids
//       const facultyDeletionQuery = `
//         DELETE FROM faculty_allocation WHERE course_id IN (?);
//       `;
//       await db.query(facultyDeletionQuery, [courseIds]);

//       // Delete from elective_allocation for the identified course_ids and the given program_id
//       const electiveDeletionQuery = `
//         DELETE FROM elective_allocation WHERE course_id IN (?) AND programme_id = ?;
//       `;
//       await db.query(electiveDeletionQuery, [courseIds, programId]);
//     }
//   } else {
//     console.log('No courses found for the given program.');
//   }
// }

const deleteExistingAllocations = async (program) => {
  try {
    // First, find all course_ids associated with the given programme_id
    const courseIds = await db.query(
      'SELECT course_id FROM course WHERE programme_id = ?',
      [program]
    );

    if (courseIds.length > 0) {
      const courseIdList = courseIds.map(row => row.course_id);

      // Delete from faculty_allocation where course_id matches the list
      await db.query(
        'DELETE FROM faculty_allocation WHERE course_id IN (?)',
        [courseIdList]
      );

      // Delete from elective_allocation where programme_id matches
      await db.query(
        'DELETE FROM elective_allocation WHERE programme_id = ?',
        [program]
      );

      console.log(`Deleted allocations for program: ${program}`);
    } else {
      console.log(`No courses found for program: ${program}`);
    }
  } catch (error) {
    console.error('Error deleting existing allocations:', error);
    throw error;  // Re-throw error to be caught by the calling function
  }
};


// Insert into faculty_allocation if not exists
async function insertFacultyAllocation(facultyId, courseId) {
  const query = `
    INSERT INTO faculty_allocation (faculty_id, course_id)
    SELECT * FROM (SELECT ? AS faculty_id, ? AS course_id) AS tmp
    WHERE NOT EXISTS (
      SELECT 1 FROM faculty_allocation WHERE faculty_id = ? AND course_id = ?
    ) LIMIT 1;
  `;
  await db.query(query, [facultyId, courseId, facultyId, courseId]);
}

// Insert into elective_allocation if not exists
async function insertElectiveAllocation(courseId, programmeId, electiveNo, semesterNumber, strength) {
  const query = `
    INSERT INTO elective_allocation (course_id, programme_id, elective_no, semester_number, strength)
    SELECT * FROM (SELECT ? AS course_id, ? AS programme_id, ? AS elective_no, ? AS semester_number, ? AS strength) AS tmp
    WHERE NOT EXISTS (
      SELECT 1 FROM elective_allocation WHERE course_id = ? AND programme_id = ? AND elective_no = ? AND semester_number = ?
    ) LIMIT 1;
  `;
  await db.query(query, [courseId, programmeId, electiveNo, semesterNumber, strength, courseId, programmeId, electiveNo, semesterNumber]);
}

// Delete user
router.delete('/users/:id', (req, res) => {
  const user_id = req.params.id;
  userModel.deleteUser(user_id, (err, result) => {
    if (err) {
      res.status(500).json({ error: 'Failed to delete user' });
    } else {
      res.json(result);
    }
  });
});

// Route for the My Timetable page
router.get('/my-timetable', (req, res) => {
  const userID = req.query.userID; // Extract userID from query parameter
  res.render('my-timetable', { userID }); // Pass userID to the my-timetable.ejs
});


// Route for the All Timetables page
router.get('/all-timetables', (req, res) => {
  res.render('all-timetables'); // Renders all-timetables.ejs
});





module.exports = router;
