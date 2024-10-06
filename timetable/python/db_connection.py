import mysql.connector

# Function to create and return a database connection
def create_db_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',  # Replace with your host
            user='root',       # Replace with your MySQL username
            password='chuchu',  # Replace with your MySQL password
            database='timetable_db'  # Replace with your MySQL database name
        )
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None
