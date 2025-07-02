#!/usr/bin/python3
"""
Script to set up MySQL database and populate it with sample data.
"""
import mysql.connector
import csv
import os
from mysql.connector import Error


def connect_db():
    """
    Connects to the MySQL database server.
    
    Returns:
        connection: MySQL connection object if successful, None otherwise
    """
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print(f"Error connecting to MySQL: {e}")


def create_database(connection):
    """
    Creates the database ALX_prodev if it does not exist.
    
    args:
        connection: MySQL connection object
    """
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS ALX_prodev")
        cursor.close()
    except Error as e:
        print(f"Error creating database: {e}")


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


def create_table(connection):
    """
    Creates a table user_data if it does not exist with the required fields.
    
    Args:
        connection: MySQL connection object to ALX_prodev
    """
    try:
        cursor = connection.cursor()

        # Create table with specified fields
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_data (
                user_id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
                name VARCHAR(255) NOT NULL,
                email VARCHAR(255) NOT NULL,
                age TINYINT UNSIGNED NOT NULL,
                INDEX idx_user_id (user_id)
            )
        """)

        cursor.close()
        print("Table user_data created successfully")
    except Error as e:
        print(f"Error creating table: {e}")


def insert_data(connection, data):
    """
    Insert data in the database if it does not exist.

    Args:
        connection: MySQL connection object to ALX_prodev
        csv_file: Path to the CSV file containing the data
    """
    try:
        # Check if file exists
        if not os.path.exists(data):
            print(f"CSV file {data} not found")
            return
        
        cursor = connection.cursor()

        # Read data from CSV file:
        with open(data, 'r') as file:
            csv_reader = csv.reader(file)
            # Skip header row
            header = next(csv_reader)

            # Prepare SQL query for inserting data
            sql_query = """
                INSERT IGNORE INTO user_data(name, email, age)
                VALUES (%s, %s, %s)
            """

            # List of rows to insert to the table
            rows_to_insert = [tuple(row[:3]) for row in csv_reader if len(row) >= 3]

            # Execute batch insert for all rows
            cursor.executemany(sql_query, rows_to_insert)
            # Commit the transaction to save changes to database
            connection.commit()

            print(f"{cursor.rowcount} record inserted successfully")

        cursor.close()
    except Error as e:
        print(f"Error inserting data: {e}")
    except Exception as e:
        print(f"An error occured: {e}")


def main():
    # Connect to the database
    connection = connect_db()

    if connection:
        # Create the ALX_prodev Database if it does not exist
        create_database(connection)
        connection.close()

        # Connect to the ALX_prodev Database
        connection = connect_to_prodev()
        if connection:
            # Create table user_data if it does not exist
            create_table(connection)
            # Insert data to the table user_data
            insert_data(connection, 'user_data.csv')
            connection.close()

if __name__ == "__main__":
    main()
