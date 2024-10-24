import mysql.connector
from db_connection import create_db_connection

# Function to get courses from the 'course' table dynamically based on programme and semester
def get_courses(is_odd_semester):
    connection = create_db_connection()
    if connection is None:
        print("Failed to connect to the database.")
        return {}

    try:
        cursor = connection.cursor()

        # Query to fetch all unique programme_ids
        programme_query = "SELECT DISTINCT programme_id FROM course"
        cursor.execute(programme_query)
        programmes = cursor.fetchall()

        # Dictionary to store courses based on programme_id and semester_number
        courses_by_programme = {}

        for programme in programmes:
            programme_id = programme[0]

            # Determine if we're fetching odd or even semesters
            if is_odd_semester:
                semester_filter = "MOD(semester_number, 2) = 1"  # Odd semesters
            else:
                semester_filter = "MOD(semester_number, 2) = 0"  # Even semesters

            # Query to fetch all unique semester_numbers for this programme, filtered by odd or even
            semester_query = f"""
                SELECT DISTINCT semester_number 
                FROM course 
                WHERE programme_id = '{programme_id}' AND {semester_filter}
            """
            cursor.execute(semester_query)
            semesters = cursor.fetchall()

            # Initialize nested dictionary to store courses for each semester
            courses_by_programme[programme_id] = {}

            for semester in semesters:
                semester_number = semester[0]

                # Query to fetch courses for the specific programme and semester
                course_query = f"""
                    SELECT course_id, course_name, course_type, hours_per_week 
                    FROM course 
                    WHERE programme_id = '{programme_id}' AND semester_number = {semester_number}
                """
                cursor.execute(course_query)
                courses = cursor.fetchall()

                # Separate lab and regular courses for this specific programme and semester
                lab_courses = []
                regular_courses = []

                for course in courses:
                    course_id, course_name, course_type, hours_per_week = course

                    # Include hours_per_week along with the course name in the results
                    if course_type == 'Lab':
                        lab_courses.append({
                            'course_id': course_id,
                            'hours_per_week': hours_per_week
                        })
                    elif course_type == 'Core':
                        regular_courses.append({
                            'course_id': course_id,
                            'hours_per_week': hours_per_week
                        })

                # Store lab and regular courses under the respective programme and semester
                courses_by_programme[programme_id][semester_number] = {
                    'lab_courses': lab_courses,
                    'regular_courses': regular_courses
                }

        return courses_by_programme

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Function to get labs grouped by dept_id along with department name and their strength
def get_labs():
    connection = create_db_connection()
    if connection is None:
        print("Failed to connect to the database.")
        return {}

    try:
        cursor = connection.cursor()

        # Query to fetch labs with their corresponding department and strength
        lab_query = """
            SELECT l.lab_id, l.lab_name, l.capacity, d.dept_id, d.dept_name
            FROM labs l
            JOIN department d ON l.dept_id = d.dept_id
        """
        cursor.execute(lab_query)
        labs = cursor.fetchall()

        # Dictionary to store labs grouped by dept_id with department_name
        labs_by_department = {}

        for lab in labs:
            lab_id, lab_name, capacity, dept_id, dept_name = lab

            # Initialize the department if not already in the dictionary
            if dept_id not in labs_by_department:
                labs_by_department[dept_id] = {
                    'labs': []
                }

            # Append the lab information under the correct department
            labs_by_department[dept_id]['labs'].append({
                'lab_id': lab_id,
                'lab_name': lab_name,
                'capacity': capacity
            })

        return labs_by_department

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()


def fetch_num_groups_per_sem(odd_sem=True):
    connection = create_db_connection()
    if connection is None:
        print("Failed to connect to the database.")
        return {}

    # Determine which semesters to fetch (odd or even)
    # semester_filter = "MOD(programme_year, 2) = 1" if odd_sem else "MOD(programme_year, 2) = 0"

    query = f"""
    SELECT p.programme_id, g.programme_year, COUNT(*) AS num_groups
    FROM grouptable g
    JOIN programme p ON g.programme_id = p.programme_id
    GROUP BY p.programme_id, g.programme_year;
    """

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        result = cursor.fetchall()

        # Create a dictionary in the format {'ProgrammeName': {semester: num_groups}}
        num_groups_per_sem = {}
        for row in result:
            programme_name = row['programme_id']
            year = row['programme_year']
            num_groups = row['num_groups']

            # Map years to semesters based on odd_sem=True (1st sem from year1, 3rd sem from year2, etc.)
            if odd_sem:
                semester = 2 * (year - 1) + 1  # Odd semesters: 1, 3, 5, ...
            else:
                semester = 2 * year  # Even semesters: 2, 4, 6, ...

            # Initialize programme dictionary if not already present
            if programme_name not in num_groups_per_sem:
                num_groups_per_sem[programme_name] = {}

            # Add the semester and group count to the programme
            num_groups_per_sem[programme_name][semester] = num_groups

        return num_groups_per_sem

    except mysql.connector.Error as e:
        print(f"Error: {e}")
        return {}

    finally:
        if cursor:
            cursor.close()

