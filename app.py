import os
import requests
import redis
from flask import Flask, redirect, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# --- CONFIGURATION & ENV SETUP ---
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path=".env.local") 

app = Flask(__name__, static_folder='frontend/project2-frontend')
CORS(app)

# GitHub Credentials
CLIENT_ID = os.getenv("CLIENT_ID", "Ov23li2ew90EjCQGbYKi")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Azure Redis Connection
REDIS_KEY = os.getenv("REDIS_KEY", "M6xAfWSvclkCtP2USeVMEad9VPx198N3rAzCaEcOYhk=")

r = redis.Redis(
    host='diet-auth-cache-zeynep.redis.cache.windows.net',
    port=6380,
    password=REDIS_KEY,
    ssl=True,
    decode_responses=True
)

@app.route('/')
def home():
    active_sessions = r.keys("session:*")
    if not active_sessions:
        return send_from_directory(app.static_folder, 'login.html')
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/login')
def login():
    github_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&scope=user"
    return redirect(github_url)

@app.route('/callback')
def callback():
    session_code = request.args.get('code')
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "code": session_code},
        headers={"Accept": "application/json"}
    )
    token_resp = response.json()
    access_token = token_resp.get("access_token")

    if not access_token:
        return "Auth Failed", 400

    user_resp = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {access_token}"})
    user_data = user_resp.json()
    username = user_data.get('login')
    
    if username:
        r.set(f"session:{username}", "active", ex=3600)
    
    return redirect('/')

@app.route('/logout')
def logout():
    session_keys = r.keys("session:*")
    if session_keys:
        r.delete(*session_keys)
    return redirect('/')

@app.route('/api/analyze_data')
def protected_data():
    if not r.keys("session:*"):
        return jsonify({"error": "Unauthorized"}), 401
    azure_url = "https://diet-analysis-api-v2.azurewebsites.net/api/analyze_data"
    response = requests.get(azure_url)
    return jsonify(response.json())

@app.route('/api/get_recipes')
def get_recipes():
    if not r.keys("session:*"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify([
        {"Recipe": "Quinoa Salad", "Diet": "Mediterranean", "Protein": "15g"},
        {"Recipe": "Beef Stir-fry", "Diet": "Paleo", "Protein": "30g"}
    ])

@app.route('/api/get_clusters')
def get_clusters():
    if not r.keys("session:*"): return jsonify({"error": "Unauthorized"}), 401
    return jsonify({"Cluster_1": "Lean Protein Focus", "Cluster_2": "High Fiber"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=3000, debug=True)