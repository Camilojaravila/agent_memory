from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4
from chatbot import get_response, get_history, get_session_ids, get_steps
import schema
import traceback

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

version = "0.1.1"

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
    return JSONResponse({"session_id": session_id})

@app.post("/chat/", tags=["Chatbot"], response_model=schema.ChatResponse)
async def chat(request: schema.ChatRequest):
    try:
        final_response = get_response(request.user_input, request.session_id)
        if not final_response:
            raise HTTPException(status_code=500, detail="No assistant response received.")
        return {"assistant_response": final_response[-1]['assistant_response'], "nodes": final_response}

    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{session_id}", tags=["Chatbot"])
async def get_chat_history(session_id: str):
    try:
        history = get_history(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/steps/{session_id}", tags=["Chatbot"])
async def get_graph_steps(session_id: str):
    try:
        history = get_steps(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/sessions/", tags=["Chatbot"], response_model=schema.SessionList)
async def get_sessions():
    try:
        sessions = get_session_ids()
        return {"session_ids": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))