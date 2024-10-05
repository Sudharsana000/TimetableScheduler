import mysql.connector
from config import DB_CONFIG

def connect_to_db():
    try:
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        if connection.is_connected():
            print("Connected to the database")
            return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def close_connection(connection):
    if connection.is_connected():
        connection.close()
        print("Database connection closed")
