from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
#from alloy_db import init_tables, close_connection
import chatbot
import schema
import traceback
from contextlib import asynccontextmanager
from weaviate_db import connect_to_db, close_db
import logging
import os
logger = logging.getLogger(__name__)


tags_metadata = [
    {
        "name": "Conversations",
        "description": "Agent services.",
    },
    {
        "name": "Messages",
        "description": "Message services.",
    },
]

env_name = os.environ.get("ENV")
version = f"2.2.7-{env_name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        connect_to_db()
        logger.info("Weaviate client connected successfully.")
        yield
    except Exception as e:
        logger.error(f"Error connecting to Weaviate: {e}")
        # Optionally, you might want to handle this error more gracefully,
        # perhaps by setting a flag and checking it in your API endpoints.
    finally:
        close_db()
        logger.info("Weaviate client closed.")


app = FastAPI(
    openapi_tags=tags_metadata,
    version=version,
    lifespan=lifespan
    )

# CORS middleware for allowing requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/conversations/{user_id}", tags=["Conversations"], response_model=schema.SessionList)
async def get_conversations(user_id: str):
    """
    Get all the session ids for conversations from the user.
    """
    try:
        sessions = chatbot.get_session_ids(user_id)
        return {"chats": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/conversations/{user_id}", tags=["Conversations"], response_model=schema.NewSession)
async def new_conversation(user_id: str):
    """Creates a new session and returns the session ID."""
    session_id = str(uuid4())
    user_session = chatbot.get_new_session_id(session_id=session_id, user_id=user_id)
    return JSONResponse({"session_id": str(user_session.session_id), "user_id": user_session.user_id})

@app.delete("/api/conversations/{session_id}", tags=["Conversations"])
async def delete_conversation(session_id: str):
    """Delete the conversation from the user."""
    conversation = chatbot.delete_conversation(session_id)
    return f"The conversation {conversation.session_id} has been deleted"

@app.post("/api/messages/chat/", tags=["Messages"], response_model=schema.ChatResponse)
async def chat(request: schema.ChatRequest):
    try:
        final_response = chatbot.get_response(request.user_input, request.session_id)
        if not final_response:
            raise HTTPException(status_code=500, detail="No assistant response received.")
        chatbot.update_timestamp(request.session_id)
        info = dict(**final_response[-1])
        info['nodes'] = final_response
        return info

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/messages/chat/{session_id}", tags=["Messages"], response_model=schema.List[schema.ConversationHistory])
async def get_chat_history(session_id: str):
    try:
        history = chatbot.get_history(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.put("/api/messages/update/", tags=["Messages"], response_model=schema.Message)
async def update_message(body: schema.MessageUpdate):
    try:
        info = body.__dict__
        return chatbot.update_message(info)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/steps/{session_id}", tags=["Chatbot"])
async def get_graph_steps(session_id: str):
    try:
        history = chatbot.get_steps(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

