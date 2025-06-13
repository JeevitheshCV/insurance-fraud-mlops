# src/utils.py

import os
from google.cloud import storage

def get_gcs_client():
    emulator_host = os.getenv("STORAGE_EMULATOR_HOST")
    if emulator_host:
        return storage.Client(client_options={"api_endpoint": emulator_host})
    return storage.Client()
