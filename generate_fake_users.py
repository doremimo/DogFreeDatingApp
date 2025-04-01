import sqlite3
import random
import csv
import os
from faker import Faker
from werkzeug.security import generate_password_hash

# Initialize Faker
fake = Faker()

# Path to profile pics
PROFILE_PIC_DIR = "static/profilepics"
profile_pics = [f for f in os.listdir(PROFILE_PIC_DIR) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

# Constants
NUM_USERS = min(116, len(profile_pics))
password = "testpass"
hashed_password = generate_password_hash(password)

# Pools
dog_free_reasons = [
    "Allergic to dogs", "Prefer cats", "Fear of dogs", "Dogs too loud",
    "Bad past experience", "Love reptiles", "Travel too much", "Can't handle fur"
]
favorite_animals = ["Cat", "Snake", "Rabbit", "Parrot", "Turtle", "Lizard", "Ferret", "Guinea Pig"]
genders = ["Male", "Female", "Nonbinary", "Prefer not to say"]
interests_pool = ["reading", "hiking", "gaming", "cooking", "traveling", "painting", "music", "photography"]

# Connect to the database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Store login credentials for testing
credentials = []

# Generate and insert users
for i in range(NUM_USERS):
    username = f"testuser{i+1:03}"
    display_name = fake.first_name()
    age = random.randint(18, 50)
    location = fake.city()
    favorite_animal = random.choice(favorite_animals)
    dog_free_reason = random.choice(dog_free_reasons)
    profile_pic = profile_pics[i % len(profile_pics)]
    gender = random.choice(genders)
    interests = ", ".join(random.sample(interests_pool, k=random.randint(2, 4)))
    bio = fake.sentence(nb_words=12)

    try:
        c.execute("""
                INSERT INTO users (
                    username, password, display_name, age, location, favorite_animal,
                    dog_free_reason, profile_pic, bio, gender, interests
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
            username, hashed_password, display_name, age, location, favorite_animal,
            dog_free_reason, profile_pic, bio, gender, interests
        ))
        credentials.append([username, password])
    except sqlite3.IntegrityError:
        continue  # skip if username already exists

conn.commit()
conn.close()

# Delete old CSV if it exists
if os.path.exists("data/user_credentials.csv"):
    os.remove("data/user_credentials.csv")

# Save credentials to CSV
with open("data/user_credentials.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["username", "password"])
    writer.writerows(credentials)

print("✅ Successfully created 116 fake users.")
print("📄 Credentials saved to data/user_credentials.csv.")
