from flask import Flask, render_template, request, redirect, url_for, session
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




@app.route("/browse")
def browse():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        SELECT display_name, username, age, location, favorite_animal, 
        dog_free_reason, profile_pic
        FROM users
        WHERE username != ?
    """, (session["username"],))
    users = c.fetchall()
    conn.close()

    return render_template("browse.html", users=users)


@app.route("/like/<username>", methods=["POST"])
def like(username):
    if "username" not in session:
        return redirect(url_for("login"))

    liker = session["username"]
    liked = username

    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    # Prevent duplicate likes
    c.execute("SELECT 1 FROM likes WHERE liker = ? AND liked = ?", (liker, liked))
    already_liked = c.fetchone()

    if not already_liked:
        c.execute("INSERT INTO likes (liker, liked) VALUES (?, ?)", (liker, liked))
        conn.commit()

    conn.close()
    return redirect(url_for("browse"))


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