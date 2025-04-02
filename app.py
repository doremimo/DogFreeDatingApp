from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
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
        bio = request.form.get("bio", "")
        gender = request.form.get("gender", "")
        interests = request.form.get("interests", "")

        if dog_free != "on":
            return "You must agree to the Dog-Free Oath."

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            display_name = request.form.get("display_name", "")
            age = request.form.get("age", None)
            location = request.form.get("location", "")
            favorite_animal = request.form.get("favorite_animal", "")
            dog_free_reason = request.form.get("dog_free_reason", "")
            hashed_password = generate_password_hash(password)
            c.execute("""
                INSERT INTO users (
                    username, password, display_name, age, location, favorite_animal,
                    dog_free_reason, profile_pic, bio, gender, interests
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (username, hashed_password, display_name, age, location, favorite_animal,
                  dog_free_reason, None, bio, gender, interests))

            conn.commit()
            conn.close()
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
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("""
            SELECT display_name, age, location, favorite_animal,
                   dog_free_reason, profile_pic, bio, gender, interests
            FROM users
            WHERE username = ?
        """, (session["username"],))
        result = c.fetchone()
        conn.close()

        (display_name, age, location, favorite_animal,
         dog_free_reason, profile_pic, bio, gender, interests) = result or (None,) * 9

        return render_template("profile.html",
                               username=session["username"],
                               display_name=display_name,
                               age=age,
                               location=location,
                               favorite_animal=favorite_animal,
                               dog_free_reason=dog_free_reason,
                               profile_pic=profile_pic,
                               bio=bio,
                               gender=gender,
                               interests=interests)
    else:
        return redirect(url_for("login"))


@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        display_name = request.form.get("display_name")
        age = request.form.get("age")
        location = request.form.get("location")
        favorite_animal = request.form.get("favorite_animal")
        dog_free_reason = request.form.get("dog_free_reason")
        bio = request.form.get("bio")
        gender = request.form.get("gender")
        interests = request.form.get("interests")

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("""
            UPDATE users SET display_name=?, age=?, location=?, favorite_animal=?, 
                            dog_free_reason=?, bio=?, gender=?, interests=? 
            WHERE username=?
        """, (display_name, age, location, favorite_animal, dog_free_reason,
              bio, gender, interests, session["username"]))
        conn.commit()
        conn.close()

        flash("Profile updated!")
        return redirect(url_for("profile"))

    # GET method: load the existing values to fill the form
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        SELECT display_name, age, location, favorite_animal, dog_free_reason,
               bio, gender, interests
        FROM users WHERE username = ?
    """, (session["username"],))
    result = c.fetchone()
    conn.close()

    return render_template("settings.html", data=result)


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

    # Fetch all other users
    c.execute("""
        SELECT display_name, username, age, location, favorite_animal, 
               dog_free_reason, profile_pic, bio, gender, interests
        FROM users
        WHERE username != ?
    """, (session["username"],))
    all_users = c.fetchall()
    conn.close()

    # Score each user
    def score_user(user):
        score = 0
        display_name, username, age, loc, _, _, _, _, gender, interests = user

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

        return score

    # Pair users with their score and sort by score
    scored_users = [(user, score_user(user)) for user in all_users]
    scored_users.sort(key=lambda x: x[1], reverse=True)

    return render_template("browse.html", users=scored_users)



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