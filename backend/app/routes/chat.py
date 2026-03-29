"""
Chat/conversation API endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.counselor import CounselorAgent
from app.agent.session import session_manager

router = APIRouter()
agent = CounselorAgent()


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    response: str


class SessionResponse(BaseModel):
    session_id: str


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Send a message to the counselor and get a response."""
    session_id = request.session_id
    if not session_id:
        session = session_manager.create_session()
        session_id = session.id

    response = await agent.chat(session_id, request.message)
    return ChatResponse(session_id=session_id, response=response)


@router.post("/session", response_model=SessionResponse)
async def create_session():
    """Create a new conversation session."""
    session = session_manager.create_session()
    return SessionResponse(session_id=session.id)
