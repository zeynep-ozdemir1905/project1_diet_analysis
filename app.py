import os
import requests
import redis
import json
import csv
from flask import Flask, redirect, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from azure.data.tables import TableClient
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURATION & ENV SETUP ---
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(dotenv_path=os.path.join(basedir, ".env.local")) 

app = Flask(__name__, static_folder='frontend/project2-frontend')
CORS(app)

# GitHub Credentials
CLIENT_ID = os.getenv("CLIENT_ID", "Ov23li2ew90EjCQGbYKi")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")

# Azure Redis Connection
REDIS_KEY = os.getenv("REDIS_KEY", "M6xAfWSvclkCtP2USeVMEad9VPx198N3rAzCaEcOYhk=")
REDIS_HOST = 'diet-auth-cache-zeynep.redis.cache.windows.net'

r = redis.Redis(
    host=REDIS_HOST,
    port=6380,
    password=REDIS_KEY,
    ssl=True,
    decode_responses=True
)

# Azure Table Connection
conn_str = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_client = TableClient.from_connection_string(conn_str=conn_str, table_name="Users")

# --- AUTHENTICATION ROUTES (Email/Password) ---

@app.route('/login-email', methods=['POST'])
def login_email():
    email = request.form.get('email')
    password = request.form.get('password')
    try:
        user = table_client.get_entity(partition_key="User", row_key=email)
        if check_password_hash(user['password'], password):
            r.set(f"session:{email}", "active", ex=3600)
            return redirect('/')
        return "Invalid credentials", 401
    except Exception:
        return "User not found. Please register first.", 404
    
@app.route('/register-user', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    hashed_password = generate_password_hash(password)
    
    user_entity = {
        "PartitionKey": "User",
        "RowKey": email,
        "password": hashed_password
    }
    try:
        table_client.create_entity(entity=user_entity)
        return redirect('/login.html') 
    except Exception as e:
        return f"Error: {str(e)}", 400

# --- PAGE ROUTES ---

@app.route('/')
def home():
    active_sessions = r.keys("session:*")
    if not active_sessions:
        return send_from_directory(app.static_folder, 'login.html')
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# --- AUTHENTICATION ROUTES (GitHub OAuth) ---

@app.route('/login')
def login():
    github_url = f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}&scope=user"
    return redirect(github_url)

@app.route('/callback')
def callback():
    session_code = request.args.get('code')
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
        return "Authentication Failed", 400

    user_resp = requests.get(
        "https://api.github.com/user", 
        headers={"Authorization": f"Bearer {access_token}"}
    )
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

# --- DATA & PERFORMANCE ROUTES ---

@app.route('/api/get_recipes')
def get_top_recipes():
    try:
        # First try Redis
        data = r.get("top_protein_full")
        if data:
            return jsonify(json.loads(data))
        
        # Fallback to local CSV if Redis is empty
        recipes = []
        csv_path = os.path.join(basedir, 'top_protein_recipes.csv')
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                recipes.append(row)
        return jsonify(recipes)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze_data')
def get_performance_stats():
    """
    Performance Lead Task: Fetch pre-calculated data from Redis.
    This data is populated by the Azure Blob Trigger (function_app.py).
    """
    # 1. Security Check
    if not r.keys("session:*"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        # 2. Fetch from Cache (The key used in your Blob Trigger)
        cached_data = r.get("diet_analysis_results")

        if cached_data:
            # Data is already cleaned and calculated
            return jsonify(json.loads(cached_data))
        else:
            return jsonify({
                "status": "pending", 
                "message": "Analysis not ready. Please upload All_Diets.csv to trigger processing."
            }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze_data')
def protected_data():
    """Fallback to external API if needed"""
    if not r.keys("session:*"):
        return jsonify({"error": "Unauthorized"}), 401
    
    azure_url = "https://diet-analysis-api-v2.azurewebsites.net/api/analyze_data"
    try:
        response = requests.get(azure_url)
        return jsonify(response.json())
    except:
        return jsonify({"error": "External API unreachable"}), 502


@app.route('/api/macros')
def get_macros():
    data = r.get("average_macros")
    return jsonify(json.loads(data)) if data else jsonify({"error": "No data"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)