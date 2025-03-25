from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "secret_key_here"

users = {}

@app.route("/")
def home():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        dog_free = request.form.get("dog_free")

        if username in users:
            return "Username already exists!"

        if dog_free != "on":
            return "You must agree to the Dog-Free Oath."

        users[username] = password
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username] == password:
            session["username"] = username
            return redirect(url_for("profile"))
        else:
            return "Invalid username or password!"

    return render_template("login.html")

@app.route("/profile")
def profile():
    if "username" in session:
        return f"Welcome, {session['username']}! You are dog-free and fabulous."
    else:
        return redirect(url_for("login"))




