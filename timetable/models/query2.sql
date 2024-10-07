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
    primary key(programme_year, programme_id, yeargrouptable_group),
    FOREIGN KEY (programme_year, programme_id) REFERENCES yearTable(programme_year, programme_id) ON DELETE CASCADE
);

select * from GroupTable;
select * from labs;

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
select * from programme;
drop table faculty_allocation;

create table faculty_allocation(
	faculty_id varchar(8) not null,
    course_id varchar(10) not null,
    FOREIGN KEY (faculty_id) REFERENCES faculty(faculty_id),
    FOREIGN KEY (course_id) REFERENCES course(course_id),
    primary key(faculty_id, course_id)
);

INSERT INTO faculty (faculty_id, dept_id, name, email, designation) VALUES
('CA001', 'CA', 'Dr. Chitra A', 'ac.mca@psgtech.ac.in', 'Professor & Head'),
('CA002', 'CA', 'Dr. Manavalan R', 'vwm.mca@psgtech.ac.in', 'Associate Professor'),
('CA003', 'CA', 'Mrs. Kalyani A', 'akk.mca@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('CA004', 'CA', 'Dr. Ilayaraja N', 'nir.mca@psgtech.ac.in', 'Assistant Professor'),
('CA005', 'CA', 'Dr. Sankar A', 'dras.mca@psgtech.ac.in', 'Professor'),
('CA006', 'CA', 'Dr. Geetha N', 'sng.mca@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('CA007', 'CA', 'Dr. Bhama S', 'sba.mca@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('CA008', 'CA', 'Dr. Subathra M', 'msa.mca@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('CA009', 'CA', 'Mr. Sundar C', 'csr.mca@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('CA010', 'CA', 'Dr. Umarani V', 'vur.mca@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('CA011', 'CA', 'Mrs. Gowri Thangam J', 'jgt.mca@psgtech.ac.in', 'Assistant Professor(Sr. Gr.)'),
('CA012', 'CA', 'Mrs. Gayathri K', 'kgi.mca@psgtech.ac.in', 'Assistant Professor(Sr. Gr.)'),
('CA013', 'CA', 'Mrs. Manoranjitham A', 'amr.mca@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('CA014', 'CA', 'Dr. Venkatesan V', 'vvn.mca@psgtech.ac.in', 'Assistant Professor(Sl. Gr.)'),
('CA015', 'CA', 'Mrs. Rajeswari N', 'nrj.mca@psgtech.ac.in', 'Assistant Professor(Sr. Gr.)'),
('CA016', 'CA', 'Mrs. Aarthi Mai A S', 'asa.mca@psgtech.ac.in', 'Assistant Professor'),
('CA017', 'CA', 'Dr. Bhuvaneswari A', 'abh.mca@psgtech.ac.in', 'Assistant Professor');

INSERT INTO faculty_allocation (course_id, faculty_id) VALUES
('23MX36', 'CA007'), -- Bhama S
('23MX37', 'CA006'), -- Geetha N
('23MX16', 'CA006'), -- Geetha N
('23MX16', 'CA010'), -- Umarani V
('23MX17', 'CA012'), -- Gayathri K
('23MX18', 'CA009'), -- Sundar C
('23MX31', 'CA007'), -- Bhama S
('23MX11', 'CA005'), -- Shankar A
('23MX11', 'CA009'), -- Sundar C
('23MX12', 'CA006'), -- Geetha N
('23MX12', 'CA010'), -- Umarani V
('23MX14', 'CA004'), -- Ilayaraja N
('23MX14', 'CA006'), -- Geetha N
('23MX13', 'CA001'), -- Chitra A
('23MX13', 'CA012'), -- Gayathri K
('23MX15', 'CA003'), -- Kalyani A
('23MX19', 'CA004'); -- Ilayaraja N

use timetable_db;

INSERT INTO course (course_id, course_name, course_type, hours_per_week, programme_id, semester_number)
VALUES 
('23MX53', 'DS', 'Core', 3, 'MCA', 5),
('23MX54', 'DBMS', 'Core', 4, 'MCA', 5),
('23MX55', 'WT', 'Core', 3, 'MCA', 5),
('23MX56', 'C Lab', 'Lab', 4, 'MCA', 5),
('23MX57', 'DS Lab', 'Lab', 4, 'MCA', 5),
('23MX58', 'WAD Lab', 'Lab', 4, 'MCA', 5),
('23MX59', 'TWM', 'Core', 1, 'MCA', 5),
('23MX66', 'JAVA Lab', 'Lab', 4, 'MCA', 6),
('23MX71', 'CC', 'Core', 3, 'MCA', 7),
('23MX76', 'CC Lab', 'Lab', 4, 'MCA', 7),
('23MX77', 'Mini Project Lab', 'Lab', 4, 'MCA', 7),
('23MXCA', 'Entrepreneurship', 'Elective', 3),
('23MXCB', 'PMBS', 'Elective', 3);

INSERT INTO course (course_id, course_name, course_type, hours_per_week, programme_id)
VALUES 
('23MXCA', 'Entrepreneurship', 'Elective', 3, 'MCA'),
('23MXCB', 'PMBS', 'Elective', 3, 'MCA');

CREATE TABLE Elective_allocation (
    course_id VARCHAR(20), -- Assuming course_id is a VARCHAR, adjust data type as needed
    programme_id VARCHAR(20), -- Assuming programme_id is a VARCHAR, adjust data type as needed
    elective_no INT,
    PRIMARY KEY (course_id, programme_id, elective_no),
    FOREIGN KEY (course_id) REFERENCES Course(course_id), -- Adjust the referenced table and column if necessary
    FOREIGN KEY (programme_id) REFERENCES Programme(programme_id) -- Adjust the referenced table and column if necessary
);
