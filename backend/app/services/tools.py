import uuid
from typing import Dict, List, Optional
from app.services.rag import RAGService

# Shared in-memory databases representing external system registers
customer_db: Dict[str, dict] = {
    "customer@aegisai.com": {
        "name": "Jane Doe",
        "subscription_tier": "enterprise",
        "billing_status": "active",
        "balance": 0.00,
        "active_tickets_count": 0
    },
    "billing-issue@aegisai.com": {
        "name": "John Smith",
        "subscription_tier": "pro",
        "billing_status": "past_due",
        "balance": 49.99,
        "active_tickets_count": 1
    }
}

ticket_registry: Dict[str, dict] = {}
email_log: List[dict] = []

def lookup_customer(email: str) -> dict:
    """Query customer CRM database to resolve billing status and tier details."""
    clean_email = email.strip().lower()
    if clean_email in customer_db:
        return {
            "found": True,
            "email": clean_email,
            **customer_db[clean_email]
        }
    
    # Return a default mock profile for testing if not found in db
    return {
        "found": False,
        "email": clean_email,
        "name": "Unknown Customer",
        "subscription_tier": "free",
        "billing_status": "none",
        "balance": 0.00,
        "active_tickets_count": 0
    }

def create_support_ticket(email: str, issue: str, priority: str = "medium") -> dict:
    """Create a support escalation ticket in the ticketing service."""
    ticket_id = f"TIC-{uuid.uuid4().hex[:8].upper()}"
    ticket = {
        "ticket_id": ticket_id,
        "email": email.strip().lower(),
        "issue": issue,
        "priority": priority.lower(),
        "status": "open"
    }
    ticket_registry[ticket_id] = ticket
    
    # Increment active ticket count in CRM database if customer exists
    clean_email = email.strip().lower()
    if clean_email in customer_db:
        customer_db[clean_email]["active_tickets_count"] += 1
        
    return ticket

def send_smtp_email(to_email: str, subject: str, body: str) -> dict:
    """Simulate dispatching a secure outbound SMTP email message."""
    message_id = f"MSG-{uuid.uuid4().hex[:12].upper()}"
    log_entry = {
        "message_id": message_id,
        "to": to_email.strip().lower(),
        "subject": subject,
        "body": body,
        "status": "delivered"
    }
    email_log.append(log_entry)
    return log_entry

async def search_knowledge_base(query: str, rag_service: RAGService) -> List[dict]:
    """Retrieve matched chunks from knowledge base vector store collections."""
    return await rag_service.retrieve_context(query=query, top_k=3)
