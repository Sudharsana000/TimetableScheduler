import mysql.connector
from db_connection import create_db_connection

# Function to get courses from the 'course' table dynamically based on programme and semester
def get_courses():
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

            # Query to fetch all unique semester_numbers for this programme
            semester_query = f"SELECT DISTINCT semester_number FROM course WHERE programme_id = '{programme_id}'"
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
