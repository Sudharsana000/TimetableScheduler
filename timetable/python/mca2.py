import random
import json
from queries import get_courses, get_department_programme_map, get_labs, get_classrooms, get_groups_by_programme, get_faculty_allocation_by_course

def structure_timetable(days, hours_per_day):
    timetable = {}
    
    for day in days:
        timetable[day] = {}
        for hour in range(1, hours_per_day + 1):
            timetable[day][hour] = {
                "Classroom": None,
                "Faculty": None,
                "Course": None
            }

    return timetable

def add_lab_courses(programme_timelines, programme_data, faculties, labs, department_programme_map, hours_per_day):
    # Initialize availability trackers for labs and faculties for each department
    lab_availability = {
        day: {hour: {} for hour in range(1, hours_per_day + 1)}
        for day in list(list(programme_timelines.values())[0].values())[0].keys()  # Use any class timetable to get day list
    }

    faculty_availability = {}
    selected_faculties = {}  # Track the selected faculty for each course

    # Prepare lab availability by department
    for department, department_labs in labs.items():
        for day in lab_availability.keys():
            for hour in range(1, hours_per_day + 1):
                lab_availability[day][hour][department] = list(department_labs['labs'])

    for day in lab_availability.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}

            # Loop through all departments and their respective semesters
            for department, semesters in programme_data.items():
                for sem in semesters.keys():
                    for course in programme_data[department][sem]['lab_courses']:
                        course_id = course['course_id']
                        if course_id in faculties:
                            faculty_availability[day][hour][course_id] = list(faculties[course_id])

    # Track day-hour combinations avoiding conflicts
    day_hour_combinations = [
        (day, int(hour))
        for day in lab_availability.keys()
        for hour in lab_availability[day].keys()
        if int(hour) % 2 == 1 and int(hour) != hours_per_day  # Ensure lab blocks (2-hour slots)
    ]

    for programme, sem_timelines in programme_timelines.items():
        # Find the department for the current programme
        department = next((dept for dept, programmes in department_programme_map.items() if programme in programmes), None)
        if department is None:
            print(f"No department found for programme: {programme}")
            continue

        for sem, class_obj in sem_timelines.items():
            lab_courses = programme_data[programme][sem]['lab_courses']

            for course in lab_courses:
                course_id = course['course_id']
                unallocated_classes_per_week = course['hours_per_week'] // 2  # Labs take 2-hour blocks

                available_days = list(class_obj.keys())

                while unallocated_classes_per_week > 0:
                    available_hours = [
                        (d, hour)
                        for d, hour in day_hour_combinations
                        if d in available_days
                        and class_obj[d][hour]["Course"] is None and class_obj[d][hour + 1]["Course"] is None
                        and lab_availability[d][hour][department] and lab_availability[d][hour + 1][department]
                        and course_id in faculty_availability[d][hour] and faculty_availability[d][hour][course_id]
                        and course_id in faculty_availability[d][hour + 1] and faculty_availability[d][hour + 1][course_id]
                    ]

                    if not available_hours:
                        print(f"No available slots for lab course '{course_id}' in semester {sem} for department {department}")
                        break

                    random_available_hour = random.choice(available_hours)
                    day, hour = random_available_hour

                    # Select lab for this department
                    selected_lab = lab_availability[day][hour][department].pop(0)
                    if course_id not in selected_faculties:
                        selected_faculty = faculty_availability[day][hour][course_id].pop(0)
                        selected_faculties[course_id] = selected_faculty
                    else:
                        selected_faculty = selected_faculties[course_id]

                    # Assign lab to the class timetable
                    class_obj[day][hour] = {
                        "Classroom": selected_lab['lab_id'],
                        "Faculty": selected_faculty,
                        "Course": course_id
                    }

                    class_obj[day][hour + 1] = {
                        "Classroom": selected_lab['lab_id'],
                        "Faculty": selected_faculty,
                        "Course": course_id
                    }

                    # Remove faculty availability for both hours
                    if not faculty_availability[day][hour][course_id]:
                        del faculty_availability[day][hour][course_id]
                    if not faculty_availability[day][hour + 1][course_id]:
                        del faculty_availability[day][hour + 1][course_id]

                    available_days.remove(day)
                    unallocated_classes_per_week -= 1

