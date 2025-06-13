import os
import mlflow
from typing import Optional


def get_best_params(run_id: Optional[str] = None) -> dict:
    """Get best parameters from the MLflow run"""
    run_id = run_id or os.getenv('FRAUD_MODELLING_MLFLOW_RUN_ID')
    tracking_uri = os.getenv('FRAUD_MODELLING_MLFLOW_TRACKING_URI')

    if not run_id or not tracking_uri:
        raise ValueError("MLflow run ID or tracking URI not set in environment variables.")

    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment('Insurance Fraud Detection')
    client = mlflow.tracking.MlflowClient()
    run = client.get_run(run_id)
    params = dict(run.data.params)

    # Remove description if present
    params.pop('model_description', None)

    return params


def convert_values_to_int_if_possible(dictionary: dict) -> dict:
    """Convert values in a dictionary to integers if possible"""
    converted_dict = {}
    for key, value in dictionary.items():
        try:
            converted_dict[key] = int(value)
        except (ValueError, TypeError):
            converted_dict[key] = value
    return converted_dict


def format_confusion_matrix(cm: list[list[int]]) -> str:
    """Format confusion matrix as a markdown table"""
    labels = ['Actual Not Fraud', 'Actual Fraud']
    columns = ['Predicted Not Fraud', 'Predicted Fraud']

    md_table = "|  | " + " | ".join(columns) + " |\n"
    md_table += "|--------------------|-" + "-|".join(['---'] * len(columns)) + "|\n"

    for i, label in enumerate(labels):
        md_table += f"| **{label}** | " + " | ".join([f"{cm[i][j]}" for j in range(len(columns))]) + " |\n"

    return md_table
