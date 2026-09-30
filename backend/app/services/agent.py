import uuid
import re
from typing import List, Optional, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import InMemorySaver

from app.core.config import settings
from app.services.rag import RAGService
from app.repositories.thread import ThreadRepository
from app.services.tools import create_support_ticket, send_smtp_email

class AgentState(TypedDict):
    """The State schema representing context data passing through the StateGraph."""
    query: str
    thread_id: uuid.UUID
    context_chunks: List[dict]
    response: Optional[str]
    escalated: bool
    requires_approval: bool
    approved: Optional[bool]
    feedback: Optional[str]
    next_node: Optional[str]

class AgentService:
    """Service layer coordinating Agent workflows using LangGraph StateGraph."""
    
    # Shared checkpointer across separate request lifetimes
    checkpointer = InMemorySaver()

    def __init__(self, rag_service: RAGService, thread_repo: ThreadRepository):
        self.rag_service = rag_service
        self.thread_repo = thread_repo
        self.graph = self._compile_graph()

    def _compile_graph(self) -> StateGraph:
        """Construct, define transitions for, and compile the LangGraph workflow."""
        builder = StateGraph(AgentState)

        # 1. Register nodes
        builder.add_node("coordinator", self._coordinator_node)
        builder.add_node("research", self._research_node)
        builder.add_node("respond", self._respond_node)
        builder.add_node("escalate", self._escalate_node)
        builder.add_node("email_dispatch", self._email_dispatch_node)

        # 2. Set entry point
        builder.set_entry_point("coordinator")

        # 3. Define transitions
        builder.add_conditional_edges(
            "coordinator",
            lambda state: state["next_node"],
            {
                "research": "research",
                "respond": "respond",
                "escalate": "escalate"
            }
        )

        builder.add_edge("research", "respond")

        # Dynamic loop-back checking for Response Node approval checks
        builder.add_conditional_edges(
            "respond",
            self._post_respond_route,
            {
                "respond": "respond",
                "email_dispatch": "email_dispatch",
                "end": END
            }
        )
        builder.add_edge("escalate", END)
        builder.add_edge("email_dispatch", END)

        # Compile with checkpointer and HITL interrupt on response draft review
        return builder.compile(checkpointer=self.checkpointer, interrupt_after=["respond"])

    def _post_respond_route(self, state: AgentState) -> str:
        """Direct transition based on human feedback."""
        if state.get("approved") is False:
            return "respond"
        elif state.get("approved") is True:
            return "email_dispatch"
        return "end"

    async def _coordinator_node(self, state: AgentState) -> dict:
        """Evaluate input to classify routes: research, direct reply, or escalation."""
        query = state["query"].lower()

        # Immediate Escalation keywords
        escalation_keywords = ["refund", "billing", "dispute", "cancel", "chargeback", "credit card"]
        if any(k in query for k in escalation_keywords):
            return {"next_node": "escalate", "escalated": True}

        # Route all non-escalation queries to RAG research by default
        return {"next_node": "research"}

    async def _research_node(self, state: AgentState) -> dict:
        """Call RAG retrieval to fetch supporting documentation context."""
        query = state["query"]
        thread_id = state["thread_id"]
        
        # Log telemetry action for research node start
        await self.thread_repo.create_action(
            thread_id,
            "knowledge_base_search",
            {
                "thought": f"Retrieving relevant documentation chunks from vector database for: '{query}'",
                "action": f"query_similarity(query_text='{query}')"
            }
        )
        
        chunks = await self.rag_service.retrieve_context(query, top_k=5)
        
        # Log telemetry action for research results observation
        observation_text = f"Retrieved {len(chunks)} relevant chunks."
        if chunks:
            observation_text += f" Top chunk score: {chunks[0]['score']:.2f} from file: '{chunks[0]['filename']}'."
        await self.thread_repo.create_action(
            thread_id,
            "knowledge_base_result",
            {
                "observation": observation_text
            }
        )
        
        return {"context_chunks": chunks}

    async def _respond_node(self, state: AgentState) -> dict:
        """Generate response draft. Re-evaluates draft if feedback was provided."""
        query = state["query"]
        thread_id = state["thread_id"]
        context_chunks = state.get("context_chunks", [])
        
        # Check if we are resuming from an operator redraft feedback
        if state.get("approved") is False:
            feedback = state.get("feedback", "")
            
            # Log redraft thought
            await self.thread_repo.create_action(
                thread_id,
                "response_redrafting",
                {
                    "thought": f"Redrafting response to incorporate human feedback: '{feedback}'",
                    "action": "generate_response(feedback=feedback)"
                }
            )
            
            new_draft = await self._generate_response(query, context_chunks, feedback=feedback)
            
            # Log decision
            await self.thread_repo.create_action(
                thread_id,
                "response_redraft_complete",
                {
                    "decision": "New response draft prepared. Waiting for human approval."
                }
            )
            
            return {
                "response": new_draft,
                "requires_approval": True,
                "approved": None,  # Reset for next review cycle
                "feedback": None
            }

        # Log draft thought
        await self.thread_repo.create_action(
            thread_id,
            "response_drafting",
            {
                "thought": "Formulating grounded draft response using retrieved context.",
                "action": "generate_response()"
            }
        )
        
        # Generate original draft response
        draft = await self._generate_response(query, context_chunks)
        
        # Log decision
        await self.thread_repo.create_action(
            thread_id,
            "response_draft_complete",
            {
                "decision": "Response draft prepared. Waiting for human approval."
            }
        )
        
        return {
            "response": draft,
            "requires_approval": True,
            "approved": None,
            "feedback": None
        }

    async def _escalate_node(self, state: AgentState) -> dict:
        """Handle support escalations, create tickets, and persist message/actions in PostgreSQL."""
        query = state["query"]
        thread_id = state["thread_id"]
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', query)
        email = emails[0] if emails else "escalated-customer@aegisai.com"

        ticket = create_support_ticket(email=email, issue=query, priority="high")
        msg_text = f"This request requires account/billing access. Escalated to support queue. Support ticket created: {ticket['ticket_id']} (Priority: {ticket['priority']})."

        # Database persistence
        await self.thread_repo.create_message(thread_id, "assistant", msg_text)
        await self.thread_repo.create_action(thread_id, "support_ticket_created", ticket)

        return {
            "escalated": True,
            "response": msg_text
        }

    async def _email_dispatch_node(self, state: AgentState) -> dict:
        """Simulate SMTP dispatch and persist message/actions in PostgreSQL."""
        query = state["query"]
        response = state["response"] or ""
        thread_id = state["thread_id"]
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', query)
        email = emails[0] if emails else "customer@aegisai.com"

        log_entry = send_smtp_email(to_email=email, subject="Response from AegisAI Support", body=response)
        
        # Database persistence
        await self.thread_repo.create_message(thread_id, "assistant", response)
        await self.thread_repo.create_action(thread_id, "smtp_email_sent", log_entry)

        return {
            "requires_approval": False
        }

    async def _generate_response(
        self,
        query: str,
        context_chunks: List[dict],
        feedback: Optional[str] = None
    ) -> str:
        """Call LLM or deterministic mock parser depending on environment configs."""
        if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY == "dummy_key_replace_in_env":
            if feedback:
                return f"[Mock Redraft] Grounded response to: '{query}' incorporating feedback: '{feedback}'"
            return f"[Mock Draft] Grounded response to: '{query}' based on {len(context_chunks)} source documents."
        else:
            from langchain_openai import ChatOpenAI
            from langchain_core.messages import SystemMessage, HumanMessage

            prompt = self.rag_service.build_grounded_prompt(query, context_chunks)
            messages = [SystemMessage(content=prompt)]

            if feedback:
                messages.append(HumanMessage(content=f"Please revise the draft response based on this operator feedback: {feedback}"))

            llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4o", temperature=0.2)
            res = await llm.ainvoke(messages)
            return str(res.content)