def add_regular_classes(programme_timelines, programme_data, faculties, classrooms, hours_per_day, existing_classes=None):
    # Initialize availability trackers for classrooms and faculties per semester
    print(programme_timelines)
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in list(list(programme_timelines.values())[0].values())[0].keys()  # Use any class timetable to get day list
    }

    faculty_availability = {}
    selected_faculties = {}  # Track the selected faculty for each course and semester

    # Prepare classroom availability for regular classes
    for day in classroom_availability.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}

            # Loop through all programmes and their respective semesters
            for department, semesters in programme_data.items():
                for sem in semesters.keys():
                    for course in programme_data[department][sem]['regular_courses']:
                        course_id = course['course_id']
                        if course_id in faculties:
                            faculty_availability[day][hour][course_id] = list(faculties[course_id])

    # Check and remove availability based on existing lab classes or already allocated courses
    if existing_classes:
        for existing_class in existing_classes:
            for day in existing_class:
                for hour in existing_class[day]:
                    # Classroom conflict check for all timetables
                    existing_classroom = existing_class[day][hour]["Classroom"]
                    if existing_classroom:
                        if isinstance(existing_classroom, list):
                            for classroom in existing_classroom:
                                if classroom in classroom_availability[day][hour]:
                                    classroom_availability[day][hour].remove(classroom)
                        else:
                            if existing_classroom in classroom_availability[day][hour]:
                                classroom_availability[day][hour].remove(existing_classroom)

                    # Faculty conflict check for all timetables
                    existing_faculty = existing_class[day][hour]["Faculty"]
                    if existing_faculty:
                        if isinstance(existing_faculty, list):
                            # If faculty is a list, remove all faculties in the list from availability
                            for faculty in existing_faculty:
                                for course in faculty_availability[day][hour]:
                                    if faculty in faculty_availability[day][hour][course]:
                                        faculty_availability[day][hour][course].remove(faculty)
                        else:
                            # If it's a single faculty, remove it from availability
                            for course in faculty_availability[day][hour]:
                                if existing_faculty in faculty_availability[day][hour][course]:
                                    faculty_availability[day][hour][course].remove(existing_faculty)

    # Track day-hour combinations for regular class allocation (this is no longer removed globally)
    day_hour_combinations = [
        (day, int(hour))
        for day in classroom_availability.keys()
        for hour in range(1, hours_per_day + 1)
    ]

    # Allocate classes for each semester in parallel
    for programme, sem_timelines in programme_timelines.items():
        for sem, class_obj in sem_timelines.items():
            regular_courses = programme_data[programme][sem]['regular_courses']

            for course in regular_courses:
                course_id = course['course_id']
                unallocated_classes_per_week = course['hours_per_week']

                while unallocated_classes_per_week > 0:
                    # Find available day-hour slots for this semester and course
                    available_hours = [
                        (d, hour)
                        for d, hour in day_hour_combinations
                        if class_obj[d][hour]["Course"] is None  # Check if slot is empty for this semester
                        and classroom_availability[d][hour]  # Classroom available
                        and course_id in faculty_availability[d][hour]  # Faculty available
                        and faculty_availability[d][hour][course_id]  # Faculty not already allocated
                    ]

                    if not available_hours:
                        # No available slots for this course in the current semester
                        print(f"No available slots for course '{course_id}' in semester {sem} for programme {programme}")
                        break

                    # Choose a random available day-hour slot
                    day, hour = random.choice(available_hours)

                    # Select a classroom for this course (per semester)
                    selected_classroom = classroom_availability[day][hour].pop(0)
                    classroom_info = f"{selected_classroom['hall_id']}"

                    # Select faculty for this course and semester (per semester)
                    if (course_id, sem) not in selected_faculties:
                        selected_faculty = faculty_availability[day][hour][course_id].pop(0)
                        selected_faculties[(course_id, sem)] = selected_faculty
                    else:
                        selected_faculty = selected_faculties[(course_id, sem)]

                    # Assign regular course to the class timetable
                    class_obj[day][hour] = {
                        "Classroom": classroom_info,
                        "Faculty": selected_faculty,
                        "Course": course_id
                    }

                    # Remove faculty from availability once allocated
                    if not faculty_availability[day][hour][course_id]:
                        del faculty_availability[day][hour][course_id]

                    # Decrement the unallocated count
                    unallocated_classes_per_week -= 1


