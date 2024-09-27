import random
import json

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

def add_elective_courses(class1, class2, elective_courses, classrooms, elective_courses_per_week, hours_per_day):
    # Track available classrooms for each day and hour
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in class1.keys()
    }
    
    # Track availability of faculties for elective courses
    faculty_availability = {}
    
    for day in class1.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            for course_pair in elective_courses:
                for course in course_pair:
                    faculty_availability[day][hour][course] = list(elective_faculties[course])

    day_hour_combinations = [
        (day, int(hour))
        for day in class1.keys()
        for hour in class1[day].keys()
        if class1[day][hour]['Course'] is None and class2[day][hour]['Course'] is None
    ]

    # Allocate electives to both class1 and class2 at the same hour
    for elective_pair in elective_courses:
        course1, course2 = elective_pair
        unallocated_classes_per_week1 = elective_courses_per_week[course1]
        unallocated_classes_per_week2 = elective_courses_per_week[course2]
        available_days = list(class1.keys())

        while unallocated_classes_per_week1 > 0 and unallocated_classes_per_week2 > 0:
            available_hours = [
                (d, hour)
                for d, hour in day_hour_combinations
                if d in available_days and classroom_availability[d][hour]
                and course1 in faculty_availability[d][hour] and faculty_availability[d][hour][course1]
                and course2 in faculty_availability[d][hour] and faculty_availability[d][hour][course2]
            ]

            if not available_hours:
                print(f"No more available slots for electives {course1} and {course2}.")
                break

            random_available_hour = random.choice(available_hours)
            day, hour = random_available_hour

            # Assign elective course1 and course2 at the same hour for both classes
            selected_classroom1 = classroom_availability[day][hour].pop(0)
            selected_classroom2 = classroom_availability[day][hour].pop(0)

            selected_faculty1 = faculty_availability[day][hour][course1].pop(0)
            selected_faculty2 = faculty_availability[day][hour][course2].pop(0)

            # Assign electives for both classes in an array format
            class1[day][hour] = {
                "Classroom": [selected_classroom1, selected_classroom2],
                "Faculty": [selected_faculty1, selected_faculty2],
                "Course": [course1, course2]
            }

            class2[day][hour] = {
                "Classroom": [selected_classroom1, selected_classroom2],
                "Faculty": [selected_faculty1, selected_faculty2],
                "Course": [course1, course2]
            }

            if not faculty_availability[day][hour][course1]:
                del faculty_availability[day][hour][course1]

            if not faculty_availability[day][hour][course2]:
                del faculty_availability[day][hour][course2]

            available_days.remove(day)
            unallocated_classes_per_week1 -= 1
            unallocated_classes_per_week2 -= 1

            # Remove the selected time slot from further allocation
            day_hour_combinations.remove((day, hour))

def add_lab_courses(class1, lab_courses, faculties, classes_per_week, labs, hours_per_day, existing_classes=None):
    # Initialize availability trackers for labs and faculties
    lab_availability = {
        day: {hour: list(labs) for hour in range(1, hours_per_day + 1)}
        for day in class1.keys()
    }
    faculty_availability = {}
    selected_faculties = {}  # Track the selected faculty for each course
    
    for day in class1.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            for course in lab_courses:
                if course in faculties:
                    faculty_availability[day][hour][course] = list(faculties[course])
    
    # Check conflicts with existing classes (array of timetables)
    if existing_classes:
        for existing_class in existing_classes:
            for day in existing_class:
                for hour in existing_class[day]:
                    # Classroom conflict: Mark the classroom as unavailable if used by any existing class
                    if existing_class[day][hour]["Classroom"]:
                        if existing_class[day][hour]["Classroom"] in lab_availability[day][hour]:
                            lab_availability[day][hour].remove(existing_class[day][hour]["Classroom"])
                    
                    # Faculty conflict: Remove faculty availability if already teaching in another class
                    existing_faculty = existing_class[day][hour]["Faculty"]
                    if existing_faculty:
                        for course in faculty_availability[day][hour]:
                            if isinstance(existing_faculty, list):
                                # Remove each faculty in the list from availability
                                for faculty in existing_faculty:
                                    if faculty in faculty_availability[day][hour][course]:
                                        faculty_availability[day][hour][course].remove(faculty)
                            else:
                                # Handle case where Faculty is a single value
                                if existing_faculty in faculty_availability[day][hour][course]:
                                    faculty_availability[day][hour][course].remove(existing_faculty)

    # Modify day-hour combinations to avoid elective hours
    day_hour_combinations = [
        (day, int(hour))
        for day in class1.keys()
        for hour in class1[day].keys()
        if class1[day][hour]["Course"] is None  # Skip elective or regular course slots
        and int(hour) % 2 == 1 and int(hour) != hours_per_day  # Only allow for lab blocks (2-hour labs)
    ]
    
    for course in lab_courses:
        unallocated_classes_per_week = classes_per_week[course]
        available_days = list(class1.keys())
        
        while unallocated_classes_per_week > 0:
            available_hours = [
                (d, hour) 
                for d, hour in day_hour_combinations
                if d in available_days and class1[d][hour]["Course"] is None
                and class1[d][hour + 1]["Course"] is None  # Ensure the next hour is free for lab blocks
                and lab_availability[d][hour] and faculty_availability[d][hour][course]
                and lab_availability[d][hour + 1] and faculty_availability[d][hour + 1][course]
            ]
            
            if not available_hours:
                #print(f"No available slots found for lab course '{course}'")
                break

            random_available_hour = random.choice(available_hours)
            day, hour = random_available_hour

            selected_lab = lab_availability[day][hour].pop(0)
            if course not in selected_faculties:
                selected_faculty = faculty_availability[day][hour][course].pop(0)
                selected_faculties[course] = selected_faculty
            else:
                selected_faculty = selected_faculties[course]

            class1[day][hour] = {
                "Classroom": selected_lab,
                "Faculty": selected_faculty,
                "Course": course
            }

            class1[day][hour + 1] = {
                "Classroom": selected_lab,
                "Faculty": selected_faculty,
                "Course": course
            }

            # Remove faculty availability for both hours
            if not faculty_availability[day][hour][course]:
                del faculty_availability[day][hour][course]
            if not faculty_availability[day][hour + 1][course]:
                del faculty_availability[day][hour + 1][course]

            available_days.remove(day)
            unallocated_classes_per_week -= 1

