import json
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os, math
from pathlib import Path

# --- Setup ---
os.chdir(Path(__file__).parent)
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'Template'))
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = "super_secret_key"
USERS_FILE = "users.json"  # store registered users

# --- Helper: Load & Save users ---
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# --- Diabetes Model ---
COEFFICIENTS = {"intercept": -8.0, "weights": [0.12, 0.045, -0.02, 0.01, -0.001, 0.13, 0.8, 0.03]}
def sigmoid(z): return 1 / (1 + math.exp(-z))
def predict_probability(features):
    z = COEFFICIENTS["intercept"]
    for w, f in zip(COEFFICIENTS["weights"], features):
        z += w * float(f)
    return sigmoid(z)

# --- Routes ---
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("index.html", user=session["user"])

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    ordered = ["pregnancies", "glucose", "bloodPressure", "skinThickness",
               "insulin", "bmi", "diabetesPedigree", "age"]
    features = [data.get(k, 0) for k in ordered]
    prob = predict_probability(features)
    label = int(prob >= 0.5)
    return jsonify({"probability": round(prob, 3), "prediction": label})

# --- Authentication ---
@app.route("/login")
def login_page():
    return render_template("login.html")

@app.route("/login_submit", methods=["POST"])
def login_submit():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    if username in users and users[username] == password:
        session["user"] = username
        return jsonify({"success": True, "message": "Login successful!"})
    return jsonify({"success": False, "error": "Invalid credentials"})

@app.route("/signup", methods=["POST"])
def signup_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    users = load_users()
    if username in users:
        return jsonify({"success": False, "error": "Username already exists!"})
    users[username] = password
    save_users(users)

    return jsonify({"success": True, "message": "Account created successfully! You can now log in."})

@app.route("/logout_page")
def logout_page():
    if "user" not in session:
        return redirect(url_for("login_page"))
    return render_template("logout.html")

@app.route("/logout", methods=["POST"])
def logout_user():
    session.pop("user", None)
    return jsonify({"success": True, "message": "Logged out successfully!"})




# --- Run app ---
if __name__ == '__main__':
    app.run()
