"""
Conversation session management.
"""

import uuid
from datetime import datetime


class Session:
    def __init__(self, session_id: str | None = None):
        self.id = session_id or str(uuid.uuid4())
        self.messages: list[dict] = []
        self.created_at = datetime.utcnow()

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
        })

    def get_messages_for_api(self) -> list[dict]:
        """Return messages in the format expected by the Claude API."""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]

    def trim_to_token_budget(self, max_messages: int = 20):
        """Keep only the most recent messages to stay within token limits."""
        if len(self.messages) > max_messages:
            self.messages = self.messages[-max_messages:]


class SessionManager:
    """In-memory session store. Can be replaced with Redis later."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self) -> Session:
        session = Session()
        self._sessions[session.id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str):
        self._sessions.pop(session_id, None)


# Global session manager
session_manager = SessionManager()
