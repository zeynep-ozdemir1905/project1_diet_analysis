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

import azure.functions as func
import logging
import pandas as pd
import io
import json
import redis
import os

app = func.FunctionApp()

REDIS_HOST = 'diet-auth-cache-zeynep.redis.cache.windows.net'
REDIS_KEY = os.getenv("REDIS_KEY")

r = redis.Redis(
    host=REDIS_HOST,
    port=6380,
    password=REDIS_KEY,
    ssl=True,
    decode_responses=True
)

@app.blob_trigger(
    arg_name="myblob",
    path="uploads/{name}",
    connection="AzureWebJobsStorage"
)
def process_diet_data(myblob: func.InputStream):
    logging.info(f"Processing {myblob.name}")

    try:
        blob_bytes = myblob.read()
        all_chunks = []

        for chunk in pd.read_csv(io.BytesIO(blob_bytes), chunksize=500):
            chunk.dropna(subset=['Protein(g)', 'Carbs(g)', 'Fat(g)'], inplace=True)
            all_chunks.append(chunk)

        df = pd.concat(all_chunks)

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

        r.set("diet_analysis_results", json.dumps(avg_macros), ex=86400)  # 24hr TTL
        logging.info(f"SUCCESS: {len(avg_macros)} diet types written to Redis")

    except Exception as e:
        logging.error(f"Critical Error in process_diet_data: {str(e)}")