from flask import Flask, request, jsonify
import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
import openai

# Initialize Flask app
app = Flask(__name__)

# Load configuration from environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")  # e.g., "postgres://user:pass@host:port/dbname"
PERSPECTIVE_KEY = os.environ.get("PERSPECTIVE_KEY")  # Your Google Cloud Perspective API key
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")    # Your OpenAI API key
THRESHOLD = 0.7  # Toxicity threshold

# Configure OpenAI client
openai.api_key = OPENAI_API_KEY

# Initialize PostgreSQL connection
conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.route("/moderate", methods=["POST"])
def moderate():
    data = request.json or {}
    username = data.get("username")
    message = data.get("message")

    # 1) Call Perspective API to assess toxicity
    perspective_url = (
        f"https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
        f"?key={PERSPECTIVE_KEY}"
    )
    perspective_payload = {
        "comment": {"text": message},
        "languages": ["en"],
        "requestedAttributes": {"TOXICITY": {}}
    }
    p_resp = requests.post(perspective_url, json=perspective_payload)
    p_data = p_resp.json()
    toxicity = (
        p_data
        .get("attributeScores", {})
        .get("TOXICITY", {})
        .get("summaryScore", {})
        .get("value", 0.0)
    )

    flagged = False
    suggestion = None

    # 2) If toxic, generate a polite rewrite via OpenAI
    if toxicity > THRESHOLD:
        flagged = True
        prompt = (
            f"Rewrite the following message politely without changing its meaning:\n"  
            f"\"{message}\"\n"
        )
        chat_resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        suggestion = chat_resp.choices[0].message.content

    # 3) Persist moderation event to PostgreSQL
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chat_moderation (username, message, toxicity, suggestion) VALUES (%s, %s, %s, %s)",
            (username, message, toxicity, suggestion)
        )
        conn.commit()

    # 4) Respond
    return jsonify({
        "flagged": flagged,
        "toxicity": toxicity,
        "suggestion": suggestion
    })

if __name__ == "__main__":
    # Run the Flask development server
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)