# Main code to generate timetables for all departments and their respective semesters
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
labs = get_labs()
classrooms = get_classrooms()
is_odd_semester = True

department_programme_map = get_department_programme_map()

faculties = get_faculty_allocation_by_course()

hours_per_day = 7

# Example: Get data from the database
# courses_by_programme = get_courses(is_odd_semester)  # This now contains multiple departments

courses_by_programme = {'MCA': {1: {'lab_courses': [{'course_id': '23MX16', 'hours_per_week': 4}, 
                    {'course_id': '23MX17', 'hours_per_week': 4}, {'course_id': '23MX18', 'hours_per_week': 4}], 
                    'regular_courses': [{'course_id': '23MX11', 'hours_per_week': 4}, 
                                        {'course_id': '23MX12', 'hours_per_week': 3}, 
                                        {'course_id': '23MX13', 'hours_per_week': 3}, 
                                        {'course_id': '23MX14', 'hours_per_week': 4}, 
                                        {'course_id': '23MX15', 'hours_per_week': 3}, 
                                        {'course_id': '23MX19', 'hours_per_week': 1}]}, 
                    2: {'lab_courses': [{'course_id': '23MX16', 'hours_per_week': 4}, 
                    {'course_id': '23MX17', 'hours_per_week': 4}, {'course_id': '23MX18', 'hours_per_week': 4}], 
                    'regular_courses': [{'course_id': '23MX11', 'hours_per_week': 4}, 
                                        {'course_id': '23MX12', 'hours_per_week': 3}, 
                                        {'course_id': '23MX13', 'hours_per_week': 3}, 
                                        {'course_id': '23MX14', 'hours_per_week': 4}, 
                                        {'course_id': '23MX15', 'hours_per_week': 3}, 
                                        {'course_id': '23MX19', 'hours_per_week': 1}]},
                                        3: {'lab_courses': [{'course_id': '23MX36', 'hours_per_week': 4},
                                        {'course_id': '23MX37', 'hours_per_week': 4}], 
                                        'regular_courses': [{'course_id': '23MX31', 'hours_per_week': 3}]},
                                        4: {'lab_courses': [{'course_id': '23MX36', 'hours_per_week': 4},
                                        {'course_id': '23MX37', 'hours_per_week': 4}], 
                                        'regular_courses': [{'course_id': '23MX31', 'hours_per_week': 3}]}}}


# Dynamically generate timetables for all departments and their respective semesters
programme_timelines = {
    programme: {
        sem: structure_timetable(days, hours_per_day)
        for sem in semesters.keys()
    }
    for programme, semesters in courses_by_programme.items()
}

# Add lab courses for all departments and their respective semesters
add_lab_courses(programme_timelines, courses_by_programme, faculties, labs, department_programme_map, hours_per_day)
add_regular_classes(programme_timelines, courses_by_programme, faculties, classrooms, hours_per_day)


# # Output the timetable for all departments and semesters as a JSON string

json_output = json.dumps(programme_timelines)
print(json_output)
# groups = get_groups_by_programme(is_odd_semester)
# print(groups)