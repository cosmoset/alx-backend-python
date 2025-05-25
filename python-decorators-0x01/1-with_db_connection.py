import  sqlite3
import functools
import os

def with_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect('users.db')
            print("Connection Established")
            result = func(conn, *args, **kwargs)
            return result


        except sqlite3.Error as e:
            print(f"Database connection Error as : {e}")
        finally:
            if conn:
                conn.close()
    return wrapper

@with_db_connection
def get_user_by_Id(conn, user_id):
    my_cursor = conn.cursor()
    my_cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return my_cursor.fetchone()

if __name__ == '__main__':
    user = get_user_by_Id(user_id=3)
    print(user)


