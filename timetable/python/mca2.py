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

    # Allocate electives to both class1 and class2
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

            # Assign elective course1 to class1 and course2 to class2
            selected_classroom1 = classroom_availability[day][hour].pop(0)
            selected_classroom2 = classroom_availability[day][hour].pop(0)

            selected_faculty1 = faculty_availability[day][hour][course1].pop(0)
            selected_faculty2 = faculty_availability[day][hour][course2].pop(0)

            class1[day][hour] = {
                "Classroom": selected_classroom1,
                "Faculty": selected_faculty1,
                "Course": course1
            }

            class2[day][hour] = {
                "Classroom": selected_classroom2,
                "Faculty": selected_faculty2,
                "Course": course2
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

def add_lab_courses(class1, lab_courses, faculties, classes_per_week, labs, hours_per_day, existing_class=None):
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
    
    # Consider the existing elective course allocations to avoid conflicts
    if existing_class:
        for day in existing_class:
            for hour in existing_class[day]:
                if existing_class[day][hour]["Classroom"]:
                    if existing_class[day][hour]["Classroom"] in lab_availability[day][hour]:
                        lab_availability[day][hour].remove(existing_class[day][hour]["Classroom"])
                if existing_class[day][hour]["Faculty"] and existing_class[day][hour]["Course"]:
                    course = existing_class[day][hour]["Course"]
                    if course in faculty_availability[day][hour] and existing_class[day][hour]["Faculty"] in faculty_availability[day][hour][course]:
                        faculty_availability[day][hour][course].remove(existing_class[day][hour]["Faculty"])

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
                print(f"No available slots found for lab course '{course}'")
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
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in class1.keys()
    }

    faculty_availability = {}
    selected_faculties = {}  # Track the selected faculty for each course

    for day in class1.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            for course in regular_courses:
                if course in regular_faculties:
                    faculty_availability[day][hour][course] = list(regular_faculties[course])
                    if (class1[day][hour]['Faculty'] is not None) and (class1[day][hour]['Faculty'] in faculty_availability[day][hour][course]):
                        faculty_availability[day][hour][course].remove(class1[day][hour]['Faculty'])
                else:
                    print(f"Error: Course '{course}' not found in faculties dictionary.")
                    return
    
    if existing_classes:
        for day in existing_classes:
            for hour in existing_classes[day]:
                if existing_classes[day][hour]["Classroom"]:
                    if existing_classes[day][hour]["Classroom"] in classroom_availability[day][hour]:
                        classroom_availability[day][hour].remove(existing_classes[day][hour]["Classroom"])
                if existing_classes[day][hour]["Faculty"]:
                    for course in faculty_availability[day][hour]:
                        if existing_classes[day][hour]["Faculty"] in faculty_availability[day][hour][course]:
                            faculty_availability[day][hour][course].remove(existing_classes[day][hour]["Faculty"])

    day_hour_combinations = [
        (day, int(hour))
        for day in class1.keys()
        for hour in class1[day].keys()
        if class1[day][hour]['Course'] is None
    ]
    
    for regular_course in regular_courses:
        unallocated_regular_classes_per_week = regular_classes_per_week[regular_course]
        available_days = list(class1.keys())

        while unallocated_regular_classes_per_week > 0:
            available_hours = [
                (d, hour)
                for d, hour in day_hour_combinations
                if d in available_days and classroom_availability[d][hour]
                and regular_course in faculty_availability[d][hour] and faculty_availability[d][hour][regular_course]
            ]

            if not available_hours:
                print("Allocation not found for", regular_course)
                break

            random_available_hour = random.choice(available_hours)
            day, hour = random_available_hour

            selected_classroom = classroom_availability[day][hour].pop(0)
            
            if regular_course not in selected_faculties:
                selected_faculty = faculty_availability[day][hour][regular_course].pop(0)
                selected_faculties[regular_course] = selected_faculty
            else:
                selected_faculty = selected_faculties[regular_course]

            class1[day][hour] = {
                "Classroom": selected_classroom,
                "Faculty": selected_faculty,
                "Course": regular_course
            }

            if not faculty_availability[day][hour][regular_course]:  
                del faculty_availability[day][hour][regular_course]

            available_days.remove(day)
            unallocated_regular_classes_per_week -= 1

            day_hour_combinations.remove((day, hour))


days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
elective_courses = [["HCI", "SPM"], ["PMBS", "ES"], ["SN", "CN"], ["ML", "DO"]]
lab_courses = ["Miniproject Lab", "CC Lab"]  # Ensure these match the keys in faculties
regular_courses = ["CC", "PE","TWM"]

labs = ["CC", "ISL", "Project"]
classrooms = ["K504", "K505"]

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
    "Miniproject Lab": 2
}

regular_classes_per_week = {
    "CC" : 3,
    "PE": 2,
    "TWM": 1
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
    "Miniproject Lab": ["Geetha"]
}

regular_faculties = {
    "CC": ["Bhama"],
    "PE": ["Rathika"],
    "TWM": ["Geetha", "Subathra"]
}

hours_per_day = 7

class1 = structure_timetable(days, hours_per_day)
class2 = structure_timetable(days, hours_per_day)

add_elective_courses(class1, class2, elective_courses, classrooms, elective_courses_per_week, hours_per_day)

add_lab_courses(class1, lab_courses, faculties, classes_per_week, labs, hours_per_day)
add_lab_courses(class2, lab_courses, faculties, classes_per_week, labs, hours_per_day, class1)

add_regular_courses(class1, regular_courses, regular_faculties, regular_classes_per_week, classrooms, class2)
add_regular_courses(class2, regular_courses, regular_faculties, regular_classes_per_week, classrooms, class1)

for day in days:
    for hour in range(1, hours_per_day+1):
        if (class1[day][hour]['Faculty'] == class2[day][hour]['Faculty']) or (class1[day][hour]['Classroom'] == class2[day][hour]['Classroom']):
            print(class1[day][hour],"----", class2[day][hour])
# json_output = json.dumps({"G1": class1, "G2": class2})
# print(json_output)