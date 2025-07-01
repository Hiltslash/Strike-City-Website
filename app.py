#!/usr/bin/env python3

from flask import Flask, render_template, request, redirect, session
import json
import copy

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Replace with something secure in production


# --- Helper Functions ---
def loadData(file):
    with open(f"data/{file}.json", "r") as f:
        return json.load(f)

def saveData(file, data):
    with open(f"data/{file}.json", "w") as f:
        json.dump(data, f, indent=4)

def loadTEMPLATE(file):
    with open(f"datatemplates/{file}.json", "r") as f:
        return json.load(f)


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = loadData("users")
        uname = request.form.get('username')
        passw = request.form.get('password')

        if uname in data and data[uname]["accINFO"]["password"] == passw:
            session["username"] = uname
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid username or password.")
    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        uname = request.form.get('username')
        password = request.form.get('password')
        faction = request.form.get('faction')
        iname = request.form.get('iname')

        data = loadData("users")
        if uname in data:
            return render_template("signup.html", error="Username already taken!")

        template = loadTEMPLATE("users")["username"]
        data[uname] = copy.deepcopy(template)

        user_data = data[uname]
        user_data["accINFO"].update({
            "username": uname,
            "password": password,
            "iname": iname,
            "id": len(data) + 1
        })
        user_data["psicoins"] = 1000
        user_data["faction"] = faction

        saveData("users", data)
        return redirect("/login")
    return render_template("signup.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    username = session.get("username")
    if not username:
        return redirect("/login")

    data = loadData("users")
    weapons = loadData("weapons")

    if request.method == "POST" and request.form.get('formType') == "BattleLOG":
        user = username
        opponent = request.form.get('opp')
        btype = request.form.get('btype')
        status = request.form.get('status')     
        cmoneytransfer = request.form.get('cmoneytransfer')

        try:
            cmoneytransfer = int(cmoneytransfer) if cmoneytransfer else 0
        except ValueError:
            cmoneytransfer = 0

        if opponent not in data:
            return render_template("dashboard.html", error="Opponent not found.", username=user, uDATA=data, wDATA=weapons)

        def adjust_stats(winner, loser, coins, kdr, life_type=None):
            data[loser]["psicoins"] -= coins
            data[winner]["psicoins"] += coins * 3
            data[loser]["kdr"] -= kdr
            data[winner]["kdr"] += kdr
            if life_type:
                data[winner][life_type] += 1
                data[loser][life_type] += 1

        if btype == "normal":
            adjust_stats(user, opponent, 100, 1) if status else adjust_stats(opponent, user, 100, 1)
        elif btype == "allout":
            adjust_stats(user, opponent, 300, 2, "nLives") if status else adjust_stats(opponent, user, 300, 2, "nLives")
        elif btype == "cannon":
            adjust_stats(user, opponent, 750, 5, "cLives") if status else adjust_stats(opponent, user, 750, 5, "cLives")
        elif btype == "custom":
            adjust_stats(user, opponent, cmoneytransfer, 1) if status else adjust_stats(opponent, user, cmoneytransfer, 1)

        for usr in [user, opponent]:
            if data[usr]["nLives"] == 0:
                data[usr]["nLives"] = 5
                data[usr]["cLives"] -= 1
            if data[usr]["cLives"] <= 0:
                data[usr] = {}

        saveData("users", data)

    return render_template("dashboard.html", username=username, uDATA=data, wDATA=weapons)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


# --- Run ---
if __name__ == '__main__':
    app.run(debug=True, port=5001)
