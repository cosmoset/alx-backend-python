import  sqlite3
import functools
import time
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

def retry_on_failure(retries=3, delay=2):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    print(f"Attempt {attempts} failed : {e}")
                    if attempts < retries:
                        print((f" Retrying in {delay} seconds..."))
                        time.sleep(delay)
                    else:
                        print("All attempts failed")
                        raise
        return wrapper
    return decorator

@with_db_connection
@retry_on_failure(retries=3, delay=3)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()


#### attempt to fetch users with automatic retry on failure

users = fetch_users_with_retry()
print(users)

