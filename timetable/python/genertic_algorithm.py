import random
import json

faculty_class_count = {}

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

# Global dictionary to track how many classes each faculty is handling
faculty_class_count = {}

def assign_faculties_for_lab_courses(lab_courses, faculties):
    global faculty_class_count  # Use the global variable

    lab_course_faculty_assignment = {}

    for course in lab_courses:
        if course in faculties and faculties[course]:
            # Iterate over the list of available faculties
            selected_faculty = None
            for faculty in faculties[course]:
                if faculty not in faculty_class_count:
                    faculty_class_count[faculty] = 0

                # Select the first faculty with less than 2 classes assigned
                if faculty_class_count[faculty] < 2:
                    selected_faculty = faculty
                    faculty_class_count[faculty] += 1
                    break

            if selected_faculty is None:
                print(f"Error: No faculties available for lab course '{course}' who can handle more classes")
                return

            lab_course_faculty_assignment[course] = selected_faculty
        else:
            print(f"Error: No faculties available for lab course '{course}'")
            return

    return lab_course_faculty_assignment

def add_lab_courses(class1, lab_courses, faculties, classes_per_week, labs, hours_per_day, existing_class=None):
    # Call the faculty assignment function here
    lab_course_faculty_assignment = assign_faculties_for_lab_courses(lab_courses, faculties)

    # Initialize availability trackers for labs and faculties
    lab_availability = {
        day: {hour: list(labs) for hour in range(1, hours_per_day + 1)}
        for day in class1.keys()
    }
    faculty_availability = {}

    for day in class1.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            for course in lab_courses:
                if course in faculties:
                    # Use the assigned faculty for this lab course
                    selected_faculty = lab_course_faculty_assignment[course]
                    faculty_availability[day][hour][course] = [selected_faculty]
                else:
                    print(f"Error: Course '{course}' not found in faculties dictionary.")
                    return
    
    # Adjust availability based on existing_class timetable
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
    
    # Filter for available hours for lab allocation (same logic as before)
    day_hour_combinations = [
        (day, int(hour))  # Extract the hour number as an integer
        for day in class1.keys()
        for hour in class1[day].keys()
        if int(hour) % 2 == 1 and int(hour) != hours_per_day  # Only take odd-numbered hours, excluding the last hour
    ]
    
    for course in lab_courses:
        unallocated_classes_per_week = classes_per_week[course]
        available_days = list(class1.keys())
        
        while unallocated_classes_per_week > 0:
            # Filter available hours where both labs and faculties are available
            available_hours = [
                (d, hour) 
                for d, hour in day_hour_combinations
                if d in available_days and class1[d][hour]["Course"] is None
                and lab_availability[d][hour] and faculty_availability[d][hour][course]
                and lab_availability[d][hour + 1] and faculty_availability[d][hour + 1][course]  # Check the next hour as well
            ]
            
            if not available_hours:
                print(f"Error: No available hours for lab course '{course}'")
                break

            random_available_hour = random.choice(available_hours)
            day, hour = random_available_hour

            # Select the first available lab and faculty (already assigned to this course)
            selected_lab = lab_availability[day][hour].pop(0)
            selected_faculty = faculty_availability[day][hour][course].pop(0)

            # Allocate the course, lab, and faculty to this slot
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

            # Mark faculty as unavailable for this time slot
            if not faculty_availability[day][hour][course]:  # Remove the course if no faculty left
                del faculty_availability[day][hour][course]
            if not faculty_availability[day][hour + 1][course]:
                del faculty_availability[day][hour + 1][course]

            # Reduce the number of unallocated classes per week
            available_days.remove(day)
            unallocated_classes_per_week -= 1

