def fetch_all_courses(connection):
    cursor = connection.cursor(dictionary=True)  # Fetch results as dictionaries
    query = "SELECT * FROM Course"
    cursor.execute(query)
    results = cursor.fetchall()  # Fetch all rows from the executed query
    cursor.close()
    return results