from flask import Flask, render_template, request, redirect, session, jsonify
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = "ai_modelhub_secret_key_2026"

DATABASE = "users.db"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


models = {
    "SentimentAI": {
        "name": "SentimentAI",
        "category": "Natural Language",
        "accuracy": "94%",
        "rating": "4.7",
        "trust": "92",
        "description": "Natural language model for sentiment analysis and text classification."
    },

    "VisionDetect": {
        "name": "VisionDetect",
        "category": "Computer Vision",
        "accuracy": "96%",
        "rating": "4.8",
        "trust": "95",
        "description": "Computer vision model for image classification and object detection."
    },

    "SpeechAI": {
        "name": "SpeechAI",
        "category": "Speech AI",
        "accuracy": "91%",
        "rating": "4.5",
        "trust": "88",
        "description": "Speech recognition model for converting spoken language into text."
    }
}


@app.route("/")
def home():
    user = session.get("user")

    return render_template(
        "Myhtm.html",
        user=user,
        auth=None,
        error=None
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return redirect("/#registerSection")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template(
            "Myhtm.html",
            user=None,
            auth="register",
            error="Please fill all fields."
        )

    if len(password) < 6:
        return render_template(
            "Myhtm.html",
            user=None,
            auth="register",
            error="Password must contain at least 6 characters."
        )

    conn = get_db()

    existing_user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if existing_user:
        conn.close()

        return render_template(
            "Myhtm.html",
            user=None,
            auth="register",
            error="An account with this email already exists."
        )

    hashed_password = generate_password_hash(password)

    conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (name, email, hashed_password)
    )

    conn.commit()
    conn.close()

    session["user"] = name

    return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":
        return redirect("/#loginSection")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template(
            "Myhtm.html",
            user=None,
            auth="login",
            error="Please enter email and password."
        )

    conn = get_db()

    user = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    conn.close()

    if user is None:
        return render_template(
            "Myhtm.html",
            user=None,
            auth="login",
            error="Invalid email or password."
        )

    if not check_password_hash(user["password"], password):
        return render_template(
            "Myhtm.html",
            user=None,
            auth="login",
            error="Invalid email or password."
        )

    session["user"] = user["name"]

    return redirect("/")


@app.route("/logout")
def logout():

    session.pop("user", None)

    return redirect("/")


@app.route("/model/<name>")
def model_details(name):

    model = models.get(name)

    if model is None:
        return jsonify({
            "error": "Model not found."
        }), 404

    return jsonify(model)


@app.route("/analyze", methods=["POST"])
def analyze():

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "No JSON data received."
            }), 400

        prompt = data.get("prompt", "").strip()

        if not prompt:
            return jsonify({
                "error": "Please enter a project idea."
            }), 400


        if not GROQ_API_KEY:

            return jsonify({
                "analysis": "This AI Model Marketplace idea is useful for students, developers and AI users. It provides a centralized platform to discover, compare and evaluate AI models. The project has good hackathon potential because it combines an AI-powered analyzer with a model marketplace.",
                "innovation": 90,
                "usefulness": 88,
                "user_experience": 86,
                "integration": 92,
                "quality": 89,
                "suggestions": [
                    "Add user authentication and personalized AI model recommendations.",
                    "Allow users to compare models based on accuracy, price, speed and trust score.",
                    "Add ratings, reviews and verified developer profiles for each AI model."
                ]
            })


        system_prompt = """
You are an expert college hackathon project evaluator.

Analyze the user's project idea.

Return ONLY valid JSON.

Use exactly these keys:

analysis
innovation
usefulness
user_experience
integration
quality
suggestions

The five score values must be integers from 0 to 100.

suggestions must contain exactly 3 useful improvement suggestions.

Do not use markdown.
Do not put JSON inside ``` blocks.
"""


        payload = {
            "model": "openai/gpt-oss-120b",
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 1000
        }


        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }


        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            print("GROQ ERROR:", response.status_code, response.text)
            return jsonify({
        "error": "Groq error: " + response.text
    }), 500


        result = response.json()

        ai_text = result["choices"][0]["message"]["content"].strip()


        if ai_text.startswith("```"):
            ai_text = ai_text.replace("```json", "")
            ai_text = ai_text.replace("```", "")
            ai_text = ai_text.strip()


        import json

        ai_data = json.loads(ai_text)


        return jsonify({
            "analysis": ai_data.get(
                "analysis",
                "No analysis available."
            ),

            "innovation": int(
                ai_data.get("innovation", 80)
            ),

            "usefulness": int(
                ai_data.get("usefulness", 80)
            ),

            "user_experience": int(
                ai_data.get("user_experience", 80)
            ),

            "integration": int(
                ai_data.get("integration", 80)
            ),

            "quality": int(
                ai_data.get("quality", 80)
            ),

            "suggestions": ai_data.get(
                "suggestions",
                []
            )
        })


    except json.JSONDecodeError:

        return jsonify({
            "error": "AI returned an invalid response. Please try again."
        }), 500


    except requests.exceptions.Timeout:

        return jsonify({
            "error": "AI request timed out. Please try again."
        }), 500


    except Exception as e:

        print("ANALYZE ERROR:", e)

        return jsonify({
            "error": "Something went wrong while analyzing the project."
        }), 500


if __name__ == "__main__":

    init_db()

    print("")
    print("======================================")
    print("       AI ModelHub is running")
    print("======================================")
    print("Open: http://127.0.0.1:5001")
    print("")

    app.run(
        host="127.0.0.1",
        port=5001,
        debug=True
    )
