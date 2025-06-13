# src/ingest/ingestion.py

import os
import pandas as pd
from google.cloud import storage
from pathlib import Path

from src.utils import get_gcs_client

def load_local_data(filepath: str) -> pd.DataFrame:
    """Load fraud dataset from local CSV file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"CSV not found at: {filepath}")
    df = pd.read_csv(filepath)
    print(f"[INFO] Loaded {df.shape[0]} rows and {df.shape[1]} columns from {filepath}")
    return df

def upload_df_to_gcs(df: pd.DataFrame, bucket_name: str, destination_blob_name: str):
    """Upload a DataFrame to GCS as a CSV file."""
    client = get_gcs_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    csv_data = df.to_csv(index=False)
    blob.upload_from_string(csv_data, content_type="text/csv")

    print(f"[INFO] Uploaded CSV to gs://{bucket_name}/{destination_blob_name}")

def main():
    # Read env variables
    local_file_path = os.getenv("LOCAL_RAW_FILE", "data/fraud_oracle.csv")
    gcs_bucket_name = os.getenv("GCS_BUCKET_NAME", "fraud-detection-data")
    gcs_blob_path = os.getenv("GCS_BLOB_PATH", "raw/fraud_oracle.csv")

    # Step 1: Load local data
    df = load_local_data(local_file_path)

    # Step 2: Upload to GCS
    upload_df_to_gcs(df, gcs_bucket_name, gcs_blob_path)

if __name__ == "__main__":
    main()
