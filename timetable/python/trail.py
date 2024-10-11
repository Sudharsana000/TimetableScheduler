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

def remove_lab_if_classroom_matches(transformed_timetable, lab_availability):
    for day, day_hours in transformed_timetable.items():
        for hour, classrooms in day_hours.items():
            for department, department_labs in lab_availability[day][hour].items():
                for lab in list(department_labs):  # Use a list copy to allow modification
                    if lab["lab_id"] in classrooms:
                        # print(f"Removing lab '{lab}' from availability for {day} at hour {hour} in department {department}")
                        lab_availability[day][hour][department].remove(lab)

    return lab_availability

def add_lab_courses(all_timetables, programme_timelines, programme_data, faculties, labs, department_programme_map, hours_per_day):
    print(labs)
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
            for department, semesters in programme_data.items():
                for sem in semesters.keys():
                    for course in programme_data[department][sem]['lab_courses']:
                        course_id = course['course_id']
                        if course_id in faculties:
                            faculty_availability[day][hour][course_id] = list(faculties[course_id])

    # Create a new dictionary to store the transformed timetable format
    transformed_timetable = {}

    # Loop through the timetable dictionary and transform the data into the desired format
    for program, year_data in all_timetables.items():
        for year, groups in year_data.items():
            for group, schedule in groups.items():
                for day, hours in schedule.items():
                    # Initialize the day in transformed_timetable if not already done
                    if day not in transformed_timetable:
                        transformed_timetable[day] = {}
                    
                    for hour, details in hours.items():
                        classroom = details.get('Classroom')
                        
                        # Initialize the list for the hour if not already done
                        if hour not in transformed_timetable[day]:
                            transformed_timetable[day][hour] = []
                        
                        # Append the classroom if it's not None
                        if classroom:
                            transformed_timetable[day][hour].append(classroom)

    lab_availability = remove_lab_if_classroom_matches(transformed_timetable, lab_availability)

    extracted_timetable = {}
    for programme, semesters in all_timetables.items():
        for sem, groups in semesters.items():
            for group, days in groups.items():
                for day, hours in days.items():
                    for hour, session in hours.items():
                        faculty = session.get('Faculty')
                        if faculty:
                            if day not in extracted_timetable:
                                extracted_timetable[day] = {}
                            if hour not in extracted_timetable[day]:
                                extracted_timetable[day][hour] = []
                            extracted_timetable[day][hour].append(faculty)

    for day, hours in extracted_timetable.items():
        for hour, faculties in hours.items():
            if day in faculty_availability and hour in faculty_availability[day]:
                for course, available_faculties in faculty_availability[day][hour].items():
                    i = 0
                    while i < len(available_faculties):
                        faculty = available_faculties[i]
                        if faculty in faculties:
                            available_faculties.remove(faculty)
                        else:
                            i += 1

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
            # print(f"No department found for programme: {programme}")
            continue

        for sem, class_obj in sem_timelines.items():
            lab_courses = programme_data[programme][sem]['lab_courses']

            for course in lab_courses:
                course_id = course['course_id']
                unallocated_classes_per_week = course['hours_per_week'] // 2  # Labs take 2-hour blocks

                available_days = list(class_obj.keys())

                while unallocated_classes_per_week > 0:
                    # Find available day-hour slots for this semester and course
                    available_hours = [
                        (d, hour)
                        for d, hour in day_hour_combinations
                        if d in available_days
                        and class_obj[d][hour]["Course"] is None and class_obj[d][hour + 1]["Course"] is None  # Check both hours for lab
                        and lab_availability[d][hour][department] and lab_availability[d][hour + 1][department]  # Labs available for both hours
                        # Ensure selected faculty is available (if already selected)
                        and (
                            course_id not in selected_faculties or
                            selected_faculties[course_id] in faculty_availability[d][hour][course_id] and 
                            selected_faculties[course_id] in faculty_availability[d][hour + 1][course_id]
                        )
                        # Check if any faculty is available
                        and course_id in faculty_availability[d][hour] and faculty_availability[d][hour][course_id]  
                        and course_id in faculty_availability[d][hour + 1] and faculty_availability[d][hour + 1][course_id]
                    ]

                    if not available_hours:
                        # print(f"No available slots for lab course '{course_id}' in semester {sem} for department {department}")
                        break

                    # Choose a random available day-hour slot
                    random_available_hour = random.choice(available_hours)
                    day, hour = random_available_hour

                    # Select lab for this department
                    selected_lab = lab_availability[day][hour][department].pop(0)

                    # Select faculty for this course
                    if course_id not in selected_faculties:
                        # If no faculty has been selected yet for this course, assign a new one
                        selected_faculty = faculty_availability[day][hour][course_id].pop(0)
                        selected_faculties[course_id] = selected_faculty
                    else:
                        # Use the already selected faculty for this course
                        selected_faculty = selected_faculties[course_id]

                    # Assign lab course to both hour slots
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

                    # Mark this day as used for lab allocation
                    available_days.remove(day)

                    # Decrement the unallocated lab hours per week
                    unallocated_classes_per_week -= 1

