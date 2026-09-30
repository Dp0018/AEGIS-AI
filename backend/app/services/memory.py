import re
import uuid
from typing import Optional

from app.core.config import settings
from app.repositories.thread import ThreadRepository
from app.repositories.memory import MemoryRepository
from app.models.memory import Memory

class MemoryService:
    """Service layer managing conversation transcript compilations and memory distillation."""

    def __init__(self, thread_repo: ThreadRepository, memory_repo: MemoryRepository):
        self.thread_repo = thread_repo
        self.memory_repo = memory_repo

    async def summarize_thread(self, thread_id: uuid.UUID) -> Optional[Memory]:
        """Load messages, compile chat transcript, and upsert condensed summary to customer profile memory."""
        messages = await self.thread_repo.get_thread_messages(thread_id)
        if not messages:
            return None

        transcript = ""
        email = "customer@aegisai.com"
        
        for msg in messages:
            transcript += f"{msg.role.upper()}: {msg.content}\n"
            # Attempt to extract customer email from user inputs
            if msg.role == "user" and "@" in msg.content:
                emails = re.findall(r'[\w\.-]+@[\w\.-]+', msg.content)
                if emails:
                    email = emails[0]

        summary = await self._generate_summary(transcript)
        return await self.memory_repo.upsert_memory(email, summary)

    async def _generate_summary(self, transcript: str) -> str:
        """Invoke ChatOpenAI or return deterministic mock summary text depending on API key settings."""
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "dummy_key_replace_in_env":
            # Deterministic mock summary for testing
            return f"[Mock Summary] Customer discussed SMTP/vector topics. Transcript snippet: {transcript[:100].strip()}..."
        else:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            system_prompt = (
                "You are a customer service CRM analyst representing AegisAI.\n"
                "Review the following support chat transcript. Summarize the user's core requests, "
                "billing status details, subscription issues, or tech questions in a single concise paragraph. "
                "Maintain a factual, objective tone."
            )
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=f"Chat Transcript:\n{transcript}\n\nCRM Profile Summary:")
            ]

            llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o", temperature=0.3)
            res = await llm.ainvoke(messages)
            return str(res.content)
