import os
from langchain_google_alloydb_pg import AlloyDBEngine
from langchain_google_vertexai import VertexAIEmbeddings
from postgres_db import get_db
from langchain_google_alloydb_pg import AlloyDBVectorStore
import uuid


embedding = VertexAIEmbeddings(
    model_name="textembedding-gecko@latest", project=os.getenv("PROJECT_ID")
)

engine = AlloyDBEngine.from_instance(
    project_id=PROJECT_ID,
    region=REGION,
    cluster=CLUSTER,
    instance=INSTANCE,
    database=DATABASE,
)

engine.init_vectorstore_table(
    table_name=TABLE_NAME,
    vector_size=768,  # Vector size for VertexAI model(textembedding-gecko@latest)
)

# Function to initialize vector store
def get_vector_store():
    db_conn = next(get_db())  # Get a database connection
    

    store = AlloyDBVectorStore.create(
        engine=engine,
        table_name=TABLE_NAME,
        embedding_service=embedding,
    )
    return store

# Function to add documents
def add_documents(all_texts):
    """Adds a list of documents to the AlloyDB vector store."""
    metadatas = [{"len": len(t)} for t in all_texts]
    ids = [str(uuid.uuid4()) for _ in all_texts]
    store = get_vector_store()

    store.add_texts(all_texts, metadatas=metadatas, ids=ids)

def delete_document(id):
    store = get_vector_store()
    store.delete([id])


# Function to search documents
def search_documents(query, top_k=5):
    """Searches for documents in AlloyDB based on the query."""
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=top_k)
    return results