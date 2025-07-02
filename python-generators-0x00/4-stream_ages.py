#!/usr/bin/python3
"""
Module for memory-efficient aggregation using generators.
Calculates average age from the user database without loading entire dataset into memory.
"""
import mysql.connector
from mysql.connector import Error


def stream_user_ages():
    """
    Generator that yields user ages one by one from database.
    Memory-efficient - doesn't load all ages at once.
    
    Yields:
        int: Individual user age
    """
    connection = connect_to_prodev()
    if not connection:
        return
    
    try:
        cursor = connection.cursor(dictionary=True)

        # SQL query to fetch batch_size rows starting from offset position
        sql_query = "SELECT age FROM user_data"

        cursor.execute(sql_query)

        for row in cursor:
            yield row['age']

    except Error as e:
        print(f"Error streaming user ages: {e}")
        return
    finally:
        # Clean up ressources
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def calculate_average_age():
    """
    Calculate average age using the stream_user_ages generator.
    Memory-efficient - processes ages one by one without loading all into memory.
    
    Returns:
        float: Average age of all users
    """
    total_age = 0
    count = 0

    for age in stream_user_ages():
        total_age += age
        count += 1

    if count == 0:
        return 0
    
    return total_age / count


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
    calculate_average_age()


if __name__ == "__main__":
    main()