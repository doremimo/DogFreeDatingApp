import sqlite3

# Connect to or create the database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Create a table for users if it doesn't already exist
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        if INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
        )
""")

conn.commit()
conn.close()