def assign_faculties_for_courses(regular_courses, regular_faculties):
    global faculty_class_count  # Use the global variable

    course_faculty_assignment = {}

    for course in regular_courses:
        if course in regular_faculties and regular_faculties[course]:
            # Iterate over the list of available faculties
            selected_faculty = None
            for faculty in regular_faculties[course]:
                if faculty not in faculty_class_count:
                    faculty_class_count[faculty] = 0

                # Select the first faculty with less than 2 classes assigned
                if faculty_class_count[faculty] < 2:
                    selected_faculty = faculty
                    faculty_class_count[faculty] += 1
                    break

            if selected_faculty is None:
                print(f"Error: No faculties available for course '{course}' who can handle more classes")
                return

            course_faculty_assignment[course] = selected_faculty
        else:
            print(f"Error: No faculties available for course '{course}'")
            return

    return course_faculty_assignment

def add_regular_courses(class1, regular_courses, regular_faculties, regular_classes_per_week, classrooms, existing_classes=None):
    # Call the faculty assignment function here
    course_faculty_assignment = assign_faculties_for_courses(regular_courses, regular_faculties)

    # Proceed with the existing logic of assigning classrooms and courses
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in class1.keys()
    }

    faculty_availability = {}

    for day in class1.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            for course in regular_courses:
                if course in regular_faculties:
                    # Use the assigned faculty for this course
                    selected_faculty = course_faculty_assignment[course]
                    faculty_availability[day][hour][course] = [selected_faculty]
                else:
                    print(f"Error: Course '{course}' not found in faculties dictionary.")
                    return

    # Add regular courses to the schedule
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in class1.keys()
    }

    # Adjust availability based on existing_class timetable
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
        (day, int(hour))  # Extract the hour number as an integer
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
            selected_faculty = faculty_availability[day][hour][regular_course].pop(0)

            class1[day][hour] = {
                "Classroom": selected_classroom,
                "Faculty": selected_faculty,
                "Course": regular_course
            }

            # Mark faculty as unavailable for this time slot
            if not faculty_availability[day][hour][regular_course]:  # Remove the course if no faculty left
                del faculty_availability[day][hour][regular_course]

            available_days.remove(day)
            unallocated_regular_classes_per_week -= 1

            day_hour_combinations.remove((day, hour))

days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
lab_courses = ["C Lab", "DS Lab", "MAD Lab"]  # Ensure these match the keys in faculties
regular_courses = ["MFCS", "SPC", "DS", "DBMS", "WT", "TWM"]

labs = ["CC", "ISL", "Project"]
classrooms = ["K504", "K505"]

classes_per_week = {
    "C Lab": 2,
    "DS Lab": 2,
    "MAD Lab": 2
}

regular_classes_per_week = {
    "MFCS" : 4,
    "SPC": 3,
    "DS": 3,
    "DBMS": 4,
    "WT": 3,
    "TWM": 1
}

faculties = {
    "C Lab": ["Geetha"],
    "DS Lab": ["Gayatri"],
    "MAD Lab": ["Sundar"]
}

regular_faculties = {
    "MFCS": ["Shankar", "Sundar"],
    "SPC": ["Manavalan"],
    "DS": ["Gayathri"],
    "DBMS": ["Geetha", "Ilayaraja"],
    "WT": ["Kalyani"],
    "TWM": ["Geetha", "Subathra"]
}

hours_per_day = 7

class1 = structure_timetable(days, hours_per_day)
add_lab_courses(class1, lab_courses, faculties, classes_per_week, labs, hours_per_day)
class2 = structure_timetable(days, hours_per_day)
add_lab_courses(class2, lab_courses, faculties, classes_per_week, labs, hours_per_day, class1)

add_regular_courses(class1, regular_courses, regular_faculties, regular_classes_per_week, classrooms, class2)
add_regular_courses(class2, regular_courses, regular_faculties, regular_classes_per_week, classrooms, class1)

# # Uncomment the following line to print the resulting timetable
# for day in days:
#     for hour in range(1, hours_per_day+1):
#         if (class1[day][hour]['Faculty'] == class2[day][hour]['Faculty']) or (class1[day][hour]['Classroom'] == class2[day][hour]['Classroom']):
#             print(class1[day][hour],"----", class2[day][hour])
json_output = json.dumps({"G1": class1, "G2": class2})
print(json_output)