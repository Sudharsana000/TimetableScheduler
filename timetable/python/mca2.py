import random
import json
from queries import get_courses

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

def add_lab_courses(department_timelines, programme_data, faculties, labs, hours_per_day):
    # Initialize availability trackers for labs and faculties for each department
    lab_availability = {
        day: {hour: list(labs) for hour in range(1, hours_per_day + 1)}
        for day in list(list(department_timelines.values())[0].values())[0].keys()  # Use any class timetable to get day list
    }
    
    faculty_availability = {}
    selected_faculties = {}  # Track the selected faculty for each course
    
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
    
    for department, sem_timelines in department_timelines.items():
        for sem, class_obj in sem_timelines.items():
            lab_courses = programme_data[department][sem]['lab_courses']
            
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
                        and lab_availability[d][hour] and lab_availability[d][hour + 1]
                        and course_id in faculty_availability[d][hour] and faculty_availability[d][hour][course_id]
                        and course_id in faculty_availability[d][hour + 1] and faculty_availability[d][hour + 1][course_id]
                    ]
                    
                    if not available_hours:
                        print(f"No available slots for lab course '{course_id}' in semester {sem} for department {department}")
                        break

                    random_available_hour = random.choice(available_hours)
                    day, hour = random_available_hour

                    selected_lab = lab_availability[day][hour].pop(0)
                    if course_id not in selected_faculties:
                        selected_faculty = faculty_availability[day][hour][course_id].pop(0)
                        selected_faculties[course_id] = selected_faculty
                    else:
                        selected_faculty = selected_faculties[course_id]

                    # Assign lab to the class timetable
                    class_obj[day][hour] = {
                        "Classroom": selected_lab,
                        "Faculty": selected_faculty,
                        "Course": course_id
                    }

                    class_obj[day][hour + 1] = {
                        "Classroom": selected_lab,
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

# Main code to generate timetables for all departments and their respective semesters
days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
labs = ["CC", "ISL", "Project"]

faculties = {
    "23MX36": ["Bhama"],
    "23MX37": ["Geetha"],
    "23MX16": ["Geetha", "Umarani"],
    "23MX17": ["Gayathri"],
    "23MX18": ["Sundar"]
}

hours_per_day = 7

# Example: Get data from the database
courses_by_programme = get_courses()  # This now contains multiple departments

# Dynamically generate timetables for all departments and their respective semesters
department_timelines = {
    department: {
        sem: structure_timetable(days, hours_per_day)
        for sem in semesters.keys()
    }
    for department, semesters in courses_by_programme.items()
}

# Add lab courses for all departments and their respective semesters
add_lab_courses(department_timelines, courses_by_programme, faculties, labs, hours_per_day)

# Output the timetable for all departments and semesters as a JSON string
json_output = json.dumps(department_timelines)
print(json_output)