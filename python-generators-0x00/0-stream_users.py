#!/usr/bin/python3
"""
Module to stream user data from a MySQL database using a generator.
"""
import mysql.connector
from mysql.connector import Error


def stream_users():
    """
    Generator function that fetches rows ony by one from user_data table
    Yields each row as a dictionary with the user's information.
    
    Returns:
        Generator yielding dictionaries with the user data:
        {
            'user_id': str,
            'name': str,
            'email': str,
            'age': int
        }
    """
    connection = connect_to_prodev()
    if connection:
        cursor = connection.cursor(dictionary=True)

        # SQL query to fetch all users
        sql_query = """
            SELECT *
            FROM user_data;
        """

        cursor.execute(sql_query)

        for row in cursor:
            yield {
                'user_id': row['user_id'],
                'name': row['name'],
                'email': row['email'],
                'age': row['age']
            }

        # Close the cursor and the connection
        cursor.close()
        connection.close()


def connect_to_prodev():
    """
    Connects to the ALX_prodev database in MySQL.
    
    Returns:
        connection: MySQL connection object to ALX_prodev if successfully, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="ALX_prodev",
        )
    
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to ALX_prodev: {e}")


def main():
    for user in stream_users():
        print(user)


if __name__ == "__main__":
    main()


# Make the module callable for the test code (1-main.py)
import sys
sys.modules[__name__] = stream_users