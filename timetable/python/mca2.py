import random
import json
from queries import get_courses, get_department_programme_map, get_labs, get_classrooms, get_groups_by_programme, get_faculty_allocation_by_course, get_elective_allocation_by_semester, fetch_num_groups_per_sem, is_odd_semester_check, get_dept_classrooms
from cost_computation import compute_costs_for_single_timetable
import copy


def structure_timetable_for_groups(days, hours_per_day, num_groups):
    timetable = {}
    
    # Create a timetable for each group
    for group in range(1, num_groups + 1):
        timetable[f'G{group}'] = {}
        for day in days:
            timetable[f'G{group}'][day] = {}
            for hour in range(1, hours_per_day + 1):
                timetable[f'G{group}'][day][hour] = {
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

def add_lab_courses(all_timetables, programme_timelines, programme_data, faculties, labs, department_programme_map, strength_data, hours_per_day):
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

    # Transform timetable to extract classroom usage for removing conflicting labs
    transformed_timetable = {}
    for program, year_data in all_timetables.items():
        for year, groups in year_data.items():
            for group, schedule in groups.items():
                for day, hours in schedule.items():
                    if day not in transformed_timetable:
                        transformed_timetable[day] = {}
                    for hour, details in hours.items():
                        classroom = details.get('Classroom')
                        if hour not in transformed_timetable[day]:
                            transformed_timetable[day][hour] = []
                        if classroom:
                            transformed_timetable[day][hour].append(classroom)

    lab_availability = remove_lab_if_classroom_matches(transformed_timetable, lab_availability)

    # Extract allocated faculties to remove conflicts in future allocations
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
                    faculty_availability[day][hour][course] = [f for f in available_faculties if f not in faculties]

    # Track day-hour combinations avoiding conflicts
    day_hour_combinations = [
        (day, int(hour))
        for day in lab_availability.keys()
        for hour in lab_availability[day].keys()
        if int(hour) % 2 == 1 and int(hour) != hours_per_day  # Ensure lab blocks (2-hour slots)
    ]

    for programme, sem_timelines in programme_timelines.items():
        department = next((dept for dept, programmes in department_programme_map.items() if programme in programmes), None)
        if department is None:
            continue

        for sem, class_obj in sem_timelines.items():
            for programme, sem_timelines in programme_timelines.items():
                department = next((dept for dept, programmes in department_programme_map.items() if programme in programmes), None)
                if department is None:
                    continue

            for sem, class_obj in sem_timelines.items():
                lab_courses = programme_data[programme][sem]['lab_courses']
                # group_strengths = strength_data.get(programme, {}).get(sem, {})

            for course in lab_courses:
                course_id = course['course_id']
                unallocated_classes_per_week = course['hours_per_week'] // 2

                available_days = list(class_obj.keys())

                while unallocated_classes_per_week > 0:
                    available_hours = [
                        (d, hour)
                        for d, hour in day_hour_combinations
                        if d in available_days
                        and class_obj[d][hour]["Course"] is None and class_obj[d][hour + 1]["Course"] is None
                        and any(
                            lab for lab in lab_availability[d][hour][department]
                            # if lab["capacity"] >= group_strengths.get('G1', 0)
                            if lab["capacity"] >= strength_data
                        )
                        and lab_availability[d][hour + 1][department]
                        and (
                            course_id not in selected_faculties or
                            selected_faculties[course_id] in faculty_availability[d][hour][course_id] and
                            selected_faculties[course_id] in faculty_availability[d][hour + 1][course_id]
                        )
                        and course_id in faculty_availability[d][hour] and faculty_availability[d][hour][course_id]
                        and course_id in faculty_availability[d][hour + 1] and faculty_availability[d][hour + 1][course_id]
                    ]

                    if not available_hours:
                        # print(f"Unable to allocate class for {course_id} in programme {programme}, semester {sem}.")
                        break
                        # No available slots for this course in the current semester
                        # raise Exception(f"Unable to allocate class for {course_id} in programme {programme}, semester {sem}.")


                    random_available_hour = random.choice(available_hours)
                    day, hour = random_available_hour

                    # Select the best-fit lab for this group, sorted by smallest suitable capacity first
                    suitable_labs = sorted(
                        [lab for lab in lab_availability[day][hour][department] if lab["capacity"] >= strength_data],
                        key=lambda lab: abs(lab["capacity"] - strength_data)  # Sort by closest capacity match
                    )
                    selected_lab = suitable_labs[0]  # Choose the best-fit lab
                    lab_availability[day][hour][department].remove(selected_lab)
                    lab_availability[day][hour + 1][department].remove(selected_lab)

                    if course_id not in selected_faculties:
                        selected_faculty = faculty_availability[day][hour][course_id].pop(0)
                        selected_faculties[course_id] = selected_faculty
                    else:
                        selected_faculty = selected_faculties[course_id]

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
                    faculty_availability[day][hour][course_id] = [
                        f for f in faculty_availability[day][hour][course_id] if f != selected_faculty
                    ]
                    faculty_availability[day][hour + 1][course_id] = [
                        f for f in faculty_availability[day][hour + 1][course_id] if f != selected_faculty
                    ]

                    available_days.remove(day)
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
                        # f"Unable to allocate class for {course_id} in programme {programme}, semester {sem}."
                        break
                        # No available slots for this course in the current semester
                        # raise Exception(f"Unable to allocate class for {course_id} in programme {programme}, semester {sem}.")

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
                                # Filter classrooms based on capacity closest to course strength
                                suitable_classrooms = sorted(
                                    [classroom for classroom in classroom_availability[day][hour] if classroom['capacity'] >= course['strength']],
                                    key=lambda c: c['capacity']
                                )
                                if suitable_classrooms:
                                    selected_classroom = suitable_classrooms[0]
                                    classroom_availability[day][hour].remove(selected_classroom)

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

def add_regular_classes(all_timetables, programme_timelines, programme_data, faculties, classrooms, strength_data, hours_per_day, existing_classes=None):
    classrooms = get_dept_classrooms(list(programme_timelines.keys())[0])
    
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in list(list(programme_timelines.values())[0].values())[0].keys()
    }

    faculty_availability = {}
    selected_faculties = {}  # Track the selected faculty for each course and semester
    group_faculty_assignment = {}  # Track the assigned faculty for each (course, group) combination

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

    # Extract existing timetable information
    for programme, semesters in all_timetables.items():
        for semester, groups in semesters.items():
            for group, days in groups.items():
                for day, hours in days.items():
                    for hour, details in hours.items():
                        classroom = details.get('Classroom')
                        if classroom:
                            if day not in extracted_timetable:
                                extracted_timetable[day] = {}
                            if hour not in extracted_timetable[day]:
                                extracted_timetable[day][hour] = []

                            if isinstance(classroom, list):
                                extracted_timetable[day][hour].extend(classroom)
                            else:
                                extracted_timetable[day][hour].append(classroom)

    # Remove allocated classrooms
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

    # Track day-hour combinations for regular class allocation
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
                        if class_obj[d][hour]["Course"] is None
                        and classroom_availability[d][hour]
                        and all(class_obj[d][h]["Course"] != course_id for h in range(1, hours_per_day + 1))
                        and course_id in faculty_availability[d][hour]
                    ]

                    if not available_hours:
                        break  # No available slots

                    day, hour = random.choice(available_hours)

                    # Select suitable classrooms based on strength
                    suitable_classrooms = sorted(
                        [room for room in classroom_availability[day][hour] if room['capacity'] >= strength_data],
                        key=lambda room: abs(room['capacity'] - strength_data)
                    )

                    if not suitable_classrooms:
                        break  # No suitable classrooms available

                    selected_classroom = suitable_classrooms[0]
                    classroom_info = f"{selected_classroom['hall_id']}"

                    # Check if a faculty has already been assigned to this course and group
                    group_key = (course_id, sem, programme)
                    if group_key in group_faculty_assignment:
                        selected_faculty = group_faculty_assignment[group_key]
                    else:
                        # If not assigned, select based on whether the course is already assigned in another group
                        available_faculties = faculty_availability[day][hour][course_id]

                        if course_already_assigned_in_other_group(all_timetables, programme, sem, course_id):
                            # Assign the second faculty if another group already has this course and multiple faculties are available
                            if len(available_faculties) > 1:
                                selected_faculty = available_faculties[1]
                            else:
                                selected_faculty = available_faculties[0]
                        else:
                            # Assign the first faculty if no other group has this course assigned yet
                            selected_faculty = available_faculties[0]

                        # Store the assigned faculty for this course and group
                        group_faculty_assignment[group_key] = selected_faculty

                    # Assign regular course to the class timetable
                    class_obj[day][hour] = {
                        "Classroom": classroom_info,
                        "Faculty": selected_faculty,
                        "Course": course_id
                    }

                    # Remove the selected classroom and faculty from availability
                    classroom_availability[day][hour].remove(selected_classroom)
                    faculty_availability[day][hour][course_id].remove(selected_faculty)

                    # Decrement the unallocated count
                    unallocated_classes_per_week -= 1


