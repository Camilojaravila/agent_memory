
from weaviate import connect_to_weaviate_cloud, WeaviateClient
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
from weaviate.classes.init import AdditionalConfig, Timeout
from langchain_weaviate.vectorstores import WeaviateVectorStore
import os

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials

from fastapi import Depends


wcd_url = os.environ["WCD_URL"]
wcd_api_key = os.environ["WCD_API_KEY"]


def get_credentials() -> Credentials:
        credentials = Credentials.from_service_account_file(
            "niilo-441811-032714d1b5e6.json",
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
