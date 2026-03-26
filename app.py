import os
import requests
import redis
from flask import Flask, redirect, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# This finds the folder where app.py lives and looks for .env right there
basedir = os.path.abspath(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
load_dotenv(dotenv_path=".env.local")  # Load .env.local for development just pushing 

print(f"DEBUG: Looking for .env at: {env_path}") # This will tell us WHERE it's looking
print(f"DEBUG: Found Client Secret? {'Yes' if os.getenv('CLIENT_SECRET') else 'No'}")
app = Flask(__name__, static_folder='frontend/project2-frontend')
CORS(app)

# GitHub Credentials 
# Using getenv avoids GitHub's "Remote Rejected" error
CLIENT_ID = os.getenv("CLIENT_ID", "Ov23li2ew90EjCQGbYKi")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Azure Redis Connection
# Pulling the key from environment for security
REDIS_KEY = os.getenv("REDIS_KEY", "M6xAfWSvclkCtP2USeVMEad9VPx198N3rAzCaEcOYhk=")

r = redis.Redis(
    host='diet-auth-cache-zeynep.redis.cache.windows.net',
    port=6380,
    password=REDIS_KEY,
    ssl=True,
    decode_responses=True
)

# --- FRONTEND ROUTES ---

@app.route('/')
def home():
    # Serves the main dashboard index.html
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    # Serves CSS, JS (script.js), and images
    return send_from_directory(app.static_folder, path)

# --- AUTHENTICATION ROUTES ---

@app.route('/login')
def login():
    # Phase 3: Redirect to GitHub for Authorization
    github_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&scope=user"
    return redirect(github_url)

@app.route('/callback')
def callback():
    session_code = request.args.get('code')
    
    # Step 1: Exchange code for access token
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={
            "client_id": CLIENT_ID, 
            "client_secret": CLIENT_SECRET, 
            "code": session_code
        },
        headers={"Accept": "application/json"}
    )
    
    token_resp = response.json()
    access_token = token_resp.get("access_token")

    if not access_token:
        return f"Auth Failed: {token_resp.get('error_description', 'No token found')}", 400

    # Step 2: Get User Info
    user_response = requests.get(
        "https://api.github.com/user",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    if user_response.status_code != 200:
        return f"GitHub User Fetch Error: {user_response.status_code}", 500

    user_data = user_response.json()
    username = user_data.get('login')
    
    if username:
        # Store session in Azure Redis for 1 hour
        r.set(f"session:{username}", "active", ex=3600)
    
    return redirect('/')

@app.route('/logout')
def logout():
    """ Clears the session from Azure Redis to log the user out. """
    session_keys = r.keys("session:*")
    if session_keys:
        r.delete(*session_keys)
    return redirect('/')

# --- DATA API (The Firewall) ---

@app.route('/api/analyze_data')
def protected_data():
    # Check if any active session exists in Redis
    active_sessions = r.keys("session:*")
    
    if not active_sessions:
        return jsonify({"error": "Unauthorized"}), 401

    # If authorized, fetch data from Azure API
    try:
        azure_url = "https://diet-analysis-api-v2.azurewebsites.net/api/analyze_data"
        response = requests.get(azure_url)
        return jsonify(response.json())
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Could not reach Azure Data API"}), 500

if __name__ == "__main__":
    # Host 0.0.0.0 allows access from your phone/external local devices
    app.run(host='0.0.0.0', port=3000, debug=True)