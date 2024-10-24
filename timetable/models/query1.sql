use timetable_db;

CREATE TABLE classrooms (
    hall_id VARCHAR(4) PRIMARY KEY,
    block VARCHAR(5),
    floor INT,
    capacity INT,
    facility JSON
);

INSERT INTO course (course_id, course_name, course_type, hours_per_week, programme_id, semester_number) VALUES
('18X105', 'English', 'Elective', 3, 'BSc CSD', NULL);

INSERT INTO faculty (faculty_id, dept_id, name, email, designation) VALUES
('AMCS001', 'AMCS', 'Dr Poomagal S', 'spm.amcs@psgtech.ac.in', 'Associate Professor'),
('AMCS002', 'AMCS', 'Dr Sasikumar M', 'msr.amcs@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('AMCS003', 'AMCS', 'Dr Brindha N', 'snb.amcs@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('AMCS004', 'AMCS', 'Mrs Deepa S', 'nsd.amcs@psgtech.ac.in', 'Assistant Professor(Sr. Gr.)'),
('AMCS005', 'AMCS', 'Ms Sudha S S', NULL, 'Assistant Professor');


CREATE TABLE users (
    email VARCHAR(200) PRIMARY KEY,
    password VARCHAR(50),
    username VARCHAR(50),
    usertype VARCHAR(50)
);

use timetable_db;

select * from users;

ALTER TABLE users
CHANGE password pswd varchar(50);

CREATE TABLE department (
    dept_id VARCHAR(5) PRIMARY KEY,
    dept_name VARCHAR(50),
    block VARCHAR(5),
    floor VARCHAR(1)
);

select * from department;

CREATE TABLE classrooms (
    hall_id VARCHAR(4) PRIMARY KEY,
    block varchar(5),
    floor INT,
    capacity INT,
    facility JSON
);

select * from classrooms;

CREATE TABLE labs (
    lab_id varchar(10) primary key,
    lab_name VARCHAR(100) NOT NULL,
    block VARCHAR(10) NOT NULL,
    floor INT NOT NULL,
    dept_id varchar(5),
    capacity INT NOT NULL,
    equipment JSON,
    lab_type VARCHAR(50) NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES department(dept_id) 
);

use timetable_db;
CREATE TABLE faculty (
    faculty_id VARCHAR(8) PRIMARY KEY,
    dept_id VARCHAR(5),
    name VARCHAR(100),
    email VARCHAR(100),
    designation VARCHAR(50),
    FOREIGN KEY (dept_id) REFERENCES department(dept_id) 
);

create table timetable (
	year_group varchar(255) primary key,
    timetable_data JSON
);

select * from users;
select * from labs;

ALTER TABLE students
ADD COLUMN programme_id VARCHAR(10),
ADD COLUMN `group` VARCHAR(5),
ADD CONSTRAINT fk_programme
    FOREIGN KEY (programme_id) REFERENCES programme(programme_id)
    ON DELETE CASCADE;

ALTER TABLE students
ADD COLUMN student_name VARCHAR(255);

ALTER TABLE students
ADD COLUMN programme_id VARCHAR(10),
ADD COLUMN `group` VARCHAR(5),
ADD CONSTRAINT fk_programme
    FOREIGN KEY (programme_id) REFERENCES programme(programme_id)
    ON DELETE CASCADE;
    
CREATE TABLE faculty_workload (
    faculty_id VARCHAR(8) PRIMARY KEY,  -- faculty_id as primary key
    workload_assigned INT DEFAULT 0,    -- workload_assigned to store the workload count
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id) ON DELETE CASCADE  -- foreign key reference to faculty table
);

DROP TRIGGER IF EXISTS update_faculty_workload;

DROP TRIGGER IF EXISTS update_faculty_workload;
DROP TRIGGER IF EXISTS update_faculty_workload_on_update;

DELIMITER $$

CREATE TRIGGER update_faculty_workload
AFTER INSERT ON faculty_allocation
FOR EACH ROW
BEGIN
    -- First, clear the current faculty workload table
    DELETE FROM faculty_workload;

    -- Recalculate and insert the workload for all faculties from faculty_allocation
    INSERT INTO faculty_workload (faculty_id, workload_assigned)
    SELECT faculty_id, COUNT(course_id) AS workload_assigned
    FROM faculty_allocation
    GROUP BY faculty_id;
END$$

DELIMITER ;

DELIMITER $$

CREATE TRIGGER update_faculty_workload_on_update
AFTER UPDATE ON faculty_allocation
FOR EACH ROW
BEGIN
    -- First, clear the current faculty workload table
    DELETE FROM faculty_workload;

    -- Recalculate and insert the workload for all faculties from faculty_allocation
    INSERT INTO faculty_workload (faculty_id, workload_assigned)
    SELECT faculty_id, COUNT(course_id) AS workload_assigned
    FROM faculty_allocation
    GROUP BY faculty_id;
END$$

DELIMITER ;

CREATE TABLE season (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sem_season ENUM('odd', 'even', 'none') NOT NULL,
    status ENUM('open', 'closed') NOT NULL
);

