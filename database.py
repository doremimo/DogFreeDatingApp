import sqlite3

# Connect to or create the database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Create a table for users if it doesn't already exist
c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        display_name TEXT,
        age INTEGER,
        location TEXT,
        favorite_animal TEXT,
        dog_free_reason TEXT,
        profile_pic TEXT,
        bio TEXT,
        gender TEXT,
        interests TEXT
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

# Table to store likes
c.execute("""
    CREATE TABLE IF NOT EXISTS likes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        liker TEXT NOT NULL,
        liked TEXT NOT NULL
    )
""")

# Table for messages
c.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT NOT NULL,
        recipient TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
""")


conn.commit()
conn.close()