def course_already_assigned_in_other_group(all_timetables, programme, sem, course_id):
    """
    Checks whether a course has already been assigned to another group in the same programme and semester.
    """
    if programme in all_timetables:
        if sem in all_timetables[programme]:
            for group, timetable in all_timetables[programme][sem].items():
                for day, hours in timetable.items():
                    for hour, course_details in hours.items():
                        if course_details["Course"] == course_id:
                            return True
    return False
                        

# Main code to generate timetables for all departments and their respective semesters
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
labs = get_labs()
classrooms = get_classrooms()
is_odd_semester = is_odd_semester_check()

department_programme_map = get_department_programme_map()

faculties = get_faculty_allocation_by_course()

elective_data = get_elective_allocation_by_semester()

hours_per_day = 7

# Example: Get data from the database
courses_by_programme = get_courses(is_odd_semester)  # This now contains multiple departments

num_groups_per_sem = fetch_num_groups_per_sem(is_odd_semester)  # Semester 1 and 3 have 2 groups each

strength_data = get_groups_by_programme(is_odd_semester=True)

programme_timelines = {
    programme: {
        sem: structure_timetable_for_groups(
            days, 
            hours_per_day, 
            num_groups_per_sem.get(programme, {}).get(sem, 1)  # Now looks up groups by programme and semester
        )
        for sem in semesters.keys()
    }
    for programme, semesters in courses_by_programme.items()
}

