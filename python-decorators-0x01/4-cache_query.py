import sqlite3
import functools
import time
import os

query_cache = {}

def with_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect('users.db')
            print("Databse connection established")
            return func(conn, *args, **kwargs)

        except sqlite3.Error as e:
            print(f"Database Error: {e}")
        finally:
            if conn:
                conn.close()
    return wrapper

def cache_query(func):
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        query = kwargs.get('query') if 'query' in kwargs else args[0] if args else None

        if query in query_cache:
            print(f"Cache hit for query: '{query}'")
            return query_cache[query]
        else:
            print(f"Cache miss for query: '{query}'. Fetching from database and caching...")
            result = func(conn,*args, **kwargs)
            query_cache[query] = result
            print(f"Query result for {query} added to cache")

            return  result

    return  wrapper

@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

#### First call will cache the result
users = fetch_users_with_cache(query="SELECT * FROM users")


#### Second call will use the cached result
users_again = fetch_users_with_cache(query="SELECT * FROM users")

