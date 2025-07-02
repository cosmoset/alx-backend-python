import sqlite3


class DatabaseConnection:
    """
    A context manager class for handling database connections.
    Automatically opens and closes connections using the with statement.
    """
    
    def __init__(self, db_name):
        """
        Initialize the context manager with database name.
        
        Args:
            db_name: Name of the database file to connect to
        """
        self.db_name = db_name
        self.connection = None
    
    def __enter__(self):
        """
        Enter the context manager - open database connection.
        
        Returns:
            connection: The database connection object
        """
        print(f"Opening connection to {self.db_name}")
        self.connection = sqlite3.connect(self.db_name)
        return self.connection
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager - close database connection.
        
        Args:
            exc_type: Exception type (if any)
            exc_value: Exception value (if any)
            traceback: Exception traceback (if any)
        
        Returns:
            False: Propagate any exception that occurred
        """
        print(f"Closing connection to {self.db_name}")
        if self.connection:
            self.connection.close()
        
        # Return False to propagate any exception
        return False


# Using the context manager to perform a query
with DatabaseConnection('users.db') as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    results = cursor.fetchall()
    
    # Print the results
    print("\nQuery Results:")
    for row in results:
        print(row)