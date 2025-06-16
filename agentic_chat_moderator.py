from flask import Flask, request, jsonify
import os
import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from OpenAI import OpenAI  # Updated import

# Initialize Flask app
app = Flask(__name__)

# Load environment variables
#DATABASE_URL = os.environ.get("DATABASE_URL")  # e.g., "postgres://user:pass@host:port/dbname"
PERSPECTIVE_KEY = os.environ.get("PERSPECTIVE_KEY")
XAI_API_KEY = os.environ.get("XAI_API_KEY")
THRESHOLD = 0.7  # Toxicity threshold

# Configure XAI client
client = XAI(
    api_key=XAI_API_KEY,  # actually using an XAI API key
    base_url="https://api.x.ai/v1",
)

# Initialize PostgreSQL connection
#conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

@app.route("/moderate", methods=["POST"])
def moderate():
    data = request.json or {}
    username = data.get("username")
    message = data.get("message")
    
    # Input validation
    if not message:
        return jsonify({"error": "Message is required"}), 400
    
    try:
        # 1) Call Perspective API to assess toxicity of user message
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
        
        # 2) If toxic, generate a polite rewrite via XAI
        if toxicity > THRESHOLD:
            flagged = True
            prompt = (
                f"Rewrite the following message politely without changing its meaning.\
                  Give no explanatory text, only your revision of this message:\n"  
                f'"{message}"\n'
            )
            
            try:
                print(f"Calling XAI with prompt: {prompt}")
                
                chat_resp = client.chat.completions.create(
                    model="grok-3-mini",
                    messages=[
                        # {
                        #     "role": "system",
                        #     "content": "You return the given message "
                        # },
                        {
                            "role": "user",
                            "content": prompt
                        },
                    ],
                    max_tokens=150,
                    temperature=0.7
                )
                suggestion = chat_resp.choices[0].message.content.strip()
                print(f"XAI response: {suggestion}")  # Debug line
                
            except Exception as XAI_error:
                print(f"XAI API Error: {str(XAI_error)}")  # Debug line
                suggestion = f"Error generating suggestion: {str(XAI_error)}"
        
        # 3) Persist moderation event to PostgreSQL
        # with conn.cursor() as cur:
        #     cur.execute(
        #         "INSERT INTO chat_moderation (username, message, toxicity, suggestion) VALUES (%s, %s, %s, %s)",
        #         (username, message, toxicity, suggestion)
        #     )
        #     conn.commit()
        
        # 4) Respond
        return jsonify({
            "flagged": flagged,
            "toxicity": toxicity,
            "suggestion": suggestion
        })
        
    except Exception as e:
        # Better error handling
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    # Fixed: double underscores, not asterisks
    port = int(os.environ.get("PORT", 3030))
    app.run(host="0.0.0.0", port=port)