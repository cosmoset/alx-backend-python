#!/usr/bin/python3
"""
Module for batch processing users from MySQL database with filtering.
"""
import mysql.connector
from mysql.connector import Error


def stream_users_in_batches(batch_size):
    """
    Generator that yields batches of users from the database.

    Args:
        batch_size (int): Number of users to fetch in each batch

    Yields:
        list: List of user dictionaries, each containing:
              {
                'user_id': str,
                'name': str,
                'email': str,
                'age': int
              }
    """
    connection = connect_to_prodev()
    if not connection:
        return

    try:
        cursor = connection.cursor(dictionary=True)
        # Tracks current position in dataset 
        offset = 0

        while True:
            # SQL query to fetch batch_size rows starting from offset position
            sql_query = """
                SELECT *
                FROM user_data
                LIMIT %s OFFSET %s
            """

            cursor.execute(sql_query, (batch_size, offset))

            # Fetch all rows for current batch as list of dictionaries
            batch = cursor.fetchall()

            if not batch:
                break

            yield batch

            offset += batch_size
    except Error as e:
        print(f"Error streaming user in batches: {e}")
    finally:
        # Clean up ressources
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def batch_processing(batch_size):
    """
    Processes batches of users and filters those over the age of 25.
    Prints each filtered user to stdout.

    Args:
        batch_size (int): Size of batches to process
    """
    for batch in stream_users_in_batches(batch_size):
        for user in batch:
            if user['age'] > 25:
                print(user)


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
    batch_processing(50)


if __name__ == "main":
    main()