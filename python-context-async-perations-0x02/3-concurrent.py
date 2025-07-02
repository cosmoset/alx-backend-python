import asyncio
import aiosqlite


async def async_fetch_users():
    """
    Asynchronously fetch all users from the database.
    
    Returns:
        list: All users from the users table
    """
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT * FROM users") as cursor:
            results = await cursor.fetchall()
            print("All users fetched")
            return results


async def async_fetch_older_users():
    """
    Asynchronously fetch users older than 40 from the database.
    
    Returns:
        list: Users with age > 40
    """
    async with aiosqlite.connect('users.db') as db:
        async with db.execute("SELECT * FROM users WHERE age > ?", (40,)) as cursor:
            results = await cursor.fetchall()
            print("Users older than 40 fetched")
            return results


async def fetch_concurrently():
    """
    Execute both queries concurrently using asyncio.gather.
    
    Returns:
        tuple: Results from both queries (all_users, older_users)
    """
    print("Starting concurrent database queries...")
    
    # Execute both queries concurrently
    all_users, older_users = await asyncio.gather(
        async_fetch_users(),
        async_fetch_older_users()
    )
    
    # Display results
    print("\n=== All Users ===")
    for user in all_users:
        print(f"ID: {user[0]}, Name: {user[1]}, Age: {user[2]}")
    
    print(f"\nTotal users: {len(all_users)}")
    
    print("\n=== Users Older Than 40 ===")
    for user in older_users:
        print(f"ID: {user[0]}, Name: {user[1]}, Age: {user[2]}")
    
    print(f"\nUsers older than 40: {len(older_users)}")
    
    return all_users, older_users


# Run the concurrent fetch
if __name__ == "__main__":
    asyncio.run(fetch_concurrently())