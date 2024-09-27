const express = require('express');
const bodyParser = require('body-parser');
const path = require('path');
const db = require('./db'); // Database connection
const classroomRoutes = require('./routes/classroomRoutes');
const facultyRoutes = require('./routes/facultyRoutes');
const departmentRoutes = require('./routes/departmentRoutes');
const userRoutes = require('./routes/userRoutes');
const timetableRoutes = require('./routes/timetableRoutes');

const app = express();

app.set('view engine', 'ejs');
app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

// Use routes
app.use('/', userRoutes);  // Login route
app.use('/homescreen', userRoutes);
app.use('/classrooms', classroomRoutes);
app.use('/faculties', facultyRoutes);
app.use('/departments', departmentRoutes);
app.use('/timetable', timetableRoutes);

// Start the server
const port = 3000;
app.listen(port, () => {
  console.log(`Server listening on port ${port}`);
});
