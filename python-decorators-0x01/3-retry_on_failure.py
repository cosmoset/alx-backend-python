#!/usr/bin/python3
"""
Implementation of retry decorator
"""
import time
import sqlite3 
import functools

def with_db_connection(func):
    """Decorator that automatically handles database connections."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = sqlite3.connect('users.db')
        try:
            return func(conn, *args, **kwargs)
        finally:
            conn.close()
    
    return wrapper

def retry_on_failure(retries=3, delay=1):
    """
    Decorator that retries a function if it fails.
    
    Args:
        retries: Number of retry attempts (default: 3)
        delay: Delay in seconds between retries (default: 2)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    print(f"Attempt {attempt + 1} failed: {e}")

                    if attempt < retries -1:
                        print(f"Retrying in {delay} seconds ...")
                        time.sleep(delay)
                    else:
                        print(f"All {retries} attempts failed.")
            
            raise last_exception
        return wrapper
    return decorator


@with_db_connection
@retry_on_failure(retries=3, delay=1)
def fetch_users_with_retry(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    return cursor.fetchall()

#### attempt to fetch users with automatic retry on failure

users = fetch_users_with_retry()
print(users)