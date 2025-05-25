import sqlite3
import functools
import  os

def with_dc_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect('users.db')
            print('Database connection established')
            results = func(conn, *args, **kwargs)
            return results

        except sqlite3.Error as e:
            print(f"Database Error encountered: {e}")
        finally:
            if conn:
                conn.close()
    return wrapper

def transactional(func):
    @functools.wraps(func)
    def wrapper(conn, *args, **kwargs):
        try:
            results = func(conn, *args, **kwargs)

            conn.commit()
            return results
        except Exception as e:
            print(f"Error encountered is : {e}")
            conn.rollback()
            raise
    return wrapper

@with_dc_connection
@transactional
def  update_user_email(conn, user_id, new_email):
    my_cursor = conn.cursor()
    my_cursor.execute("UPDATE users SET email = ? WHERE id = ?", (new_email,user_id,))
    #return my_cursor.fetchone()

if __name__ == '__main__':
    user = update_user_email(user_id=2, new_email= 'samanthaaurelia@gmail.com')
    print(user)
