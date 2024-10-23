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

/// Function to fetch department data, including all faculties, groups, and workload
const fetchDepartmentData = (deptId, callback) => {
  // SQL query to fetch all programs in the given department
  const fetchProgramsQuery = `
    SELECT programme_id, programme_name 
    FROM programme
    WHERE dept_id = ?;
  `;

  // SQL query to fetch all courses in the department based on semester
  const fetchCoursesQuery = `
    SELECT course_id, course_name, course_type, hours_per_week, programme_id, semester_number 
    FROM course
    WHERE programme_id IN (
      SELECT programme_id FROM programme WHERE dept_id = ?
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

  // SQL query to fetch elective details (number of electives in each semester)
  const fetchElectiveDetailsQuery = `
    SELECT programme_id, semester_number, number_of_electives
    FROM elective_details
    WHERE programme_id IN (
      SELECT programme_id FROM programme WHERE dept_id = ?
    );
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
        res.render('home');
      } else if (userType === 'faculty_incharge') {
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
                        // Pass the departmentData and facultyAllocations to the render function
                        console.log(facultyAllocations);
                        res.render('allotment', {
                            departmentData,
                            allFaculties: departmentData.allFaculties,
                            facultyAllocations // Pass the faculty allocation data here
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

// Function to fetch faculty allocation details
function fetchFacultyAllocation(callback) {
  const query = 'SELECT faculty_id, course_id FROM faculty_allocation';
  db.query(query, (err, results) => {
      if (err) {
          return callback(err, null);
      }
      return callback(null, results);
  });
}


router.get('/homescreen', (req, res) => {
   res.render('home');
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

  console.log('Received Data:', JSON.stringify(allocationData, null, 2));

  try {
    // Extracting data for processing
    const program = allocationData.program;
    const coreCourses = allocationData.coreCourses;
    const electives = allocationData.electives;

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
    res.status(200).json({ message: 'Data received and processeddd.' });
  } catch (error) {
    console.error('Error processing data:', error);
    res.status(500).json({ message: 'Error processing data' });
  }
});

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

module.exports = router;
