import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Literal, Optional

app = FastAPI(title="Agent Crafter API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AgentRequest(BaseModel):
    role: Literal["general", "student", "finance", "lawyer"] = Field(
        "general", description="Which agent persona to use"
    )
    message: str = Field(..., min_length=1, description="User input message")
    context: Optional[str] = Field(
        None, description="Optional additional context from the conversation"
    )


class AgentResponse(BaseModel):
    role: str
    reply: str
    tips: list[str] = []


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }

    try:
        # Try to import database module
        from database import db

        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"

            # Try to list collections to verify connectivity
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]  # Show first 10 collections
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    # Check environment variables
    import os as _os

    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


def _respond_general(message: str) -> AgentResponse:
    reply = (
        "I'm your Agent Crafter assistant. Tell me what you want to achieve and I'll help break it down into clear steps. "
        f"You said: '{message}'. Here's how we can proceed:"
    )
    tips = [
        "Be specific about your goal and constraints",
        "Share any examples or formats you prefer",
        "We can iterate until it feels right",
    ]
    return AgentResponse(role="general", reply=reply, tips=tips)


def _respond_student(message: str) -> AgentResponse:
    reply = (
        "Let's approach this like a helpful study partner. We'll clarify the concept, give an example, and outline steps.\n\n"
        f"Question/Topic: {message}\n\n"
        "1) Concept overview: In simple terms, this is about understanding the core idea and how it connects to related topics.\n"
        "2) Quick example: We'll use a small, concrete example to make it stick.\n"
        "3) Study steps: Read -> Summarize -> Practice -> Review.\n"
    )
    tips = [
        "Ask for a practice question if you'd like",
        "Say 'explain like I'm 12' for simpler wording",
        "We can create flashcards from any topic",
    ]
    return AgentResponse(role="student", reply=reply, tips=tips)


def _respond_finance(message: str) -> AgentResponse:
    reply = (
        "I am not a financial advisor, but I can offer general, educational guidance.\n\n"
        f"Topic: {message}\n\n"
        "Framework:\n"
        "- Goal: Define time horizon and risk tolerance\n"
        "- Snapshot: Income, expenses, debts, and savings\n"
        "- Plan: Diversify, keep costs low, automate contributions\n"
        "- Risk note: Markets fluctuate; consider professional advice for decisions\n"
    )
    tips = [
        "We can outline a sample budget or emergency fund plan",
        "Ask for pros and cons of an option",
        "Request a checklist you can follow",
    ]
    return AgentResponse(role="finance", reply=reply, tips=tips)


def _respond_lawyer(message: str) -> AgentResponse:
    reply = (
        "I am not a lawyer, but I can provide general, educational information.\n\n"
        f"Issue: {message}\n\n"
        "Consider:\n"
        "- Jurisdiction matters: laws vary by location\n"
        "- Definitions: clarify terms and parties involved\n"
        "- Process: typical steps, timelines, and documents\n"
        "- Disclaimer: For actionable advice, consult a licensed attorney\n"
    )
    tips = [
        "Share your location to get more tailored general info",
        "Ask for a plain-language summary of key terms",
        "We can draft a generic template for learning purposes",
    ]
    return AgentResponse(role="lawyer", reply=reply, tips=tips)


@app.post("/api/agent/respond", response_model=AgentResponse)
def agent_respond(req: AgentRequest):
    message = req.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    if req.role == "student":
        return _respond_student(message)
    if req.role == "finance":
        return _respond_finance(message)
    if req.role == "lawyer":
        return _respond_lawyer(message)
    return _respond_general(message)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
