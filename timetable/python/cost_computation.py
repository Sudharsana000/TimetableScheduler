from collections import defaultdict

def compute_free_hours(timetable):
    free_hours = 0
    for programme, semesters in timetable.items():
        for semester, groups in semesters.items():
            for group, days in groups.items():
                for day, hours in days.items():
                    for hour, details in hours.items():
                        course = details.get('Course')
                        # Check if Course is None or an empty list (indicating a free hour)
                        if course is not None or (isinstance(course, list) and all(c is not None for c in course)):
                            free_hours += 1
    return free_hours

# Function to compute faculty distribution cost for a single timetable
def compute_faculty_distribution(timetable):
    cost = 0
    for programme, semesters in timetable.items():
        for semester, groups in semesters.items():
            faculty_usage = defaultdict(lambda: defaultdict(int))
            for group, days in groups.items():
                for day, hours in days.items():
                    for hour, details in hours.items():
                        faculty = details['Faculty']
                        if faculty is not None:
                            # If Faculty is a list, iterate over each faculty member
                            if isinstance(faculty, list):
                                for fac in faculty:
                                    faculty_usage[fac][day] += 1
                            else:
                                faculty_usage[faculty][day] += 1
            
            # Calculate uneven distribution cost
            for faculty, days in faculty_usage.items():
                day_count = list(days.values())
                max_classes_in_a_day = max(day_count)
                min_classes_in_a_day = min(day_count)
                cost += (max_classes_in_a_day - min_classes_in_a_day)  # Higher spread reduces the cost
    return cost

# Function to compute classroom switching cost for a single timetable
def compute_classroom_switching(timetable):
    cost = 0
    for programme, semesters in timetable.items():
        for semester, groups in semesters.items():
            for group, days in groups.items():
                for day, hours in days.items():
                    previous_classroom = None
                    for hour, details in hours.items():
                        classroom = details['Classroom']
                        if classroom is not None and previous_classroom is not None and classroom != previous_classroom:
                            cost += 1
                        previous_classroom = classroom
    return cost

def compute_total_cost(timetable, free_hours_weight, faculty_distribution_weight, classroom_switching_weight):
    free_hours_cost = compute_free_hours(timetable)
    faculty_distribution_cost = compute_faculty_distribution(timetable)
    classroom_switching_cost = compute_classroom_switching(timetable)

    total_cost = (free_hours_cost * free_hours_weight +
                  faculty_distribution_cost * faculty_distribution_weight +
                  classroom_switching_cost * classroom_switching_weight)
    
    return total_cost

# New function to compute costs for a single timetable
def compute_costs_for_single_timetable(timetable, free_hours_weight, faculty_distribution_weight, classroom_switching_weight):
    total_cost = compute_total_cost(timetable, free_hours_weight, faculty_distribution_weight, classroom_switching_weight)
    return {
        "total_cost": total_cost
    }
