#!/usr/bin/python3
"""
Module for lazy pagination of user data using generators.
This implementation uses yield to create generators for efficient pagination.
"""
import mysql.connector
from mysql.connector import Error


def paginate_users(page_size, offset):
    """
    Fetches one page of users from database.
    
    Args:
        page_size (int): Number of users to fetch
        offset (int): Starting position in database
        
    Returns:
        list: List of user dictionaries for this page
    """
    connection = connect_to_prodev()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)

        # SQL query to fetch page_size rows starting from offset position
        sql_query = "SELECT * FROM user_data LIMIT %s OFFSET %s"

        cursor.execute(sql_query, (page_size, offset))

        # Fetch all rows for current page as list of dictionaries
        page = cursor.fetchall()

        return page

    except Error as e:
        print(f"Error paginating users: {e}")
        return []
    finally:
        # Clean up ressources
        if cursor:
            cursor.close()
        if connection:
            connection.close()


def lazy_pagination(page_size):
    """
    Generator that yields pages of users one by one.
    Only fetches next page when needed (lazy loading).
    
    Args:
        page_size (int): Number of users per page
        
    Yields:
        list: List of user dictionaries for each page
    """
    offset = 0
    while True:
        page = paginate_users(page_size, offset)

        if not page:
            break

        yield page

        offset += page_size


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
    for page in lazy_pagination(100):
        for user in page:
            print(user)


if __name__ == "__main__":
    main()