from flask import Flask, render_template, request, redirect, url_for, make_response
import requests
import sqlite3
from datetime import datetime

app = Flask(__name__)
GROQ_API_KEY = "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"

# Initialize SQLite database
def init_db():
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# Call this when the app starts
init_db()

def call_groq_api(user_message):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": user_message}]
    }
    response = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
    result = response.json()
    return result.get("choices", [{}])[0].get("message", {}).get("content", "⚠️ 無法取得回覆")

@app.route("/", methods=["GET", "POST"])
def chat():
    with sqlite3.connect("chat_history.db") as conn:
        cursor = conn.cursor()
        cleared_message = None
        if request.method == "POST":
            if "clear" in request.form:
                print("Clearing all messages from database")  # Debug log
                cursor.execute("DELETE FROM messages")  # Clear all messages
                conn.commit()
                cleared_message = "對話紀錄已清除"
                response = make_response(render_template("index.html", messages=[], cleared_message=cleared_message))
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                return response

            user_message = request.form.get("user_message", "").strip()
            if user_message:  # Only process if user_message is not empty
                cursor.execute("INSERT INTO messages (sender, message) VALUES (?, ?)", ("👤", user_message))
                conn.commit()
                reply = call_groq_api(user_message)
                cursor.execute("INSERT INTO messages (sender, message) VALUES (?, ?)", ("🤖", reply))
                conn.commit()

        cursor.execute("SELECT sender, message FROM messages ORDER BY timestamp")
        messages = cursor.fetchall()

    response = make_response(render_template("index.html", messages=messages, cleared_message=cleared_message))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

if __name__ == "__main__":
    app.run(debug=True)