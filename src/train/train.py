import os
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix, recall_score
from sklearn.model_selection import train_test_split
from imblearn.ensemble import BalancedRandomForestClassifier
import pandas as pd

from prefect import flow, task
from prefect.artifacts import create_markdown_artifact

from utils import get_best_params, convert_values_to_int_if_possible, format_confusion_matrix

from dotenv import load_dotenv
from sqlalchemy import create_engine

import mlflow

load_dotenv()

@task
def read_data() -> pd.DataFrame:
    """Reads the data from the database"""

    db_params = {
    'host': os.getenv('db_host'),
    'port': os.getenv('db_port'), 
    'database': os.getenv('db_name'),
    'user': os.getenv('db_username'),
    'password': os.getenv('db_password')
}
    engine = create_engine(f'postgresql+psycopg2://{db_params["user"]}:{db_params["password"]}@{db_params["host"]}:{db_params["port"]}/{db_params["database"]}')
    query = "SELECT * FROM model_data_w_dummy"
    ready_df = pd.read_sql_query(query, engine)
    engine.dispose()

    return ready_df

@task
def split_data(data: pd.DataFrame, test_size: float = 0.2) -> tuple:
    """Split dataset into training and testing sets"""

    dummies_X = data.drop(columns=['FraudFound_P'])
    y = data['FraudFound_P']
    X_train, X_test, y_train, y_test = train_test_split(dummies_X, y, test_size=test_size, random_state=42)

    return X_train, X_test, y_train, y_test

@task
def best_params_from_mlflow() -> dict:
    """Get the best parameters from MLflow"""

    best_params = get_best_params()
    best_params = convert_values_to_int_if_possible(best_params)
    return best_params

@task
def train_model(X_train: pd.DataFrame, y_train: pd.Series, X_test, y_test) -> None:
    """Train the model and log the metrics and model to MLflow"""

    with mlflow.start_run() as run:

        best_params = best_params_from_mlflow()
        mlflow.log_params(best_params)
        model = BalancedRandomForestClassifier(**best_params)
        model.fit(X_train, y_train)
        model_name = 'balanced_rf_model'
        mlflow.sklearn.log_model(model, model_name)

        y_pred = model.predict(X_test)

        mlflow.log_metric('recall', recall_score(y_test, y_pred))
        cr = classification_report(y_test, y_pred, output_dict=True, target_names=['Not Fraud', 'Fraud'])
        mlflow.log_dict(cr, './classification_report.json')
        md_classification_report = """
| Class | Precision | Recall | F1-Score | Support |
|-------|-----------|--------|----------|---------|
"""
        for cls in ['Not Fraud', 'Fraud']:
            md_classification_report += f"| {cls} | "
            md_classification_report += f"{cr[cls]['precision']:.4f} | "
            md_classification_report += f"{cr[cls]['recall']:.4f} | "
            md_classification_report += f"{cr[cls]['f1-score']:.4f} | "
            md_classification_report += f"{cr[cls]['support']:.1f} |\n"
        cm = confusion_matrix(y_test, y_pred)
        mlflow.log_figure(ConfusionMatrixDisplay(cm).plot().figure_, './confusion_matrix.png')
        md_confussion_matrix = f"""
{format_confusion_matrix(cm)}
"""
        create_markdown_artifact(
            key="modelreport",
            markdown=md_classification_report+md_confussion_matrix
        )

        mlflow_model_info = f"""
## MLflow Run Information

```
- Model Name: {model_name}
- Artifact URI: {run.info.artifact_uri}
- Run ID: {run.info.run_id}
- Experiment ID: {run.info.experiment_id}
- GCS location: {run.info.artifact_uri}/{model_name}/model.pkl
```
"""
        create_markdown_artifact(
            key="mlflowinfo",
            markdown=mlflow_model_info
        )

        deploy_model_instructions = f"""
## Deploy Model Instructions

- MLflow settings
```python
import os
import mlflow

tracking_uri = os.getenv('FRAUD_MODELLING_MLFLOW_TRACKING_URI')
mlflow.set_tracking_uri(tracking_uri)
mlflow.set_experiment('Insurance Fraud Detection')
```
- Load the model
```python
logged_model = 'runs:/{run.info.run_id}/{model_name}'
model = mlflow.pyfunc.load_model(logged_model)
```
"""

        create_markdown_artifact(
            key="deployinstructions",
            markdown=deploy_model_instructions
        )

    return None

@flow(log_prints=True)
def insurance_fraud_model() -> None:
    """Orchestration flow to train the insurance fraud model and log the metrics and model to MLflow"""

    # MLflow settings
    tracking_uri = os.getenv('FRAUD_MODELLING_MLFLOW_TRACKING_URI')
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment('Insurance Fraud Detection')

    # Load
    data = read_data()
    # Split
    X_train, X_test, y_train, y_test = split_data(data)   
    # Train
    train_model(X_train, y_train, X_test, y_test)

if __name__ == "__main__":
    insurance_fraud_model.serve(
        name='Train Insurance Fraud Model',
        tags=['balanced_random_forest', 'train', 'mlflow']
    )
