import os
#from langchain_google_alloydb_pg import GoogleAlloyDBVectorStore
from langchain_google_alloydb_pg import AlloyDBEngine
from langchain.embeddings import OpenAIEmbeddings
from postgres_db import get_db

# Load environment variables
ALLOYDB_INSTANCE = os.getenv("ALLOYDB_INSTANCE")  # e.g., "projects/{PROJECT_ID}/locations/{REGION}/clusters/{CLUSTER_ID}/instances/{INSTANCE_ID}"
ALLOYDB_DATABASE = os.getenv("ALLOYDB_DATABASE", "documents_db")
ALLOYDB_TABLE = os.getenv("ALLOYDB_TABLE", "document_vectors")

# Initialize OpenAI embeddings
embeddings = OpenAIEmbeddings()

# Function to initialize vector store
def get_vector_store():
    db_conn = next(get_db())  # Get a database connection
    return GoogleAlloyDBVectorStore(
        alloydb_instance=ALLOYDB_INSTANCE,
        database=ALLOYDB_DATABASE,
        table=ALLOYDB_TABLE,
        embedding=embeddings,
        connection=db_conn,  # Use the existing PostgreSQL connection
    )

# Function to add documents
def add_documents(docs):
    """Adds a list of documents to the AlloyDB vector store."""
    vector_store = get_vector_store()
    vector_store.add_texts(docs)

# Function to search documents
def search_documents(query, top_k=5):
    """Searches for documents in AlloyDB based on the query."""
    vector_store = get_vector_store()
    results = vector_store.similarity_search(query, k=top_k)
    return results