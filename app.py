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