# Function to get labs grouped by dept_id along with department name and their strength
def get_classrooms():
    connection = create_db_connection()
    if connection is None:
        print("Failed to connect to the database.")
        return {}

    try:
        cursor = connection.cursor()

        # Query to fetch classrooms with block, floor, and capacity details
        classroom_query = """
            SELECT hall_id, block, floor, capacity
            FROM classrooms
        """
        cursor.execute(classroom_query)
        classrooms = cursor.fetchall()

        # List to store classroom details
        classroom_list = []

        for classroom in classrooms:
            hall_id, block, floor, capacity = classroom

            # Append each classroom's information as a dictionary
            classroom_list.append({
                'hall_id': hall_id,
                'block': block,
                'floor': floor,
                'capacity': capacity
            })

        return classroom_list

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return []
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_department_programme_map():
    connection = create_db_connection()
    if connection is None:
        print("Failed to connect to the database.")
        return {}

    try:
        cursor = connection.cursor()

        # Query to fetch department and programme mappings
        department_programme_query = """
            SELECT dept_id, GROUP_CONCAT(programme_id) AS programme_ids
            FROM programme
            GROUP BY dept_id;
        """
        cursor.execute(department_programme_query)
        department_programmes = cursor.fetchall()

        # Dictionary to store the mapping of dept_id to programme_ids
        department_programme_map = {}

        for row in department_programmes:
            dept_id = row[0]
            programme_ids = row[1].split(',')  # Split the concatenated string into a list

            # Store the result in the dictionary
            department_programme_map[dept_id] = programme_ids

        return department_programme_map

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_groups_by_programme(is_odd_semester):
    connection = create_db_connection()
    if connection is None:
        print("Failed to connect to the database.")
        return {}

    try:
        cursor = connection.cursor()

        # Query to fetch groups along with the programme information
        group_query = """
            SELECT programme_id, year_group, programme_year, group_strength
            FROM groupTable
            ORDER BY programme_id, programme_year, year_group;
        """

        cursor.execute(group_query)
        group_data = cursor.fetchall()

        # Dictionary to store groups by programme and semester in the desired format
        strength_data = {}

        for row in group_data:
            programme_id = row[0]
            year_group = row[1]
            programme_year = row[2]
            group_strength = row[3]

            # Calculate the semester number based on programme_year and is_odd_semester
            if is_odd_semester:
                semester_number = 2 * programme_year - 1  # Odd semester
            else:
                semester_number = 2 * programme_year  # Even semester

            # Initialize the dictionary for the programme if not already done
            if programme_id not in strength_data:
                strength_data[programme_id] = {}

            # Initialize the dictionary for the semester if not already done
            if semester_number not in strength_data[programme_id]:
                strength_data[programme_id][semester_number] = {}

            # Add group and strength to the corresponding semester and programme
            strength_data[programme_id][semester_number][year_group] = group_strength

        return strength_data

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_faculty_allocation_by_course():
    connection = create_db_connection()  # Assuming you have a function to create a DB connection
    if connection is None:
        print("Failed to connect to the database.")
        return {}

    try:
        cursor = connection.cursor()

        # Query to fetch faculty allocations for each course (only faculty_id)
        faculty_query = """
            SELECT course_id, faculty_id
            FROM faculty_allocation
            ORDER BY course_id, faculty_id;
        """

        cursor.execute(faculty_query)
        faculty_data = cursor.fetchall()

        # Dictionary to store faculty IDs by course
        faculty_by_course = {}

        for row in faculty_data:
            course_id = row[0]
            faculty_id = row[1]

            # Initialize the list for the course if not already done
            if course_id not in faculty_by_course:
                faculty_by_course[course_id] = []

            # Append the faculty ID to the course's list
            faculty_by_course[course_id].append(faculty_id)

        return faculty_by_course

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_elective_allocation_by_semester(is_odd_semester=True): 
    connection = create_db_connection()  # Assuming you have a function to create a DB connection
    if connection is None:
        print("Failed to connect to the database.")
        return {}

    try:
        cursor = connection.cursor()

        # Query to fetch electives from odd semesters and group by elective_no and programme_id
        elective_query = """
            SELECT 
                ea.course_id, 
                ea.programme_id, 
                ea.semester_number,  -- Include semester_number
                ea.elective_no,
                ea.strength,
                p.programme_name,
                c.course_name,
                c.hours_per_week,
                fa.faculty_id
            FROM 
                Elective_allocation ea
            JOIN 
                Course c ON ea.course_id = c.course_id
            JOIN 
                Programme p ON ea.programme_id = p.programme_id
            JOIN 
                faculty_allocation fa ON ea.course_id = fa.course_id
            JOIN 
                Faculty f ON fa.faculty_id = f.faculty_id
            WHERE 
                MOD(ea.semester_number, 2) = %s
            ORDER BY 
                ea.programme_id, ea.semester_number, ea.elective_no, ea.course_id;
        """

        # Determine whether we want odd semesters or not
        semester_type = 1 if is_odd_semester else 0

        cursor.execute(elective_query, (semester_type,))
        elective_data = cursor.fetchall()

        # Dictionary to store electives grouped by programme_id and semester_number
        electives_by_programme = {}

        for row in elective_data:
            course_id = row[0]
            programme_id = row[1]
            semester_number = row[2]  # Capture semester_number
            elective_no = row[3]
            strength = row[4]
            programme_name = row[5]
            course_name = row[6]
            hours_per_week = row[7]
            faculty_id = row[8]

            # Initialize the outer dictionary for the programme_id if not already done
            if programme_id not in electives_by_programme:
                electives_by_programme[programme_id] = {}

            # Initialize the inner dictionary for the semester_number if not already done
            if semester_number not in electives_by_programme[programme_id]:
                electives_by_programme[programme_id][semester_number] = {}

            # Initialize the inner dictionary for the elective_no if not already done
            if elective_no not in electives_by_programme[programme_id][semester_number]:
                electives_by_programme[programme_id][semester_number][elective_no] = []

            # Append the course details to the elective_no's list within the programme and semester
            electives_by_programme[programme_id][semester_number][elective_no].append({
                'course_id': course_id,
                'course_name': course_name,
                'hours_per_week': hours_per_week,
                'faculty_id': faculty_id,
                'strength': strength,
            })

        return electives_by_programme

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return {}
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def is_odd_semester_check():
    connection = create_db_connection()  # Assuming you have a function to create a DB connection
    if connection is None:
        print("Failed to connect to the database.")
        return None

    try:
        cursor = connection.cursor()

        # Query to fetch the current semester season
        season_query = """
            SELECT sem_season 
            FROM season 
            LIMIT 1;
        """

        cursor.execute(season_query)
        season_data = cursor.fetchone()

        if season_data is not None:
            sem_season = season_data[0]
            # Return True if the semester season is odd, else False if even
            if sem_season == 'odd':
                return True
            elif sem_season == 'even':
                return False
            else:
                print("No valid semester season found.")
                return None
        else:
            print("No open season found.")
            return None

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def get_dept_classrooms(programme_id):
    connection = create_db_connection()
    if connection is None:
        print("Failed to connect to the database.")
        return None

    try:
        cursor = connection.cursor()

        # Query to get the department and block based on programme_id
        dept_block_query = """
            SELECT d.block 
            FROM programme p
            JOIN department d ON p.dept_id = d.dept_id
            WHERE p.programme_id = %s;
        """

        cursor.execute(dept_block_query, (programme_id,))
        result = cursor.fetchone()

        if result is None:
            print("No block found for the given programme_id.")
            return None

        dept_block = result[0]  # Extract block from the result

        # Query to get all classrooms in that block
        classrooms_query = """
            SELECT hall_id, block, floor, capacity, facility
            FROM classrooms
            WHERE block = %s;
        """

        cursor.execute(classrooms_query, (dept_block,))
        classrooms = cursor.fetchall()

        # Return classrooms data as a list of dictionaries
        classrooms_list = [
            {
                'hall_id': row[0],
                'block': row[1],
                'floor': row[2],
                'capacity': row[3],
                'facility': row[4]
            }
            for row in classrooms
        ]

        return classrooms_list

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

