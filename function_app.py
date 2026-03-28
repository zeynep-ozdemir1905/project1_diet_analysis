import azure.functions as func
import logging
import pandas as pd
import io
import json
import redis
import os

# --- INITIALIZE FUNCTION APP ---
app = func.FunctionApp()

# --- REDIS CONFIGURATION ---
# Note: Using os.getenv ensures your local.settings.json values are used
REDIS_HOST = 'diet-auth-cache-zeynep.redis.cache.windows.net'
REDIS_KEY = os.getenv("REDIS_KEY", "M6xAfWSvclkCtP2USeVMEad9VPx198N3rAzCaEcOYhk=")

# Setup Redis Client (SSL is required for Azure Redis)
try:
    r = redis.Redis(
        host=REDIS_HOST,
        port=6380,
        password=REDIS_KEY,
        ssl=True,
        decode_responses=True
    )
except Exception as e:
    logging.error(f"Failed to connect to Redis: {str(e)}")

@app.blob_trigger(arg_name="myblob", 
                  path="uploads/All_Diets.csv", 
                  connection="AzureWebJobsStorage") 
def process_diet_data(myblob: func.InputStream):
    """
    Performance Lead Logic: 
    Wakes up when All_Diets.csv is uploaded, cleans data, 
    and populates Redis with analyzed results.
    """
    logging.info(f"Performance Lead: Processing {myblob.name} ({myblob.length} bytes)")

    try:
        # 1. READ DATA
        # Reading from the trigger stream into a Pandas DataFrame
        blob_bytes = myblob.read()
        df = pd.read_csv(io.BytesIO(blob_bytes))

        # 2. DATA CLEANING (Phase 2 Requirement)
        # Ensure we don't have empty macro values before calculating
        df.dropna(subset=['Protein(g)', 'Carbs(g)', 'Fat(g)'], inplace=True)
        
        # 3. ANALYSIS: AVERAGE MACROS (equivalent to average_macros.csv)
        avg_macros = df.groupby('Diet_type').agg({
            'Protein(g)': 'mean',
            'Carbs(g)': 'mean',
            'Fat(g)': 'mean'
        }).round(2).to_dict(orient='index')

        # 4. ANALYSIS: TOP 5 PROTEIN (equivalent to top_5_protein_recipes.csv)
        top_5 = df.nlargest(5, 'Protein(g)')[['Recipe_name', 'Protein(g)', 'Diet_type']].to_dict(orient='records')

        # 5. ANALYSIS: TOP 20 PROTEIN (equivalent to top_protein_recipes.csv)
        top_full = df.nlargest(20, 'Protein(g)')[['Recipe_name', 'Protein(g)', 'Diet_type']].to_dict(orient='records')

        # 6. CACHING: Push JSON strings to Redis
        # We store them as separate keys so the frontend can request only what it needs
        r.set("average_macros", json.dumps(avg_macros))
        r.set("top_5_protein", json.dumps(top_5))
        r.set("top_protein_full", json.dumps(top_full))

        logging.info("SUCCESS: Redis cache updated with cleaning and analysis results.")

    except Exception as e:
        logging.error(f"Critical Error in process_diet_data: {str(e)}")