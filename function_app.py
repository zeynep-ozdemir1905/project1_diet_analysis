import azure.functions as func
import pandas as pd
import io
import os
import json
from azure.storage.blob import BlobServiceClient

app = func.FunctionApp()

@app.route(route="analyze_data", auth_level=func.AuthLevel.ANONYMOUS)
def analyze_data(req: func.HttpRequest) -> func.HttpResponse:
    connection_string = os.environ.get("StorageConnectionString")
    
    if not connection_string:
        return func.HttpResponse("Error: StorageConnectionString not set.", status_code=500)

    try:
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        blob_client = blob_service_client.get_blob_client(container="diets-data", blob="All_Diets.csv")
        
        download_stream = blob_client.download_blob()
        df = pd.read_csv(io.BytesIO(download_stream.readall()))

        # Calculate Calories based on your specific CSV columns
        # Formula: (Protein * 4) + (Carbs * 4) + (Fat * 9)
        df['Calculated_Calories'] = (df['Protein(g)'] * 4) + (df['Carbs(g)'] * 4) + (df['Fat(g)'] * 9)

        # Analysis: Average Macros and Calories by Diet Type
        analysis = df.groupby('Diet_type').agg({
            'Calculated_Calories': 'mean',
            'Protein(g)': 'mean',
            'Carbs(g)': 'mean',
            'Fat(g)': 'mean'
        }).round(2).to_dict(orient='index')

        return func.HttpResponse(
            json.dumps(analysis),
            mimetype="application/json",
            status_code=200
        )

    except Exception as e:
        return func.HttpResponse(f"Error: {str(e)}", status_code=500)
