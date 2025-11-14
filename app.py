# app.py
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import pickle
import pandas as pd

from werkzeug.security import generate_password_hash, check_password_hash

from database import is_strong_password, register_user, get_user, init_db

app = Flask(__name__)
app.secret_key = "replace_with_a_long_random_secret"

# === MODEL + DATA LOADING (safe) ===
MODEL_PATH = "svc.pkl"
LABEL_PATH = "label_encoder.pkl"
DATA_DIR = "data"

def safe_load_pickle(path):
    try:
        with open(path, "rb") as f:
            return pickle.load(f)
    except Exception as e:
        print(f"Could not load {path}: {e}")
        return None

model = safe_load_pickle(MODEL_PATH)
le = safe_load_pickle(LABEL_PATH)

def safe_read_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    if os.path.exists(path):
        df = pd.read_csv(path)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        return df
    return pd.DataFrame()

desc_df = safe_read_csv("symptom_description.csv")
prec_df = safe_read_csv("symptom_precaution.csv")
med_df = safe_read_csv("medications.csv")
workout_df = safe_read_csv("workout_df.csv")
diet_df = safe_read_csv("diets.csv")
train_df = safe_read_csv("training.csv")

symptom_columns = [col for col in train_df.columns if col != 'prognosis']

# === ROUTES ===

@app.route("/")
def root():
    # if user logged in, go to /home else show login
    if session.get("user"):
        return redirect(url_for("home"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = get_user(username)
        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect(url_for("home"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            error = "Please enter username and password."
            return render_template("register.html", error=error)

        valid, msg = is_strong_password(password)
        if not valid:
            return render_template("register.html", error=msg)

        hashed = generate_password_hash(password)
        ok = register_user(username, hashed)
        if ok:
            success = "Account created. Please log in."
            return render_template("login.html", success=success)
        else:
            error = "Username already exists. Choose another."

    return render_template("register.html", error=error)

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/home")
def home():
    if not session.get("user"):
        return redirect(url_for("login"))
    return render_template("index.html", username=session.get("user"))

# ===== PREDICT API (used by frontend JS) =====
@app.route("/predict_api", methods=["POST"])
def predict_api():
    if not session.get("user"):
        return jsonify({"error": "Unauthorized"}), 401

    if model is None or le is None:
        return jsonify({"error": "Model not loaded"}), 500

    try:
        req = request.get_json()
        symptoms_input = req.get("symptoms", "").lower().strip()
        symptoms_list = [s.strip().replace(' ', '_') for s in symptoms_input.split(',') if s]

        # prepare input vector
        input_data = [0] * len(symptom_columns)
        for s in symptoms_list:
            if s in symptom_columns:
                input_data[symptom_columns.index(s)] = 1

        pred = model.predict([input_data])[0]
        predicted_disease = le.inverse_transform([pred])[0]
        disease_lower = predicted_disease.lower()

        def fetch_value(df, columns):
            if df.empty:
                return ["Not available"]
            col = next((c for c in columns if c in df.columns), None)
            if not col:
                return ["Not available"]
            matches = df.loc[df["disease"].str.lower() == disease_lower, col].dropna().tolist()
            return matches if matches else ["Not available"]

        res = {
            "disease": predicted_disease,
            "description": fetch_value(desc_df, ['description', 'desc'])[0],
            "precautions": fetch_value(prec_df, ['precaution_1', 'precaution1', 'precautions']),
            "medications": fetch_value(med_df, ['medication', 'medications', 'medicine']),
            "workouts": fetch_value(workout_df, ['workout', 'workouts', 'exercise']),
            "diets": fetch_value(diet_df, ['diet', 'diets'])
        }
        return jsonify(res)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# === Run ===
if __name__ == "__main__":
    # ensure DB exists
    init_db()
    app.run(debug=True)
