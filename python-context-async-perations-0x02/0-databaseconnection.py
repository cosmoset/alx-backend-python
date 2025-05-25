import sqlite3

class DatabaseConnection:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None

    def __enter__(self):
        try:
            self.conn = sqlite3.connect(self.db_file)
            print("Database connection established")
            return self.conn
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.close()
            print("Database connection closed")

if __name__ == '__main__':
    with DatabaseConnection('users.db') as connection:
        my_cursor = connection.cursor()
        my_cursor.execute("SELECT * FROM users")
        users = my_cursor.fetchall()
        for user in users:
            print(user)


