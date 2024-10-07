import random
import json
from queries import get_courses, get_department_programme_map, get_labs, get_classrooms, get_groups_by_programme, get_faculty_allocation_by_course, get_elective_allocation_by_semester

def structure_timetable_for_groups(days, hours_per_day, num_groups):
    timetable = {}
    
    # Create a timetable for each group
    for group in range(1, num_groups + 1):
        timetable[f'Group_{group}'] = {}
        for day in days:
            timetable[f'Group_{group}'][day] = {}
            for hour in range(1, hours_per_day + 1):
                timetable[f'Group_{group}'][day][hour] = {
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

def add_elective_courses(elective_data, programme_timelines, classrooms, hours_per_day):
    # Track available classrooms for each day and hour
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in list(programme_timelines.values())[0].keys()  # Use any class timetable to get day list
    }
    
    # Track available faculties for each elective course
    faculty_availability = {}
    selected_faculties = {}  # Track selected faculties for each elective

    for day in classroom_availability.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            for programme, sem_data in elective_data.items():
                for sem, elective_groups in sem_data.items():
                    for elective_num, electives in elective_groups.items():
                        for course in electives:
                            course_id = course['course_id']
                            faculty_availability[day][hour][course_id] = list([course['faculty_id']])

    # Generate day-hour combinations
    day_hour_combinations = [
        (day, int(hour))
        for day in classroom_availability.keys()
        for hour in classroom_availability[day].keys()
    ]

    # Loop through the electives and allocate them
    for programme, sem_data in elective_data.items():
        for sem, elective_groups in sem_data.items():
            class_timetables = programme_timelines[programme][sem]

            for elective_num, electives in elective_groups.items():
                unallocated_classes_per_week = electives[0]['hours_per_week']
                available_days = list(class_timetables.keys())

                while unallocated_classes_per_week > 0:
                    # Find available day-hour slots for all groups
                    available_hours = [
                        (d, hour)
                        for d, hour in day_hour_combinations
                        if d in available_days and classroom_availability[d][hour]
                        and all(course['course_id'] in faculty_availability[d][hour] for course in electives)
                    ]

                    if not available_hours:
                        print(f"No available slots for electives in semester {sem}, elective group {elective_num}.")
                        break

                    # Choose a random available time slot
                    day, hour = random.choice(available_hours)

                    # Assign electives to the same time slot for different classrooms
                    selected_classrooms = []
                    for course in electives:
                        selected_classroom = classroom_availability[day][hour].pop(0)
                        selected_classrooms.append(selected_classroom)
                        course_id = course['course_id']

                        if course_id not in selected_faculties:
                            selected_faculty = faculty_availability[day][hour][course_id].pop(0)
                            selected_faculties[course_id] = selected_faculty
                        else:
                            selected_faculty = selected_faculties[course_id]

                        # Assign the course to the class timetable
                        for group in class_timetables:
                            class_timetables[group][day][hour] = {
                                "Classroom": selected_classroom['hall_id'],
                                "Faculty": selected_faculty,
                                "Course": course_id
                            }

                    # Decrement the unallocated classes count
                    unallocated_classes_per_week -= 1

                    # Remove the selected day-hour combination to prevent further allocation
                    day_hour_combinations.remove((day, hour))

def add_regular_classes(programme_timelines, programme_data, faculties, classrooms, hours_per_day, existing_classes=None):
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
                        # print(f"No available slots for course '{course_id}' in semester {sem} for programme {programme}")
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
courses_by_programme = get_courses(is_odd_semester)  # This now contains multiple departments

num_groups_per_sem = {1: 2, 3: 2}  # Semester 1 and 3 have 2 groups each

programme_timelines = {
    programme: {
        sem: structure_timetable_for_groups(days, hours_per_day, num_groups_per_sem.get(sem, 1))
        for sem in semesters.keys()
    }
    for programme, semesters in courses_by_programme.items()
}

# Updated course allocation function to handle multiple groups
def add_courses_for_groups(programme_timelines, programme_data, faculties, classrooms, hours_per_day):
    for programme, sem_timelines in programme_timelines.items():
        for sem, group_timelines in sem_timelines.items():
            for group, class_obj in group_timelines.items():
                add_lab_courses({programme: {sem: class_obj}}, programme_data, faculties, labs, department_programme_map, hours_per_day)
                add_regular_classes({programme: {sem: class_obj}}, programme_data, faculties, classrooms, hours_per_day)

# Call the updated function to allocate courses for all groups
add_courses_for_groups(programme_timelines, courses_by_programme, faculties, classrooms, hours_per_day)

json_output = json.dumps(programme_timelines)
print(json_output)
