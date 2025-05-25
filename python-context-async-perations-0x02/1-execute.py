import sqlite3

class ExecuteQuery:
    def __init__(self, db_path, query, params=None):
        self.db_path = db_path
        self.query = query
        self.params = params or ()
        self.conn = None
        self.result = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor() #Creates a cursor object used to execute SQL statements.
        cursor.execute(self.query, self.params) # Executes the SQL query (self.query) with parameters (self.params), such as ? placeholders for safe values.
        self.result = cursor.fetchall()  # Fetches all rows returned by the query and stores them in self.result.
        return self.result # The return value of __enter__() is what gets assigned to the variable in the with block,
    def __exit__(self, exc_type, exc_value, exc_tb):
        if self.conn:
            self.conn.close()


# === Example usage ===
query = "SELECT * FROM users WHERE age > ?"
params = (25,)

with ExecuteQuery("users.db", query, params) as result:
    print(result)
