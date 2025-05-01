
from weaviate import connect_to_weaviate_cloud, WeaviateClient
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from weaviate.classes.init import AdditionalConfig, Timeout
from langchain_weaviate.vectorstores import WeaviateVectorStore
import os
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

import configs


wcd_url = os.environ["WCD_URL"]
wcd_api_key = os.environ["WCD_API_KEY"]

# Weaviate client instance
weaviate_client: WeaviateClient = None


def get_credentials() -> Credentials:
    """Retrieves service account credentials from Google Cloud Secret Manager."""
    secret_name = os.environ.get("WCD_CRED_SECRET_NAME")
    credentials_info = configs.get_secret(secret_name)
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



credentials = get_credentials()
token = credentials.token

def connect_to_db():
    global weaviate_client

    weaviate_client = connect_to_weaviate_cloud(
            cluster_url=wcd_url,
            auth_credentials=Auth.api_key(wcd_api_key),
            headers={'X-Goog-Vertex-Api-Key': token},
            additional_config=AdditionalConfig(
                timeout=Timeout(init=300, query=120, insert=240)
            )
        )

def get_weaviate_retriever(embeddings):
    global weaviate_client
    vectorstore = WeaviateVectorStore(weaviate_client, "Rag", "content", embedding=embeddings)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    return retriever


def close_db():
    global weaviate_client
    if weaviate_client:
            weaviate_client.close()

connect_to_db()