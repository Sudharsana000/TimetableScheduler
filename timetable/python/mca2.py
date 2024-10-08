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

def add_lab_courses(programme_timelines, programme_data, faculties, labs, department_programme_map, hours_per_day, groups):
    lab_availability = {
        day: {hour: {} for hour in range(1, hours_per_day + 1)}
        for day in list(list(programme_timelines.values())[0].values())[0].keys()
    }

    faculty_availability = {}
    selected_faculties = {}

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

    day_hour_combinations = [
        (day, int(hour))
        for day in lab_availability.keys()
        for hour in lab_availability[day].keys()
        if int(hour) % 2 == 1 and int(hour) != hours_per_day
    ]

    for programme, sem_timelines in programme_timelines.items():
        department = next((dept for dept, programmes in department_programme_map.items() if programme in programmes), None)
        if department is None:
            print(f"No department found for programme: {programme}")
            continue

        for sem, group_timelines in sem_timelines.items():
            for group in groups[programme][sem]:
                class_obj = group_timelines[group]

                lab_courses = programme_data[programme][sem]['lab_courses']
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
                            and lab_availability[d][hour][department] and lab_availability[d][hour + 1][department]
                            and course_id in faculty_availability[d][hour] and faculty_availability[d][hour][course_id]
                            and course_id in faculty_availability[d][hour + 1] and faculty_availability[d][hour + 1][course_id]
                        ]

                        if not available_hours:
                            print(f"No available slots for lab course '{course_id}' in semester {sem} for department {department}")
                            break

                        random_available_hour = random.choice(available_hours)
                        day, hour = random_available_hour

                        selected_lab = lab_availability[day][hour][department].pop(0)
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

                        if not faculty_availability[day][hour][course_id]:
                            del faculty_availability[day][hour][course_id]
                        if not faculty_availability[day][hour + 1][course_id]:
                            del faculty_availability[day][hour + 1][course_id]

                        available_days.remove(day)
                        unallocated_classes_per_week -= 1

def add_regular_classes(programme_timelines, programme_data, faculties, classrooms, hours_per_day, groups, existing_classes=None):
    classroom_availability = {
        day: {hour: list(classrooms) for hour in range(1, hours_per_day + 1)}
        for day in list(list(programme_timelines.values())[0].values())[0].keys()
    }

    faculty_availability = {}
    selected_faculties = {}

    for day in classroom_availability.keys():
        faculty_availability[day] = {}
        for hour in range(1, hours_per_day + 1):
            faculty_availability[day][hour] = {}
            for department, semesters in programme_data.items():
                for sem in semesters.keys():
                    for course in programme_data[department][sem]['regular_courses']:
                        course_id = course['course_id']
                        if course_id in faculties:
                            faculty_availability[day][hour][course_id] = list(faculties[course_id])

    if existing_classes:
        for existing_class in existing_classes:
            for day in existing_class:
                for hour in existing_class[day]:
                    existing_classroom = existing_class[day][hour]["Classroom"]
                    if existing_classroom:
                        if isinstance(existing_classroom, list):
                            for classroom in existing_classroom:
                                if classroom in classroom_availability[day][hour]:
                                    classroom_availability[day][hour].remove(classroom)
                        else:
                            if existing_classroom in classroom_availability[day][hour]:
                                classroom_availability[day][hour].remove(existing_classroom)

                    existing_faculty = existing_class[day][hour]["Faculty"]
                    if existing_faculty:
                        if isinstance(existing_faculty, list):
                            for faculty in existing_faculty:
                                for course in faculty_availability[day][hour]:
                                    if faculty in faculty_availability[day][hour][course]:
                                        faculty_availability[day][hour][course].remove(faculty)
                        else:
                            for course in faculty_availability[day][hour]:
                                if existing_faculty in faculty_availability[day][hour][course]:
                                    faculty_availability[day][hour][course].remove(existing_faculty)

    day_hour_combinations = [
        (day, int(hour))
        for day in classroom_availability.keys()
        for hour in range(1, hours_per_day + 1)
    ]

    for programme, sem_timelines in programme_timelines.items():
        for sem, group_timelines in sem_timelines.items():
            for group in groups[programme][sem]:
                class_obj = group_timelines[group]

                regular_courses = programme_data[programme][sem]['regular_courses']
                for course in regular_courses:
                    course_id = course['course_id']
                    unallocated_classes_per_week = course['hours_per_week']

                    while unallocated_classes_per_week > 0:
                        available_hours = [
                            (d, hour)
                            for d, hour in day_hour_combinations
                            if class_obj[d][hour]["Course"] is None
                            and classroom_availability[d][hour]
                            and course_id in faculty_availability[d][hour]
                            and faculty_availability[d][hour][course_id]
                        ]

                        if not available_hours:
                            break

                        day, hour = random.choice(available_hours)

                        selected_classroom = classroom_availability[day][hour].pop(0)
                        classroom_info = f"{selected_classroom['hall_id']}"

                        if (course_id, sem) not in selected_faculties:
                            selected_faculty = faculty_availability[day][hour][course_id].pop(0)
                            selected_faculties[(course_id, sem)] = selected_faculty
                        else:
                            selected_faculty = selected_faculties[(course_id, sem)]

                        class_obj[day][hour] = {
                            "Classroom": classroom_info,
                            "Faculty": selected_faculty,
                            "Course": course_id
                        }

                        if not faculty_availability[day][hour][course_id]:
                            del faculty_availability[day][hour][course_id]

                        unallocated_classes_per_week -= 1

def main():
    data = {'MCA': {1: {'lab_courses': [{'course_id': '23MX16', 'hours_per_week': 4}, 
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
                                    }}

    programme_data = get_courses(is_odd_semester=True)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    hours_per_day = 7

    programme_timelines = {}

    for programme in programme_data.keys():
        programme_timelines[programme] = {}
        for sem in programme_data[programme].keys():
            groups = get_groups_by_programme(programme, sem)
            programme_timelines[programme][sem] = {
                group: structure_timetable(days, hours_per_day)
                for group in groups
            }

    faculties = get_faculty_allocation_by_course()
    labs = get_labs()
    classrooms = get_classrooms()
    department_programme_map = get_department_programme_map()

    groups = {programme: get_groups_by_programme(programme, sem) for programme in programme_data for sem in programme_data[programme]}

    add_lab_courses(programme_timelines, programme_data, faculties, labs, department_programme_map, hours_per_day, groups)
    add_regular_classes(programme_timelines, programme_data, faculties, classrooms, hours_per_day, groups)

    print(json.dumps(programme_timelines, indent=4))

if __name__ == "__main__":
    main()
