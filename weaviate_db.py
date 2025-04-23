
from weaviate import connect_to_weaviate_cloud, WeaviateClient
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from weaviate.classes.init import AdditionalConfig, Timeout
from langchain_weaviate.vectorstores import WeaviateVectorStore
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.cloud import secretmanager
from fastapi import Depends
from google.oauth2 import service_account


wcd_url = os.environ["WCD_URL"]
wcd_api_key = os.environ["WCD_API_KEY"]

try:
    # Load the service account key file
    with open(os.getenv('GOOGLE_APPLICATION_CREDENTIALS'), "r") as f:
        service_account_info = json.load(f)

    # Create credentials
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info
    )
except:
    pass


def get_credentials_from_secret_manager() -> Credentials:
    """Retrieves service account credentials from Google Cloud Secret Manager."""
    secret_name = os.environ.get("WCD_CRED_SECRET_NAME", "your-wcd-credentials-secret-name") # Get the secret name from an env variable
    client = secretmanager.SecretManagerServiceClient()
    project_id = os.environ.get("GOOGLE_PROJECT_ID")  # Ensure you have your GCP project ID as an env variable
    if not project_id:
        raise ValueError("GOOGLE_PROJECT_ID environment variable not set.")

    secret_version_name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"

    try:
        response = client.access_secret_version(request={"name": secret_version_name})
        secret_content = response.payload.data.decode("utf-8")
        # Assuming your secret content is a JSON key file
        credentials_info = json.loads(secret_content)
        credentials = Credentials.from_service_account_info(
            credentials_info,
            scopes=[
                "https://www.googleapis.com/auth/generative-language",
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        )
        request = Request()
        credentials.refresh(request)
        return credentials
    except Exception as e:
        print(f"Error accessing secret '{secret_name}': {e}")
        # Handle the error appropriately, perhaps by raising it
        raise


credentials = get_credentials_from_secret_manager()
token = credentials.token


def get_weaviate_retriever(embeddings):
    with connect_to_weaviate_cloud(
                cluster_url=wcd_url,
                auth_credentials=Auth.api_key(wcd_api_key),
                headers={'X-Goog-Vertex-Api-Key': token},
                additional_config=AdditionalConfig(
                    timeout=Timeout(init=300, query=120, insert=240)
                )
            ) as client:
        vectorstore = WeaviateVectorStore(client, "Rag", "content", embedding=embeddings)
        retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    return retriever
