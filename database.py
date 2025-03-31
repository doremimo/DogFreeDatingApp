import sqlite3

# Connect to or create the database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Create a table for users if it doesn't already exist
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        if INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        dog_free_reason TEXT
        )
""")

# Create a table to store reports
c.execute("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reported_user TEXT NOT NULL,
        reporter TEXT NOT NULL
        )
""")

# Add dog_free_reason column if it's not already there
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        dog_free_reason TEXT
    )
""")

conn.commit()
conn.close()