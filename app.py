import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key_here"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        dog_free = request.form.get("dog_free")

        if dog_free != "on":
            return "You must agree to the Dog-Free Oath."

        # Get all form data
        display_name = request.form.get("display_name", "")
        age = request.form.get("age", None)
        location = request.form.get("location", "")
        favorite_animal = request.form.get("favorite_animal", "")
        dog_free_reason = request.form.get("dog_free_reason", "")
        bio = request.form.get("bio", "")
        gender = request.form.get("gender", "")
        interests = request.form.get("interests", "")
        main_tag = request.form.get("main_tag", "")
        tags = request.form.getlist("tags")
        all_tags = [main_tag] + tags
        tags_string = ",".join(tags)

        # Validation: must include at least one pet-related tag
        pet_tags = {
            "Fully Pet-Free", "Allergic to Everything", "Reptile Roomie", "Cat Companion",
            "Rodent Roomie", "Bird Bestie", "Fish Friend", "Turtle Tenant", "Plant Person",
            "Bug Buddy", "My Pet’s a Vibe", "No Bark Zone", "Clean House > Cute Paws"
        }
        if not any(tag in pet_tags for tag in all_tags):
            return "You must select at least one pet-related tag (main or additional)."

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            hashed_password = generate_password_hash(password)

            c.execute("""
                INSERT INTO users (
                    username, password, display_name, age, location,
                    favorite_animal, dog_free_reason, profile_pic, bio,
                    gender, interests, main_tag, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                username, hashed_password, display_name, age, location,
                favorite_animal, dog_free_reason, "", bio, gender, interests,
                main_tag, tags_string
            ))

            conn.commit()
            conn.close()
            flash("Account created successfully!", "success")
            return redirect(url_for("login"))

        except sqlite3.IntegrityError:
            return "Username already exists!"

    return render_template("signup.html")



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        conn.close()

        if result and check_password_hash(result[0], password):
            session["username"] = username
            return redirect(url_for("profile"))

        else:
            return "Invalid username or password!"

    return render_template("login.html")

@app.route("/profile")
def profile():
    if "username" in session:
        username = session["username"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()

        # 🧠 Get profile data
        c.execute("""
            SELECT display_name, age, location, favorite_animal,
                   dog_free_reason, profile_pic, bio, gender,
                   interests, main_tag, tags,
                   gallery_image_1, gallery_image_2, gallery_image_3,
                   gallery_image_4, gallery_image_5
            FROM users WHERE username = ?
        """, (username,))
        result = c.fetchone()

        # ✅ Get count of unread messages
        c.execute("""
            SELECT COUNT(*) FROM messages 
            WHERE recipient = ? AND is_read = 0
        """, (username,))
        unread_count = c.fetchone()[0]

        conn.close()

        (display_name, age, location, favorite_animal, dog_free_reason,
         profile_pic, bio, gender, interests, main_tag, tags_string,
         g1, g2, g3, g4, g5) = result or (None,) * 16

        gallery_images = [g for g in [g1, g2, g3, g4, g5] if g]

        tags = tags_string.split(",") if tags_string else []

        return render_template("profile.html",
                               username=username,
                               display_name=display_name,
                               age=age,
                               location=location,
                               favorite_animal=favorite_animal,
                               dog_free_reason=dog_free_reason,
                               profile_pic=profile_pic,
                               bio=bio,
                               gender=gender,
                               interests=interests,
                               main_tag=main_tag,
                               tags=tags,
                               unread_count=unread_count,
                               gallery_images=gallery_images)
    else:
        return redirect(url_for("login"))


# Upload up to 5 Pictures
UPLOAD_FOLDER = 'static/gallery/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    if request.method == "POST":
        # === Text fields ===
        display_name = request.form.get("display_name", "")
        age = request.form.get("age", None)
        location = request.form.get("location", "")
        favorite_animal = request.form.get("favorite_animal", "")
        dog_free_reason = request.form.get("dog_free_reason", "")
        bio = request.form.get("bio", "")
        gender = request.form.get("gender", "")
        interests = request.form.get("interests", "")
        main_tag = request.form.get("main_tag", "")
        tags = request.form.getlist("tags")
        tags_string = ",".join(tags)

        # Pet tag validation
        pet_tags = {
            "Fully Pet-Free", "Allergic to Everything", "Reptile Roomie", "Cat Companion",
            "Rodent Roomie", "Bird Bestie", "Fish Friend", "Turtle Tenant", "Plant Person",
            "Bug Buddy", "My Pet’s a Vibe", "No Bark Zone", "Clean House > Cute Paws"
        }
        if not any(tag in pet_tags for tag in [main_tag] + tags):
            flash("You must select at least one pet-related tag.", "danger")
            return redirect(url_for("settings"))

        # === Update profile info ===
        c.execute("""
            UPDATE users SET
                display_name = ?, age = ?, location = ?, favorite_animal = ?,
                dog_free_reason = ?, bio = ?, gender = ?, interests = ?,
                main_tag = ?, tags = ?
            WHERE username = ?
        """, (
            display_name, age, location, favorite_animal, dog_free_reason,
            bio, gender, interests, main_tag, tags_string, username
        ))

        # === Handle gallery image uploads ===
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        for i in range(1, 6):
            file = request.files.get(f'gallery_image_{i}')
            if file and allowed_file(file.filename):
                filename = secure_filename(f"{username}_gallery_{i}_{file.filename}")
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                c.execute(f"UPDATE users SET gallery_image_{i} = ? WHERE username = ?", (f'gallery/{filename}', username))

        conn.commit()
        conn.close()
        flash("Profile updated!", "success")
        return redirect(url_for("profile"))

    # === GET request: load current data ===
    c.execute("""
        SELECT display_name, age, location, favorite_animal, dog_free_reason,
               bio, gender, interests, main_tag, tags
        FROM users WHERE username = ?
    """, (username,))
    data = c.fetchone()
    conn.close()

    return render_template("settings.html", data=data)

@app.route("/delete_gallery_image/<int:index>", methods=["POST"])
def delete_gallery_image(index):
    if "username" not in session:
        return redirect(url_for("login"))

    if not 1 <= index <= 5:
        flash("Invalid image index.", "danger")
        return redirect(url_for("profile"))

    username = session["username"]
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Get current image path
    c.execute(f"SELECT gallery_image_{index} FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    image_path = result[0] if result else None

    if image_path:
        # Try to delete file
        try:
            os.remove(os.path.join("static", image_path))
        except Exception as e:
            print("Error deleting file:", e)

        # Remove from DB
        c.execute(f"UPDATE users SET gallery_image_{index} = NULL WHERE username = ?", (username,))
        conn.commit()

    conn.close()
    flash("Photo deleted.", "success")
    return redirect(url_for("profile"))




@app.route("/browse", methods=["GET", "POST"])
def browse():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Get filter inputs
    min_age = request.form.get("min_age")
    max_age = request.form.get("max_age")
    location_input = request.form.get("location", "").strip().lower()
    gender_input = request.form.get("gender", "").strip().lower()
    interest_input = request.form.get("interest", "").strip().lower()

    # Get preferred and dealbreaker tags from input
    preferred_tags = request.form.getlist("preferred_tags")
    preferred_tags = [tag.strip().lower() for tag in preferred_tags if tag.strip()]

    dealbreaker_tags = request.form.getlist("dealbreaker_tags")
    dealbreaker_tags = [tag.strip().lower() for tag in dealbreaker_tags if tag.strip()]

    # Fetch all other users
    c.execute("""
        SELECT display_name, username, age, location, favorite_animal, 
               dog_free_reason, profile_pic, bio, gender, interests, main_tag, tags
        FROM users
        WHERE username != ?
    """, (session["username"],))
    all_users = c.fetchall()
    conn.close()

    # Score each user
    def score_user(user):
        score = 0
        display_name, username, age, loc, _, _, _, _, gender, interests, _, tags_str = user

        if min_age and age and int(age) >= int(min_age):
            score += 1
        if max_age and age and int(age) <= int(max_age):
            score += 1
        if location_input and loc and location_input in loc.lower():
            score += 1
        if gender_input and gender and gender_input == gender.lower():
            score += 1
        if interest_input and interests and interest_input in interests.lower():
            score += 1

        user_tags = tags_str.lower().split(",") if tags_str else []

        # 🚫 Exclude users with dealbreaker tags
        if any(tag in user_tags for tag in dealbreaker_tags):
            return -1

        # ✅ Add score for matching preferred tags
        for tag in preferred_tags:
            if tag in user_tags:
                score += 1

        return score

    # Pair users with their score and sort by best match
    scored_users = [
        (user, score) for user in all_users
        if (score := score_user(user)) >= 0
    ]
    scored_users.sort(key=lambda x: x[1], reverse=True)

    return render_template("browse.html", users=scored_users)

@app.route("/user/<username>")
def view_user_profile(username):
    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Get user info
    c.execute("""
        SELECT display_name, age, location, favorite_animal,
               dog_free_reason, profile_pic, bio, gender,
               interests, main_tag, tags,
               gallery_image_1, gallery_image_2, gallery_image_3,
               gallery_image_4, gallery_image_5
        FROM users WHERE username = ?
    """, (username,))
    result = c.fetchone()
    conn.close()

    if not result:
        flash("User not found.", "danger")
        return redirect(url_for("browse"))

    (display_name, age, location, favorite_animal, dog_free_reason,
     profile_pic, bio, gender, interests, main_tag, tags_string,
     g1, g2, g3, g4, g5) = result or (None,) * 16

    gallery_images = [g for g in [g1, g2, g3, g4, g5] if g]
    tags = tags_string.split(",") if tags_string else []

    return render_template("public_profile.html",
                           username=username,
                           display_name=display_name,
                           age=age,
                           location=location,
                           favorite_animal=favorite_animal,
                           dog_free_reason=dog_free_reason,
                           profile_pic=profile_pic,
                           bio=bio,
                           gender=gender,
                           interests=interests,
                           main_tag=main_tag,
                           tags=tags,
                           gallery_images=gallery_images)



@app.route("/matches")
def matches():
    if "username" not in session:
        return redirect(url_for("login"))

    current_user = session["username"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Get users who current_user liked
    c.execute("SELECT liked FROM likes WHERE liker = ?", (current_user,))
    liked_users = set([row[0] for row in c.fetchall()])

    # Get users who liked current_user
    c.execute("SELECT liker FROM likes WHERE liked = ?", (current_user,))
    liked_by_users = set([row[0] for row in c.fetchall()])

    # Find mutual matches
    mutual_matches = liked_users.intersection(liked_by_users)

    # Get display info for those matched users
    if mutual_matches:
        placeholders = ",".join("?" * len(mutual_matches))
        c.execute(f"""
            SELECT display_name, username, age, location, favorite_animal, dog_free_reason, profile_pic
            FROM users WHERE username IN ({placeholders})
        """, tuple(mutual_matches))
        match_list = c.fetchall()
    else:
        match_list = []

    conn.close()

    return render_template("matches.html", matches=match_list)


@app.route("/like/<username>", methods=["POST"])
def like(username):
    if "username" not in session:
        return redirect(url_for("login"))

    liker = session["username"]
    liked = username

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT 1 FROM likes WHERE liker = ? AND liked = ?", (liker, liked))
    already_liked = c.fetchone()

    if not already_liked:
        c.execute("INSERT INTO likes (liker, liked) VALUES (?, ?)", (liker, liked))
        conn.commit()
        flash(f"You liked @{liked}!")

    conn.close()
    return redirect(url_for("browse"))



@app.route("/messages/<username>", methods=["GET", "POST"])
def message_thread(username):
    if "username" not in session:
        return redirect(url_for("login"))

    current_user = session["username"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Handle new message being sent
    if request.method == "POST":
        message = request.form["message"]
        if message.strip():
            c.execute("INSERT INTO messages (sender, recipient, content) VALUES (?, ?, ?)",
                      (current_user, username, message))
            conn.commit()

    # Mark message from the other user as read
    c.execute("""
        UPDATE messages
        SET is_read = 1
        WHERE sender = ? AND recipient = ? AND is_read = 0
    """), (username, current_user)

    # Fetch conversation between current_user and the other user
    c.execute("""
        SELECT sender, content, timestamp FROM messages
        WHERE (sender = ? AND recipient = ?)
           OR (sender = ? AND recipient = ?)
        ORDER BY timestamp ASC
    """, (current_user, username, username, current_user))

    messages = c.fetchall()
    conn.close()

    return render_template("messages.html", messages=messages, other_user=username)



@app.route("/report/<username>", methods=["POST"])
def report(username):
    if "username" not in session:
        return redirect(url_for("login"))

    reporter = session["username"]

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("INSERT INTO reports (reported_user, reporter) VALUES (?, ?)", (username, reporter))
    conn.commit()
    conn.close()

    flash(f"You reported @{username}.")
    return redirect(url_for("browse"))


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

@app.route("/dev-login")
def dev_login():
    # Automatically log in as a fake user
    session["username"] = "testuser111"
    return redirect(url_for("profile"))

@app.route("/dev-login-1")
def dev_login_1():
    session["username"] = "testuser1"
    return redirect(url_for("profile"))

@app.route("/dev-login-2")
def dev_login_2():
    session["username"] = "testuser2"
    return redirect(url_for("profile"))

@app.route("/debug-likes")
def debug_likes():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT liker, liked FROM likes")
    rows = c.fetchall()
    conn.close()

    return "<br>".join([f"{liker} liked {liked}" for liker, liked in rows])



if __name__ == "__main__":
    app.run(debug=True)