def remove_hall_if_classroom_matches(transformed_timetable, classroom_availability):
    for day, day_hours in transformed_timetable.items():
        for hour, classrooms in day_hours.items():
            for room in classroom_availability[day][hour]:
                if room['hall_id'] in transformed_timetable[day][hour]:
                    classroom_availability[day][hour].remove(room)

    return classroom_availability

def add_parallel_electives(all_timetables, group_timelines, faculties, classrooms, hours_per_day, elective_data=None):
    # Initialize classroom availability for each day and hour
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in list(list(group_timelines.values())[0].keys())  # Get day list from any timetable
    }

    # Initialize faculty availability for elective courses
    faculty_availability = {}
    for day in classroom_availability.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            # Loop through electives to set the faculty availability
            for programme, semesters in elective_data.items():
                for sem, elective_groups in semesters.items():
                    for elective_num, elective_courses in elective_groups.items():
                        for course in elective_courses:
                            course_id = course['course_id']
                            if course_id in faculties:
                                faculty_availability[day][hour][course_id] = list(faculties[course_id])

    # Extract the current timetable allocations to filter out occupied classrooms and faculties
    for programme, semesters in all_timetables.items():
        for semester, groups in semesters.items():
            for group, days in groups.items():
                for day, hours in days.items():
                    for hour, details in hours.items():
                        # Remove classrooms that are already occupied
                        classroom = details.get('Classroom')
                        if classroom and day in classroom_availability and hour in classroom_availability[day]:
                            classroom_availability[day][hour] = [hall for hall in classroom_availability[day][hour] if hall['hall_id'] != classroom]
                        # Remove faculties that are already occupied
                        faculty = details.get('Faculty')
                        if faculty:
                            for course_id, available_faculties in faculty_availability[day][hour].items():
                                if faculty in available_faculties:
                                    faculty_availability[day][hour][course_id].remove(faculty)

    # Track day-hour combinations for elective allocation
    day_hour_combinations = [
        (day, int(hour))
        for day in classroom_availability.keys()
        for hour in range(1, hours_per_day + 1)
    ]

    # Allocate electives dynamically for each programme and semester
    for programme, semesters in elective_data.items():
        for sem, elective_groups in semesters.items():
            # Maintain a set of courses allocated per day for each group
            courses_allocated_per_day = {
                group: {day: set() for day in classroom_availability.keys()}
                for group in all_timetables[programme][sem]
            }

            for elective_num, elective_courses in elective_groups.items():
                # Allocate parallel electives for all groups in the semester **at the same time slot**
                while any(course['hours_per_week'] > 0 for course in elective_courses):
                    # Find available time slots for all groups
                    available_hours = [
                        (d, hour)
                        for d, hour in day_hour_combinations
                        if classroom_availability[d][hour]
                        # Ensure all electives in the group have available faculty and classrooms
                        and all(
                            course['course_id'] in faculty_availability[d][hour] 
                            and faculty_availability[d][hour][course['course_id']]
                            for course in elective_courses
                        )
                        # Ensure no group in the semester is already scheduled for that hour
                        and all(
                            group in all_timetables[programme][sem]
                            and all_timetables[programme][sem][group][d][hour]['Course'] is None
                            # Ensure neither elective course is scheduled more than once per day
                            and not any(
                                course['course_id'] in courses_allocated_per_day[group][d]
                                for course in elective_courses
                            )
                            for group in all_timetables[programme][sem]
                        )
                    ]

                    if not available_hours:
                        # No available slots for electives
                        break

                    # Choose a random available day-hour slot
                    day, hour = random.choice(available_hours)

                    # Allocate the elective courses for **all groups** in the semester at the same day and hour
                    assigned_classrooms = []
                    assigned_faculties = []
                    assigned_courses = []

                    for course in elective_courses:
                        course_id = course['course_id']
                        if course['hours_per_week'] > 0:
                            # Check if faculty is still available before popping
                            if faculty_availability[day][hour][course_id]:
                                selected_classroom = classroom_availability[day][hour].pop(0)
                                selected_faculty = faculty_availability[day][hour][course_id].pop(0)

                                assigned_classrooms.append(selected_classroom['hall_id'])
                                assigned_faculties.append(selected_faculty)
                                assigned_courses.append(course_id)

                                # Decrement the unallocated hours for the course
                                course['hours_per_week'] -= 1
                            else:
                                # Skip if no faculty is available
                                continue

                    # Assign the elective course to the same time slot for all groups in this semester
                    for group in all_timetables[programme][sem]:
                        if assigned_classrooms and assigned_faculties:
                            all_timetables[programme][sem][group][day][hour] = {
                                "Classroom": assigned_classrooms,
                                "Faculty": assigned_faculties,
                                "Course": assigned_courses
                            }

                            # Mark the course as allocated for that group on that day
                            for course_id in assigned_courses:
                                courses_allocated_per_day[group][day].add(course_id)

                    # Remove the selected day-hour combination from future allocation
                    day_hour_combinations.remove((day, hour))

