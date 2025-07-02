import sqlite3


class ExecuteQuery:
    """
    A reusable context manager for executing database queries.
    Manages both connection and query execution with parameters.
    """
    
    def __init__(self, db_name, query, params=None):
        """
        Initialize the context manager with database name, query, and parameters.
        
        Args:
            db_name: Name of the database file
            query: SQL query to execute
            params: Parameters for the query (optional)
        """
        self.db_name = db_name
        self.query = query
        self.params = params if params is not None else ()
        self.connection = None
        self.cursor = None
        self.results = None
    
    def __enter__(self):
        """
        Enter the context manager - open connection and execute query.
        
        Returns:
            results: The results of the query execution
        """
        # Open database connection
        self.connection = sqlite3.connect(self.db_name)
        self.cursor = self.connection.cursor()
        
        # Execute the query with parameters
        if isinstance(self.params, (list, tuple)):
            self.cursor.execute(self.query, self.params)
        else:
            self.cursor.execute(self.query, (self.params,))
        
        # Fetch all results
        self.results = self.cursor.fetchall()
        
        return self.results
    
    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager - close cursor and connection.
        
        Args:
            exc_type: Exception type (if any)
            exc_value: Exception value (if any)
            traceback: Exception traceback (if any)
        
        Returns:
            False: Propagate any exception that occurred
        """
        # Close cursor if it exists
        if self.cursor:
            self.cursor.close()
        
        # Close connection if it exists
        if self.connection:
            self.connection.close()
        
        # Return False to propagate any exception
        return False


# Using the context manager to execute a query with parameters
query = "SELECT * FROM users WHERE age > ?"
param = 25

with ExecuteQuery('users.db', query, param) as results:
    print(f"Users older than {param}:")
    for user in results:
        print(f"  ID: {user[0]}, Name: {user[1]}, Age: {user[2]}")

# Example of using with multiple parameters
print("\nExample with multiple parameters:")
query2 = "SELECT * FROM users WHERE age > ? AND city = ?"
params2 = (20, 'New York')

with ExecuteQuery('users.db', query2, params2) as results:
    print(f"Users older than {params2[0]} from {params2[1]}:")
    for user in results:
        print(f"  {user}")