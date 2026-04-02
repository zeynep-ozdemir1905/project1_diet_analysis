from collections import defaultdict
import os
import pandas as pd
import requests
import redis
import json
import csv
from flask import Flask, redirect, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from azure.data.tables import TableClient
from werkzeug.security import generate_password_hash, check_password_hash
import azure.functions as func



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
table_client = TableClient.from_connection_string(conn_str=conn_str, table_name="User")

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
    


# @app.route('/api/analyze_data')
# def get_performance_stats():
#     print("API Endpoint /api/analyze_data called")  # Debugging line to confirm endpoint is hit
#     # map_csv_to_redis()

#     if not r.keys("session:*"):
#         return jsonify({"error": "Unauthorized"}), 401

#     try:
#         keys = r.keys("record:*")

#         if not keys:
#             return jsonify({
#                 "status": "empty",
#                 "message": "No data found in Redis"
#             }), 404

#         all_data = []
#         for key in keys:
#             record = r.hgetall(key)from collections import defaultdict

@app.route('/api/seed_redis')
def seed_redis():
    try:
        csv_path = os.path.join(basedir, 'All_Diets.csv')
        df = pd.read_csv(csv_path)
        df.dropna(subset=['Protein(g)', 'Carbs(g)', 'Fat(g)'], inplace=True)

        avg_macros_df = df.groupby('Diet_type').agg({
            'Protein(g)': 'mean',
            'Carbs(g)': 'mean',
            'Fat(g)': 'mean'
        }).round(2).reset_index()

        avg_macros = {
            row['Diet_type']: {
                "Protein(g)": row['Protein(g)'],
                "Carbs(g)": row['Carbs(g)'],
                "Fat(g)": row['Fat(g)']
            }
            for _, row in avg_macros_df.iterrows()
        }

        r.set("diet_analysis_results", json.dumps(avg_macros), ex=86400)
        return jsonify({"status": "ok", "diets_cached": list(avg_macros.keys())}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze_data')
def get_performance_stats():
    if not r.keys("session:*"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        cached_data = r.get("diet_analysis_results")

        if cached_data:
            data = json.loads(cached_data)
            # Convert dict format to list format for frontend compatibility
            result = [
                {
                    "Diet_type": diet,
                    "Protein(g)": macros["Protein(g)"],
                    "Carbs(g)": macros["Carbs(g)"],
                    "Fat(g)": macros["Fat(g)"]
                }
                for diet, macros in data.items()
            ]
            return jsonify(result), 200
        else:
            return jsonify({
                "status": "pending",
                "message": "Diet data not yet processed. Please upload CSV to Azure Blob."
            }), 202

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
#             all_data.append(record)

#         print("Fetched records:", all_data)

#         return jsonify(all_data), 200

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
    
#def map_csv_to_redis():
 #   print("Mapping CSV data to Redis...")

  #  basedir = os.path.abspath(os.path.dirname(__file__))
   # csv_path = os.path.join(basedir, 'All_Diets.csv')

    #df = pd.read_csv(csv_path)

    #for index, row in df.iterrows():
        # Use index OR a meaningful unique column
        #unique_id = index  
        # Example alternative:
        # unique_id = row["Recipe_name"]

        #redis_key = f"record:{unique_id}"

        # Convert row to dictionary
        #data_payload = row.to_dict()

        # Store in Redis hash
        #r.hset(redis_key, mapping=data_payload)

        # Debug confirmation
        #saved = r.hgetall(redis_key)
        #print(f"Saved {redis_key}: {saved}")

#def main(myblob: func.InputStream):
    #print(f"Processing blob: {myblob.name}")

    # Read blob directly
    #df = pd.read_csv(BytesIO(myblob.read()))

    #all_data = df.to_dict(orient="records")

    # Save to Redis
   # r.set("diet_analysis_results", json.dumps(all_data))

    #print("Data pushed to Redis")

# Change this to match your script.js API_URL
@app.route('/api/diet_results')
def get_diet_results():

    if not r.keys("session:*"):
        return jsonify({"error": "Unauthorized"}), 401

    try:
        cached_data = r.get("diet_analysis_results")

        if cached_data:
            data = json.loads(cached_data)
            print("FROM REDIS:", data)  # debug
            return jsonify(data), 200

        else:
            return jsonify({
                "status": "pending",
                "message": "No cached data found. Upload CSV to Azure Blob."
            }), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)