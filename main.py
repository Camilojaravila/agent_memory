from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
import agent
import schema
#import chatbot

tags_metadata = [
    {
        "name": "Agent",
        "description": "Agent services.",
    },
    {
        "name": "Chatbot",
        "description": "Chatbot services.",
    },
]

version = "0.0.1"

app = FastAPI(
    openapi_tags=tags_metadata,
    version=version)

# CORS middleware for allowing requests from your frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/new_session", tags=["Agent"])
async def new_session():
    """Creates a new session and returns the session ID."""
    session_id = str(uuid4())
    agent.get_by_session_id(session_id)
    return JSONResponse({"session_id": session_id})

@app.post("/chat/{session_id}", tags=["Agent"])
async def chat(session_id: str, chat_request: schema.ChatRequest):
    """Handles chat requests."""
    try:
        message = chat_request.message
        response = agent.call_model(message, session_id)
        return JSONResponse({"response": response})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history",  tags=["Agent"])
async def get_chats():
    """Retrieves all the ID stored."""
    sessions = agent.get_session_ids()
    print(sessions)
    return JSONResponse({"ids": [str(s) for s in  sessions]})

@app.get("/history/{session_id}",  tags=["Agent"])
async def get_messages(session_id: str):
    """Retrieves the chat history for a session."""
    #if session_id not in agent.store:
    #    raise HTTPException(status_code=404, detail="Session not found")

    memory = agent.get_by_session_id(session_id)

    return JSONResponse({"history": [message.to_json() for message in memory.get_messages()]})

'''

@app.post("/chatbot/{session_id}", tags=["Chatbot"])
async def interact_with_chatbot(chat_request: schema.ChatRequest, session_id: str):
    """Processes a chatbot message."""
    try:
        response = chatbot.stream_graph_updates(chat_request.message, session_id)
        return JSONResponse({"messages": response})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chatbot/{session_id}/history", tags=["Chatbot"])
async def get_history(session_id: str):
    """Retrieves chatbot session history."""
    try:
        history = chatbot.get_history(session_id)
        serializable_history = [message.dict() for message in history.values["messages"]]
        return JSONResponse({"messages": serializable_history})
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found")
'''