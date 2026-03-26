from azure.storage.blob import BlobServiceClient

import pandas as pd

import io

import json

import os
 
def process_nutritional_data_from_azurite():

    # Correct Azurite connection

    blob_service_client = BlobServiceClient.from_connection_string(

        "UseDevelopmentStorage=true"

    )
 
    container_name = "datasets"

    blob_name = "All_Diets.csv"
 
    container_client = blob_service_client.get_container_client(container_name)

    blob_client = container_client.get_blob_client(blob_name)
 
    stream = blob_client.download_blob().readall()

    df = pd.read_csv(io.BytesIO(stream))
 
    df[['Protein(g)', 'Carbs(g)', 'Fat(g)']] = df[['Protein(g)', 'Carbs(g)', 'Fat(g)']].fillna(0)
 
    avg_macros = df.groupby('Diet_type')[['Protein(g)', 'Carbs(g)', 'Fat(g)']].mean()
 
    os.makedirs("simulated_nosql", exist_ok=True)
 
    result = avg_macros.reset_index().to_dict(orient='records')
 
    with open("simulated_nosql/results.json", "w") as f:

        json.dump(result, f, indent=4)
 
    return "Data processed and stored successfully."
 
print(process_nutritional_data_from_azurite())

 