# Updated course allocation function to handle multiple groups
def add_courses_for_groups(programme_timelines, programme_data, faculties, classrooms, labs, hours_per_day, elective_data, department_programme_map, strength_data):
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
                    strength_data[programme][sem][group],
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
                    strength_data[programme][sem][group],
                    hours_per_day
                )

max_total_cost = -1
max_programme_timelines = None

for i in range(100):
    programme_timelines = {
        programme: {
            sem: structure_timetable_for_groups(
                days, 
                hours_per_day, 
                num_groups_per_sem.get(programme, {}).get(sem, 1)  # Now looks up groups by programme and semester
            )
            for sem in semesters.keys()
        }
        for programme, semesters in courses_by_programme.items()
    }

    add_courses_for_groups(programme_timelines, courses_by_programme, faculties, classrooms, labs, hours_per_day, elective_data, department_programme_map, strength_data)

    free_hours_weight = 3.0
    faculty_distribution_weight = 2.0
    classroom_switching_weight = 1.5
    total_costs = compute_costs_for_single_timetable(programme_timelines, free_hours_weight, faculty_distribution_weight, classroom_switching_weight)

    # print(total_costs)

    # Check if the current total cost is greater than the maximum found so far
    if total_costs['total_cost'] > max_total_cost:
        max_total_cost = total_costs['total_cost']
        max_programme_timelines = programme_timelines

# After the loop, max_programme_timelines contains the programme_timelines with the maximum total cost
# print("Programme Timelines with Maximum Total Cost:")
json_output = json.dumps(max_programme_timelines)
print(json_output)
# print("Maximum Total Cost:", max_total_cost)



# Call the updated function to allocate courses for all groups
# add_courses_for_groups(programme_timelines, courses_by_programme, faculties, classrooms, labs, hours_per_day, elective_data, department_programme_map, strength_data)


# i=0
# for i in range(0, 5000):
#     try:
#         # print("--------------------------------------------")
#         add_courses_for_groups(programme_timelines, courses_by_programme, faculties, classrooms, labs, hours_per_day, elective_data, department_programme_map, strength_data)
#         # print(f"Timetable {i + 1} generated successfully.")
#         json_output = json.dumps(programme_timelines)
#         print(json_output)
#         # print("--------------------------------------------")
#     except Exception as e:
#         pass
#         # print("=============================================")
#         # print(f"Error generating timetable {i + 1}: {e}")
        
#         # print("=============================================")

# # json_output = json.dumps(programme_timelines)
# # print(json_output)

# successful_timelines = 0
# i = 0

# while successful_timelines < 1:
#     try:
#         # Call the function to add courses and generate timetables
#         add_courses_for_groups(programme_timelines, courses_by_programme, faculties, classrooms, labs, hours_per_day, elective_data, department_programme_map, strength_data)
        
#         # If no exception occurs, increment the counter for successful timetables
#         json_output = json.dumps(programme_timelines)
#         print(f"Timetable {successful_timelines + 1} generated successfully.")
#         print(json_output)
        
#         successful_timelines += 1  # Increment successful timelines count
        
#     except Exception as e:
#         pass
#         # If an exception occurs, print the error and continue the loop to retry
#         # print(f"Error generating timetable {i + 1}: {e}")
    
#     i += 1  # Increment the loop index