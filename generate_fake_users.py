import sqlite3
import random

# Connect to the database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Sample data
display_names = ["Luna", "Kai", "River", "Nova", "Archer"]
locations = ["Tokyo", "Berlin", "New York", "Osaka", "Vancouver"]
favorite_animals = ["Cat", "Snake", "Fox", "Rabbit", "Owl"]
dog_free_reasons = [
    "Allergic to dogs",
    "Prefer cats",
    "Don’t like barking",
    "Had a bad experience with dogs",
    "Just not a dog person"
]
profile_pics = ["pic1.jpg", "pic2.jpg", "pic3.jpg", "pic4.jpg", "pic5.jpg"]

# Generate and insert fake users
for i in range(5):
    username = f"testuser{i}"
    password = "hashed_password"
    display_name = display_names[i]
    age = random.randint(20, 40)
    location = random.choice(locations)
    favorite_animal = favorite_animals[i]
    reason = dog_free_reasons[i]
    pic = profile_pics[i]

    try:
        c.execute("""
        INSERT INTO users (
            username, password, display_name, age, location, favorite_animal, 
            dog_free_reason, profile_pic) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,(username, password, display_name, age, location, favorite_animal, reason, pic))
        print(f"Added {username}")
    except sqlite3.IntegrityError:
        print(f"{username} already exists – skipping")

conn.commit()
conn.close()
print("Fake users generated.")