def add_regular_courses(class1, regular_courses, regular_faculties, regular_classes_per_week, classrooms, existing_classes=None):
    # Initialize classroom availability for all days and hours
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in class1.keys()
    }

    faculty_availability = {}
    selected_faculties = {}  # Track the selected faculty for each course

    # Initialize faculty availability for all courses
    for day in class1.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            for course in regular_courses:
                if course in regular_faculties:
                    faculty_availability[day][hour][course] = list(regular_faculties[course])
                    # Remove already assigned faculties in class1
                    if (class1[day][hour]['Faculty'] is not None) and (class1[day][hour]['Faculty'] in faculty_availability[day][hour][course]):
                        faculty_availability[day][hour][course].remove(class1[day][hour]['Faculty'])
                else:
                    print(f"Error: Course '{course}' not found in faculties dictionary.")
                    return

    # Check and remove availability based on existing classes (list of timetables)
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

    # Find available day-hour combinations
    day_hour_combinations = [
        (day, int(hour))
        for day in class1.keys()
        for hour in class1[day].keys()
        if class1[day][hour]['Course'] is None  # Only empty slots
    ]

    # Allocate regular courses
    for regular_course in regular_courses:
        unallocated_regular_classes_per_week = regular_classes_per_week[regular_course]
        available_days = list(class1.keys())

        while unallocated_regular_classes_per_week > 0:
            available_hours = [
                (d, hour)
                for d, hour in day_hour_combinations
                if d in available_days
                and classroom_availability[d][hour]  # Classroom available
                and regular_course in faculty_availability[d][hour]
                and faculty_availability[d][hour][regular_course]  # Faculty available
            ]

            if not available_hours:
                #print(f"Allocation not found for {regular_course}")
                break

            # Choose a random available day-hour slot
            random_available_hour = random.choice(available_hours)
            day, hour = random_available_hour

            # Allocate classroom
            selected_classroom = classroom_availability[day][hour].pop(0)

            # Allocate faculty (if not already selected)
            if regular_course not in selected_faculties:
                selected_faculty = faculty_availability[day][hour][regular_course].pop(0)
                selected_faculties[regular_course] = selected_faculty
            else:
                selected_faculty = selected_faculties[regular_course]

            # Update the timetable for class1
            class1[day][hour] = {
                "Classroom": selected_classroom,
                "Faculty": selected_faculty,
                "Course": regular_course
            }

            # Remove faculty from availability once allocated
            if not faculty_availability[day][hour][regular_course]:
                del faculty_availability[day][hour][regular_course]

            # Remove from available day-hour slots and decrement the unallocated count
            day_hour_combinations.remove((day, hour))
            available_days.remove(day)
            unallocated_regular_classes_per_week -= 1

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
elective_courses = [["HCI", "SPM"], ["PMBS", "ES"], ["SN", "CN"], ["ML", "DO"]]
lab_courses = ["Miniproject Lab", "CC Lab"]  # Ensure these match the keys in faculties
lab_courses1 = ["C Lab", "DS Lab", "WAD Lab"]
regular_courses = ["CC", "PE","TWM"]
regular_courses1 = ["MFCS", "SPC","DBMS", "DS", "WT", "TWM"]

labs = ["CC", "ISL", "Project"]
classrooms = ["K503", "K504", "K505"]

elective_courses_per_week = {
    "HCI": 3,
    "SPM": 3,
    "PMBS": 3,
    "ES": 3,
    "SN": 3,
    "CN": 3,
    "ML": 3,
    "DO": 3
}

classes_per_week = {
    "CC Lab": 2,
    "Miniproject Lab": 2,
    "C Lab": 2,
    "DS Lab": 2,
    "WAD Lab": 2
}

