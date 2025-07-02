#!/usr/bin/env python3
# © 2025 Beau Davidson
from flask import Flask, render_template, request, redirect, session
import json
import copy

app = Flask(__name__)
app.secret_key = "pepperthelilguy"


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
@app.route("/shop", methods=["GET", "POST"])
def shop():
    username = session.get("username")
    if not username:
        return redirect("/login")

    users = loadData("users")
    weapons = loadData("weapons")
    user = users.get(username, {})
    message = None

    if request.method == "POST":
        weapon_id = request.form.get("weapon_id")
        # Find weapon by id
        weapon = None
        for w in weapons.values():
            if w.get("id") == weapon_id:
                weapon = w
                break
        if not weapon:
            message = "Weapon not found."
        else:
            # Check if user already owns weapon (by id in inventory)
            if "inventory" not in user:
                user["inventory"] = []
            if weapon_id in user["inventory"]:
                message = "You already own this weapon."
            else:
                # Parse cost (ignore +permission etc)
                cost_str = str(weapon["Cost"]).split("+")[0].strip()
                try:
                    cost = int(cost_str)
                except Exception:
                    cost = 0
                if user.get("psicoins", 0) < cost:
                    message = "Not enough psicoins."
                else:
                    user["psicoins"] -= cost
                    user["inventory"].append(weapon_id)
                    users[username] = user
                    saveData("users", users)
                    message = f"Purchased {weapon['name']}!"

    return render_template("shop.html", username=username, weapons=weapons, user=user, message=message)

from flask import jsonify

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if "username" not in session:
        return redirect("/login")
    chathistory = loadData("chat")
    # AJAX polling support
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Only render the chat messages part, but ensure it returns a full <div id="chat-messages">...</div>
        return f'<div id="chat-messages">' + render_template("_chat_messages.html", chathistory=chathistory) + '</div>'
    if request.method == "POST":
        message = request.form.get('message')
        sender = session.get('username')
        if not message or not sender:
            return render_template("chat.html", chathistory=chathistory, username=sender, error="Message cannot be empty.")
        if len(chathistory) >= 10:
            chathistory.pop()        
        chathistory.insert(0, {"sender": sender, "message": message})
        saveData("chat", chathistory)
        return redirect("/chat")

    return render_template("chat.html", chathistory=chathistory, username=session.get('username'))

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
    user = data.get(username, {})
    error = None

    # Equip weapon logic
    if request.method == "POST" and request.form.get('formType') == "equipWeapon":
        equip_idx = request.form.get('equip_idx')
        try:
            equip_idx = int(equip_idx)
            if 0 <= equip_idx < len(user.get("inventory", [])):
                user["equipped"] = [equip_idx]
                data[username] = user
                saveData("users", data)
        except Exception:
            error = "Invalid weapon selection."

    if request.method == "POST" and request.form.get('formType') == "BattleLOG":
        usern = username
        opponent = request.form.get('opp')
        btype = request.form.get('btype')
        status = request.form.get('status')     
        cmoneytransfer = request.form.get('cmoneytransfer')

        try:
            cmoneytransfer = int(cmoneytransfer) if cmoneytransfer else 0
        except ValueError:
            cmoneytransfer = 0

        if opponent not in data:
            return render_template("dashboard.html", error="Opponent not found.", username=usern, uDATA=data, wDATA=weapons)

        def adjust_stats(winner, loser, coins, kdr, life_type=None):
            data[loser]["psicoins"] -= coins
            data[winner]["psicoins"] += coins * 3
            data[loser]["kdr"] -= kdr
            data[winner]["kdr"] += kdr
            if life_type:
                data[winner][life_type] += 1
                data[loser][life_type] += 1

        if btype == "normal":
            adjust_stats(usern, opponent, 100, 1) if status else adjust_stats(opponent, usern, 100, 1)
        elif btype == "allout":
            adjust_stats(usern, opponent, 300, 2, "nLives") if status else adjust_stats(opponent, usern, 300, 2, "nLives")
        elif btype == "cannon":
            adjust_stats(usern, opponent, 750, 5, "cLives") if status else adjust_stats(opponent, usern, 750, 5, "cLives")
        elif btype == "custom":
            adjust_stats(usern, opponent, cmoneytransfer, 1) if status else adjust_stats(opponent, usern, cmoneytransfer, 1)

        for usr in [usern, opponent]:
            if data[usr]["nLives"] == 0:
                data[usr]["nLives"] = 5
                data[usr]["cLives"] -= 1
            if data[usr]["cLives"] <= 0:
                data[usr] = {}

        saveData("users", data)

    if request.method == "POST" and request.form.get('formType') == "adminPanelWeapon":
        pass

    return render_template("dashboard.html", username=username, uDATA=data, wDATA=weapons, error=error)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/")


# --- Run ---
if __name__ == '__main__':
    app.run(debug=True, port=5009, host="0.0.0.0")
