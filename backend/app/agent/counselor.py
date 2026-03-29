"""
Main counselor agent — integrates Claude API with RAG retrieval.
"""

import anthropic

from app.config import settings
from app.agent.prompts import SYSTEM_PROMPT, build_context_prompt
from app.agent.session import Session, session_manager
from app.rag.retriever import Retriever


class CounselorAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.retriever = Retriever()

    async def chat(self, session_id: str, user_message: str) -> str:
        """Process a user message and return the counselor's response."""
        # Get or create session
        session = session_manager.get_session(session_id)
        if not session:
            session = session_manager.create_session()

        # Retrieve relevant context via RAG
        context_chunks = self.retriever.search(user_message, n_results=5)

        # Build the context-enhanced prompt
        context_prompt = build_context_prompt(context_chunks, user_message)

        # Add user message to session
        session.add_message("user", context_prompt)

        # Trim conversation if needed
        session.trim_to_token_budget()

        # Call Claude API
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            messages=session.get_messages_for_api(),
        )

        assistant_message = response.content[0].text

        # Save assistant response to session
        session.add_message("assistant", assistant_message)

        return assistant_message

    def search_courses(self, query: str) -> list[dict]:
        """Search courses via RAG."""
        return self.retriever.search_courses(query)

    def search_feedback(self, query: str) -> list[dict]:
        """Search student feedback via RAG."""
        return self.retriever.search_feedback(query)

    def search_careers(self, query: str) -> list[dict]:
        """Search career info via RAG."""
        return self.retriever.search_careers(query)
