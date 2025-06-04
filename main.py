from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import chatbot
import schema
import traceback
from contextlib import asynccontextmanager
from weaviate_db import connect_to_db, close_db
import logging
import os

# --- (El resto de la configuración inicial se mantiene igual) ---
logger = logging.getLogger(__name__)

tags_metadata = [
    {
        "name": "Conversations",
        "description": "Endpoints para crear, obtener y eliminar conversaciones.",
    },
    {
        "name": "Messages",
        "description": "Endpoints para interactuar con los mensajes dentro de una conversación.",
    },
    {
        "name": "Chatbot",
        "description": "Endpoints de bajo nivel para depuración del agente."
    }
]

env_name = os.environ.get("ENV", "local")
version = f"2.2.8-{env_name}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        connect_to_db()
        logger.info("Cliente de Weaviate conectado exitosamente.")
        yield
    except Exception as e:
        logger.error(f"Error crítico al conectar con Weaviate: {e}")
    finally:
        close_db()
        logger.info("Cliente de Weaviate desconectado.")

app = FastAPI(
    title="Niilo Chat API",
    description="API para el agente conversacional multimodal de Niilo.",
    openapi_tags=tags_metadata,
    version=version,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoints de la API con Documentación Detallada ---

@app.get("/api/conversations/{user_id}", tags=["Conversations"], response_model=schema.SessionList)
async def get_conversations(user_id: str):
    """
    Recupera la lista de todas las conversaciones iniciadas por un usuario.

    Este endpoint consulta la base de datos y devuelve un resumen de cada
    chat asociado al `user_id` proporcionado.

    Args:
        user_id (str): El identificador único del usuario.

    Returns:
        schema.SessionList: Un objeto que contiene una lista de `chats`,
        donde cada chat incluye su `session_id`, `user_id`, fechas y
        el primer mensaje de la conversación.

    Raises:
        HTTPException 500: Si ocurre un error inesperado al consultar la base de datos.
    """
    try:
        sessions = chatbot.get_session_ids(user_id)
        return {"chats": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{user_id}", tags=["Conversations"], response_model=schema.NewSession)
async def new_conversation(user_id: str):
    """
    Crea una nueva sesión de chat para un usuario.

    Genera un `session_id` único y lo asocia con el `user_id`
    proporcionado, creando un nuevo registro de conversación vacío.

    Args:
        user_id (str): El identificador único del usuario para el cual se crea la sesión.

    Returns:
        schema.NewSession: Un objeto JSON con el `session_id` y el `user_id` de la nueva conversación.
    """
    session_id = str(uuid4())
    user_session = chatbot.get_new_session_id(session_id=session_id, user_id=user_id)
    return JSONResponse({"session_id": str(user_session.session_id), "user_id": user_session.user_id})

@app.delete("/api/conversations/{session_id}", tags=["Conversations"], status_code=200)
async def delete_conversation(session_id: str):
    """
    Elimina permanentemente una conversación y todos sus mensajes.

    Esta es una operación destructiva. Usa este endpoint para permitir
    a los usuarios borrar su historial.

    Args:
        session_id (str): El identificador único de la sesión a eliminar.

    Returns:
        str: Un mensaje de confirmación indicando que la conversación ha sido eliminada.
    """
    conversation = chatbot.delete_conversation(session_id)
    return f"La conversación {conversation.session_id} ha sido eliminada"

@app.post("/api/messages/chat/", tags=["Messages"], response_model=schema.ChatResponse)
async def chat(request: schema.ChatRequest):
    """
    Envía un mensaje a una conversación y recibe la respuesta del agente.

    Este es el endpoint principal para la interacción del chat. Procesa el
    `user_input`, lo envía al agente de IA para obtener una respuesta y
    actualiza el estado de la conversación.

    Args:
        request (schema.ChatRequest): Un cuerpo de solicitud JSON con:
            - `session_id` (str): El ID de la conversación actual.
            - `user_input` (str): El mensaje escrito por el usuario.

    Returns:
        schema.ChatResponse: Un objeto JSON con la respuesta del asistente,
        su ID, y una lista de `nodes` que detallan los pasos intermedios
        que el agente tomó para generar la respuesta (útil para depuración).

    Raises:
        HTTPException 500: Si el agente no logra generar una respuesta o si
        ocurre un error interno.
    """
    try:
        final_response = chatbot.get_response(request.user_input, request.session_id)
        if not final_response:
            raise HTTPException(status_code=500, detail="No se recibió respuesta del asistente.")
        chatbot.update_timestamp(request.session_id)
        info = dict(**final_response[-1])
        info['nodes'] = final_response
        return info

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/messages/chat/{session_id}", tags=["Messages"], response_model=list[schema.ConversationHistory])
async def get_chat_history(session_id: str):
    """
    Obtiene el historial completo de mensajes de una conversación específica.

    Devuelve una lista de todos los mensajes, tanto del usuario ('human')
    como del asistente ('ai'), en orden cronológico.

    Args:
        session_id (str): El identificador único de la sesión de la cual se
        quiere obtener el historial.

    Returns:
        list[schema.ConversationHistory]: Una lista de objetos, donde cada
        uno representa un mensaje con su contenido, tipo, autor y metadatos.

    Raises:
        HTTPException 500: Si ocurre un error al recuperar el historial.
    """
    try:
        history = chatbot.get_history(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/api/messages/update/", tags=["Messages"], response_model=schema.Message)
async def update_message(body: schema.MessageUpdate):
    """
    Actualiza un mensaje con el feedback del usuario.

    Permite registrar si un mensaje del asistente fue útil (`like`),
    junto con un feedback más detallado en forma de etiquetas y observaciones.

    Args:
        body (schema.MessageUpdate): Un cuerpo de solicitud JSON con:
            - `message_id` (str): El ID del mensaje a actualizar.
            - `like` (bool): True si fue útil, False si no lo fue.
            - `feedback` (List[str]): Lista de etiquetas de feedback.
            - `observations` (str, opcional): Comentarios adicionales.

    Returns:
        schema.Message: El objeto del mensaje actualizado, incluyendo la
        fecha de creación original.

    Raises:
        HTTPException 500: Si el mensaje no se encuentra o falla la actualización.
    """
    try:
        info = body.__dict__
        return chatbot.update_message(info)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/steps/{session_id}", tags=["Chatbot"])
async def get_graph_steps(session_id: str):
    """
    [DEBUG] Obtiene los pasos internos del grafo de ejecución del agente.

    Este es un endpoint de bajo nivel, principalmente para depuración.
    Permite a los desarrolladores ver el "razonamiento" paso a paso
    que siguió el agente para una conversación específica.

    Args:
        session_id (str): El identificador de la sesión a investigar.

    Returns:
        schema.Validation: Validación para el usuario.

    Raises:
        HTTPException 500: Si ocurre un error al recuperar los pasos.
    """
    try:
        history = chatbot.get_steps(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/messages/{user_id}", tags=["Chatbot"])
async def get_validation_message(user_id: str, interval: str, num_msg: int):
    """
    Obtiene el número de mensajes en un intervalo de tiempo.


    Args:
        user_id (str): El identificador de la sesión a investigar.
        interval (str): Intervalo de tiempo a evaluar.
        num_msg (int): Numero de mensajes máximo permitido.

    Returns:
        list: Una lista de objetos o diccionarios que representan cada paso
        en el grafo de ejecución del agente.

    Raises:
        HTTPException 500: Si ocurre un error al recuperar los pasos.
    """
    try:
        history = chatbot.get_validation(user_id, interval, num_msg)
        return history
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
