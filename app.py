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
                    username, password, display_name, age, location, favorite_animal, dog_free_reason
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (username, hashed_password, display_name, age, location, favorite_animal, dog_free_reason))

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
            SELECT display_name, age, location, favorite_animal, dog_free_reason
            FROM users WHERE username = ?
        """, (session["username"],))
        result = c.fetchone()
        conn.close()

        display_name, age, location, favorite_animal, dog_free_reason = result or (None, None, None, None, None)

        return render_template("profile.html",
                               username=session["username"],
                               display_name=display_name,
                               age=age,
                               location=location,
                               favorite_animal=favorite_animal,
                               dog_free_reason=dog_free_reason)
    else:
        return redirect(url_for("login"))



@app.route("/browse")
def browse():
    if "username" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        SELECT display_name, username, age, location, favorite_animal, dog_free_reason
        FROM users
        WHERE username != ?
    """, (session["username"],))
    users = c.fetchall()
    conn.close()

    return render_template("browse.html", users=users)


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

if __name__ == "__main__":
    app.run(debug=True)