regular_classes_per_week = {
    "CC" : 3,
    "PE": 2,
    "TWM": 1,
    "MFCS": 4,
    "SPC": 3,
    "DBMS": 4,
    "DS": 3,
    "WT": 3
}

elective_faculties = {
    "HCI": ["Ilayaraja"],
    "SPM": ["Shankar"],
    "PMBS": ["Kalpana"],
    "ES": ["Sundar"],
    "SN": ["Gowri Thangam"],
    "CN": ["Kalyani"],
    "ML": ["Umarani"],
    "DO": ["Manavalan"]
}

faculties = {
    "CC Lab": ["Bhama"],
    "Miniproject Lab": ["Geetha"],
    "C Lab": ["Geetha", "Umarani"],
    "DS Lab": ["Gayathri"],
    "WAD Lab": ["Sundar"]
}

regular_faculties = {
    "CC": ["Bhama"],
    "PE": ["Rathika"],
    "TWM": ["Geetha", "Subathra", "Ilayaraja", "Umarani"],
    "MFCS": ["Shankar", "Sundar"],
    "SPC": ["Geetha", "Umarani"],
    "DBMS": ["Ilayaraja", "Geetha"],
    "DS": ["Chitra", "Gayathri"],
    "WT": ["Kalyani"]
}

hours_per_day = 7

class1 = structure_timetable(days, hours_per_day)
class2 = structure_timetable(days, hours_per_day)
class3 = structure_timetable(days, hours_per_day)
class4 = structure_timetable(days, hours_per_day)

add_elective_courses(class1, class2, elective_courses, classrooms, elective_courses_per_week, hours_per_day)

add_lab_courses(class1, lab_courses, faculties, classes_per_week, labs, hours_per_day)
add_lab_courses(class2, lab_courses, faculties, classes_per_week, labs, hours_per_day, [class1])
add_lab_courses(class3, lab_courses1, faculties, classes_per_week, labs, hours_per_day, [class1, class2])
add_lab_courses(class4, lab_courses1, faculties, classes_per_week, labs, hours_per_day, [class1, class2, class3])

add_regular_courses(class1, regular_courses, regular_faculties, regular_classes_per_week, classrooms, [class2, class3, class4])
add_regular_courses(class2, regular_courses, regular_faculties, regular_classes_per_week, classrooms, [class1, class3, class4])
add_regular_courses(class3, regular_courses1, regular_faculties, regular_classes_per_week, classrooms, [class2, class1, class4])
add_regular_courses(class4, regular_courses1, regular_faculties, regular_classes_per_week, classrooms, [class2, class3, class1])

# for day in days:
#     for hour in range(1, hours_per_day + 1):
#         # Check faculty conflicts
#         faculty_conflicts = (
#             (class1[day][hour]['Faculty'] == class2[day][hour]['Faculty'] and class1[day][hour]['Faculty'] is not None) or
#             (class1[day][hour]['Faculty'] == class3[day][hour]['Faculty'] and class1[day][hour]['Faculty'] is not None) or
#             (class1[day][hour]['Faculty'] == class4[day][hour]['Faculty'] and class1[day][hour]['Faculty'] is not None) or
#             (class2[day][hour]['Faculty'] == class3[day][hour]['Faculty'] and class2[day][hour]['Faculty'] is not None) or
#             (class2[day][hour]['Faculty'] == class4[day][hour]['Faculty'] and class2[day][hour]['Faculty'] is not None) or
#             (class3[day][hour]['Faculty'] == class4[day][hour]['Faculty'] and class3[day][hour]['Faculty'] is not None)
#         )

#         # Check classroom conflicts
#         classroom_conflicts = (
#             (class1[day][hour]['Classroom'] == class2[day][hour]['Classroom'] and class1[day][hour]['Classroom'] is not None) or
#             (class1[day][hour]['Classroom'] == class3[day][hour]['Classroom'] and class1[day][hour]['Classroom'] is not None) or
#             (class1[day][hour]['Classroom'] == class4[day][hour]['Classroom'] and class1[day][hour]['Classroom'] is not None) or
#             (class2[day][hour]['Classroom'] == class3[day][hour]['Classroom'] and class2[day][hour]['Classroom'] is not None) or
#             (class2[day][hour]['Classroom'] == class4[day][hour]['Classroom'] and class2[day][hour]['Classroom'] is not None) or
#             (class3[day][hour]['Classroom'] == class4[day][hour]['Classroom'] and class3[day][hour]['Classroom'] is not None)
#         )

#         if faculty_conflicts or classroom_conflicts:
#             print(f"Conflict at {day} {hour}:")
#             print("Class 1:", class1[day][hour])
#             print("Class 2:", class2[day][hour])
#             print("Class 3:", class3[day][hour])
#             print("Class 4:", class4[day][hour])
#             print("-" * 50)

json_output = json.dumps({"MCA year 2 G1": class1, "MCA year 2 G2": class2, "MCA year 1 G1": class3, "MCA year 1 G2": class4})
print(json_output)