def add_regular_classes(all_timetables, programme_timelines, programme_data, faculties, classrooms, hours_per_day, existing_classes=None):
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

    extracted_timetable = {}

    for programme, semesters in all_timetables.items():
        for semester, groups in semesters.items():
            for group, days in groups.items():
                for day, hours in days.items():
                    for hour, details in hours.items():
                        classroom = details.get('Classroom')

                        # If classroom exists
                        if classroom:
                            if day not in extracted_timetable:
                                extracted_timetable[day] = {}
                            if hour not in extracted_timetable[day]:
                                extracted_timetable[day][hour] = []

                            # Check if classroom is a list (array) and flatten it
                            if isinstance(classroom, list):
                                extracted_timetable[day][hour].extend(classroom)  # Flatten the list and append elements
                            else:
                                extracted_timetable[day][hour].append(classroom)  # Append the single classroom

    for day, hours in extracted_timetable.items():
        for hour, classrooms in hours.items():
            if day in classroom_availability and hour in classroom_availability[day]:
                i = 0
                while i < len(classroom_availability[day][hour]):
                    hall = classroom_availability[day][hour][i]
                    if hall['hall_id'] in classrooms:
                        classroom_availability[day][hour].remove(hall)
                    else:
                        i += 1

    extracted_timetable = {}
    for programme, semesters in all_timetables.items():
        for sem, groups in semesters.items():
            for group, days in groups.items():
                for day, hours in days.items():
                    for hour, session in hours.items():
                        faculty = session.get('Faculty')
                        if faculty:
                            if day not in extracted_timetable:
                                extracted_timetable[day] = {}
                            if hour not in extracted_timetable[day]:
                                extracted_timetable[day][hour] = []
                            extracted_timetable[day][hour].append(faculty)

    for day, hours in extracted_timetable.items():
        for hour, faculties in hours.items():
            if day in faculty_availability and hour in faculty_availability[day]:
                for course, available_faculties in faculty_availability[day][hour].items():
                    i = 0
                    while i < len(available_faculties):
                        faculty = available_faculties[i]
                        if faculty in faculties:
                            available_faculties.remove(faculty)
                        else:
                            i += 1

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
                        # Ensure the course hasn't been scheduled already on the current day
                        and all(class_obj[d][h]["Course"] != course_id for h in range(1, hours_per_day + 1))
                        # Check if the faculty has been selected already for the course-semester
                        and (
                            (course_id, sem) not in selected_faculties or
                            # If selected, ensure the same faculty is available for this time slot
                            selected_faculties[(course_id, sem)] in faculty_availability[d][hour][course_id]
                        )
                        # If no faculty has been selected, check any faculty is available
                        and course_id in faculty_availability[d][hour]  
                        and faculty_availability[d][hour][course_id]  # Faculty not already allocated
                    ]

                    if not available_hours:
                        # No available slots for this course in the current semester
                        # print("Unable to allocate class for ",course_id)
                        break

                    # Choose a random available day-hour slot
                    day, hour = random.choice(available_hours)

                    # Select a classroom for this course (per semester)
                    selected_classroom = classroom_availability[day][hour].pop(0)
                    classroom_info = f"{selected_classroom['hall_id']}"

                    # Select faculty for this course and semester (per semester)
                    if (course_id, sem) not in selected_faculties:
                        # If no faculty has been selected yet for this course-semester
                        selected_faculty = faculty_availability[day][hour][course_id].pop(0)
                        selected_faculties[(course_id, sem)] = selected_faculty
                    else:
                        # If the faculty has already been selected, use the same faculty
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

