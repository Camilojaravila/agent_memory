import weaviate
from weaviate.classes.init import Auth
import os
from dotenv import load_dotenv
from google.cloud import aiplatform
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings

load_dotenv()


# Define the Gemini model
model = ChatVertexAI(
    model="gemini-2.0-flash",
    temperature=0.1
)

embedding = VertexAIEmbeddings(model_name='text-embedding-004')

def get_credentials() -> service_account.Credentials:
        credentials = service_account.Credentials.from_service_account_file(
            "niilo-441811-032714d1b5e6.json",
            scopes=[
                "https://www.googleapis.com/auth/generative-language",
                "https://www.googleapis.com/auth/cloud-platform",
            ],
        )
        request = Request()
        credentials.refresh(request)
        return credentials

token = get_credentials().token
# Configuración de Weaviate
client: weaviate.WeaviateClient = weaviate.connect_to_weaviate_cloud(
    cluster_url=os.getenv("WEAVIATE_URL"),                                    # Replace with your Weaviate Cloud URL
    auth_credentials=Auth.api_key(os.getenv("WEAVIATE_API_KEY")),             # Replace with your Weaviate Cloud key
    headers={'X-Goog-Vertex-Api-Key': token}  # Replace with your OpenAI API key

)


def initialize_weaviate():
    """Inicializa la colección en Weaviate si no existe."""
    class_obj = {
        "class": "LangGraphState",
        "properties": [
            {
                "name": "state",
                "dataType": ["text"]
            }
        ]
    }

    if not client.schema.exists("LangGraphState"):
        client.schema.create_class(class_obj)

def save_state(state):
    """Guarda el estado en Weaviate."""
    response = model.predict(instances=[str(state)])
    vector = response.predictions[0]  # Obtiene el vector del estado
    client.data_object.create(
        data_object={"state": str(state)},
        class_name="LangGraphState",
        vector=vector
    )

def load_state(query):
    """Carga el estado más similar desde Weaviate."""
    response = model.predict(instances=[query])
    vector = response.predictions[0]
    results = client.query.get(
        "LangGraphState",
        ["state"]
    ).with_near_vector({
        "vector": vector
    }).with_limit(1).do()

    if results["data"]["Get"]["LangGraphState"]:
        return results["data"]["Get"]["LangGraphState"][0]["state"]
    return None

client.close()

if __name__ == "__main__":
    # Ejemplo de uso
    initialize_weaviate()
    save_state({"message": "Hola, ¿cómo estás?"})
    loaded_state = load_state("¿Qué tal?")
    print(f"Estado cargado: {loaded_state}")