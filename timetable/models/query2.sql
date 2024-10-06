use timetable_db;

create table department (
	dept_id varchar(10) primary key,
    dept_name varchar(255) not null,
    block varchar(1) not null,
    floor int not null,
    dept_type ENUM('service', 'non-service', 'both') NOT NULL
);
select * from department;

CREATE TABLE Programme (
    programme_id varchar(10) PRIMARY KEY,  -- Unique ID for each programme
    programme_name VARCHAR(100) NOT NULL,  -- Name of the programme
    dept_id varchar(10),  -- Reference to the Department
	FOREIGN KEY (dept_id) REFERENCES Department(dept_id) ON DELETE CASCADE
);

select * from department;
select * from programme;

create table yearTable(
	programme_year int not null,
    programme_id varchar(10) not null,
    primary key(programme_year, programme_id),
    FOREIGN KEY (programme_id) REFERENCES Programme(programme_id) ON DELETE CASCADE
);

select * from yearTable;

create table GroupTable(
	year_group varchar(2) not null,
    programme_year int not null,
	programme_id varchar(10) not null,
    group_strength int not null,
    primary key(programme_year, programme_id, year_group),
    FOREIGN KEY (programme_year, programme_id) REFERENCES yearTable(programme_year, programme_id) ON DELETE CASCADE
);

select * from GroupTable;

CREATE TABLE Course (
    course_id varchar(10) PRIMARY KEY,  -- Unique ID for each course
    course_name VARCHAR(100) NOT NULL,  -- Name of the course
    course_type ENUM('Core', 'Elective', 'Lab') NOT NULL,  -- Type of the course
    hours_per_week INT NOT NULL,  -- Number of hours per week for the course
    programme_id varchar(10) NOT NULL,  -- Programme that this course belongs to
    semester_number INT,  -- Semester for regular and lab courses; elective courses won't have this field populated
    FOREIGN KEY (programme_id) REFERENCES Programme(programme_id) ON DELETE CASCADE,
    CHECK ((course_type = 'Elective' AND semester_number IS NULL) OR (course_type IN ('Core', 'Lab') AND semester_number IS NOT NULL))
);

select * from course;

