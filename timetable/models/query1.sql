use timetable_db;

CREATE TABLE classrooms (
    hall_id VARCHAR(4) PRIMARY KEY,
    block VARCHAR(5),
    floor INT,
    capacity INT,
    facility JSON
);

INSERT INTO course (course_id, course_name, course_type, hours_per_week, programme_id, semester_number) VALUES
('18X101', 'Calculus and its Applications', 'Core', 3, 'BSc CSD', 1),
('18X102', 'Environmental Science and Green Computing', 'Core', 3, 'BSc CSD', 1),
('18X103', 'C Programming', 'Core', 3, 'BSc CSD', 1),
('18X104', 'Analog and Digital Electronics', 'Core', 3, 'BSc CSD', 1),
('18X105', 'English', 'Core', 3, 'BSc CSD', 1),
('18X106', 'C Programming Laboratory', 'Lab', 2, 'BSc CSD', 1),
('18X107', 'Web Design Laboratory', 'Lab', 2, 'BSc CSD', 1),
('18X108', 'Analog and Digital Electronics Laboratory', 'Lab', 2, 'BSc CSD', 1);


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