elective_data = get_elective_allocation_by_semester()

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
def add_courses_for_groups(programme_timelines, programme_data, faculties, classrooms, labs, hours_per_day, elective_data, department_programme_map):
    for programme, sem_timelines in programme_timelines.items():
        for sem, group_timelines in sem_timelines.items():
            
            # Step 1: Allocate lab courses for each group separately
            for group, class_obj in group_timelines.items():
                add_lab_courses(
                    programme_timelines, 
                    {programme: {sem: class_obj}}, 
                    programme_data, 
                    faculties, 
                    labs, 
                    department_programme_map, 
                    hours_per_day
                )
                
            # Step 2: Allocate electives for all groups in the semester together
            add_parallel_electives(
                programme_timelines,  # Pass all programme timelines as electives need all groups
                group_timelines,
                faculties,
                classrooms,
                hours_per_day,
                elective_data
            )

            # Step 3: Allocate regular classes for each group separately after electives
            for group, class_obj in group_timelines.items():
                add_regular_classes(
                    programme_timelines, 
                    {programme: {sem: class_obj}}, 
                    programme_data, 
                    faculties, 
                    classrooms, 
                    hours_per_day
                )

# Call the updated function to allocate courses for all groups
add_courses_for_groups(programme_timelines, courses_by_programme, faculties, classrooms, labs, hours_per_day, elective_data, department_programme_map)

# json_output = json.dumps(programme_timelines)
# print(json_output)

# def compare_allocations(all_timetable):
#     faculty_conflicts = {}
#     classroom_conflicts = {}

#     # Loop through all programs, semesters, and groups to check for conflicts
#     for programme, semesters in all_timetable.items():
#         for sem, groups in semesters.items():
#             for group, timetable in groups.items():
#                 for day, hours in timetable.items():
#                     for hour, session in hours.items():
#                         faculty = session.get('Faculty')
#                         classroom = session.get('Classroom')
#                         course = session.get('Course')

#                         # Check for faculty conflicts
#                         if faculty:
#                             key = (day, hour, faculty)
#                             if key not in faculty_conflicts:
#                                 faculty_conflicts[key] = []
#                             faculty_conflicts[key].append((programme, sem, group, course))

#                         # Check for classroom conflicts
#                         if classroom:
#                             key = (day, hour, classroom)
#                             if key not in classroom_conflicts:
#                                 classroom_conflicts[key] = []
#                             classroom_conflicts[key].append((programme, sem, group, course))

#     # Report conflicts
#     print("Faculty Allocation Conflicts:")
#     for key, allocations in faculty_conflicts.items():
#         if len(allocations) > 1:
#             day, hour, faculty = key
#             print(f"Faculty {faculty} is allocated multiple times on {day}, Hour {hour}:")
#             for allocation in allocations:
#                 print(f"  -> Programme: {allocation[0]}, Semester: {allocation[1]}, Group: {allocation[2]}, Course: {allocation[3]}")
    
#     print("\nClassroom Allocation Conflicts:")
#     for key, allocations in classroom_conflicts.items():
#         if len(allocations) > 1:
#             day, hour, classroom = key
#             print(f"Classroom {classroom} is allocated multiple times on {day}, Hour {hour}:")
#             for allocation in allocations:
#                 print(f"  -> Programme: {allocation[0]}, Semester: {allocation[1]}, Group: {allocation[2]}, Course: {allocation[3]}")

# # Run the comparison
# compare_allocations(programme_timelines)
