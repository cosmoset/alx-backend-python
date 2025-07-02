#!/usr/bin/python3
"""
Cache Query Decorator
"""
import time
import sqlite3 
import functools
import inspect


query_cache = {}


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


def cache_query(func):
    """"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()

        # Get function signature
        sig = inspect.signature(func)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()

        query = bound.arguments.get("query")

        if query_cache.get(query):
            end_time = time.time()
            execution_time = (end_time - start_time) * 1000 # Convert to milliseconds
            print(f"Cache hit for query: {query}")
            print(f"Execution time: {execution_time:.2f}ms (from cache)")
            return query_cache[query]
        
        result = func(*args, **kwargs)
        query_cache[query] = result

        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        print(f"Execution time: {execution_time:.2f}ms (from database)")

        return result
    
    return wrapper


@with_db_connection
@cache_query
def fetch_users_with_cache(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    return cursor.fetchall()

#### First call will cache the result
users = fetch_users_with_cache(query="SELECT * FROM users")
print(users)

#### Second call will use the cached result
users_again = fetch_users_with_cache(query="SELECT * FROM users")
print(users)