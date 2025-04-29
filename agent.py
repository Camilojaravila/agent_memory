import os
from typing import Dict, List
# Recomendado: Usar ChatVertexAI para mejor soporte JSON, si no ChatGoogleGenerativeAI
from langchain_google_vertexai import ChatVertexAI, VertexAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableMap, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from postgres_db import get_by_session_id, checkpoint
from weaviate_db import get_weaviate_retriever
from prompts import prompt_niilo

# --- Configuración LLM ---
# Asegúrate de tener las variables de entorno o credenciales configuradas
PROJECT_ID = os.environ.get("GOOGLE_PROJECT_ID")
LOCATION = os.environ.get("GOOGLE_LOCATION", "us-central1") # O la región que uses

# LLM para conversación (Niilo) - Más creativo
llm_chat = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-001", # Revisa el modelo más adecuado
    temperature=0.7, # Permite respuestas más naturales
    max_output_tokens=1024,
    project=PROJECT_ID,
    # streaming=True # Habilita si necesitas streaming de tokens
)

# LLM para tareas estructuradas (Routing, Análisis Fórmulas, Extracción Params) - Preciso
llm_structured = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-001",
    temperature=0.0, # Determinista para JSON/Clasificación
    max_output_tokens=2048, # Ajusta si el JSON es grande
)

# --- Embeddings y Retriever ---
embeddings = VertexAIEmbeddings(
    model_name="text-embedding-004",
    project=PROJECT_ID,
    location=LOCATION
)
# Asume que esta función retorna un retriever compatible con Langchain
retriever = get_weaviate_retriever(embeddings)

# --- Cadena RAG para Niilo (Núcleo Conversacional) ---

def format_docs(docs: List[BaseMessage]) -> str:
    """Formatea los documentos recuperados en un string."""
    info = "\n\n".join(doc.page_content for doc in docs if hasattr(doc, 'page_content'))
    return info

# Construcción de la cadena RAG
rag_chain_niilo = (
    RunnablePassthrough.assign( # Mantiene la pregunta original
        context=(lambda x: format_docs(retriever.invoke(x["question"]))) # Invoca retriever y formatea
    )
    | prompt_niilo # Aplica el prompt de Niilo (espera 'question' y 'context')
    | llm_chat # Usa el LLM conversacional
    | StrOutputParser() # Obtiene la respuesta como string
)

# Añadir historial a la cadena RAG
# Espera un diccionario con la clave "question" conteniendo el mensaje del usuario (string)
chain_with_history = RunnableWithMessageHistory(
    rag_chain_niilo,
    get_by_session_id, # Función para obtener historial
    input_messages_key="question", # Clave donde va el mensaje del usuario (string)
    history_messages_key="chat_history", # Clave que el prompt espera para el historial
    # output_messages_key="answer" # Opcional: clave para la respuesta AI en el historial
)

# Función para obtener mensajes (útil para depuración o si se necesita fuera de RunnableWithMessageHistory)
def get_chat_messages(session_id: str) -> List[BaseMessage]:
    """Recupera los mensajes del historial para un session_id."""
    chat_history = get_by_session_id(session_id)
    return chat_history.messages if hasattr(chat_history, 'messages') else []
