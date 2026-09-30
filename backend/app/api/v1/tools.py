from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.core.dependencies import get_operator_user
from app.models.user import User
from app.schemas.tools import CustomerLookupRequest, TicketCreateRequest, EmailSendRequest
from app.schemas.common import ErrorResponse
from app.services.tools import (
    lookup_customer,
    create_support_ticket,
    send_smtp_email,
    email_log,
    ticket_registry
)

router = APIRouter()

@router.post(
    "/customer",
    responses={401: {"model": ErrorResponse}}
)
async def query_crm_customer(
    payload: CustomerLookupRequest,
    current_user: User = Depends(get_operator_user)
):
    """Lookup customer profile, status, and balance detail by email."""
    result = lookup_customer(payload.email)
    return result

@router.post(
    "/ticket",
    responses={401: {"model": ErrorResponse}}
)
async def create_crm_support_ticket(
    payload: TicketCreateRequest,
    current_user: User = Depends(get_operator_user)
):
    """Create a support ticket in the ticket database."""
    result = create_support_ticket(
        email=payload.email,
        issue=payload.issue,
        priority=payload.priority or "medium"
    )
    return result

@router.post(
    "/email",
    responses={401: {"model": ErrorResponse}}
)
async def dispatch_smtp_email(
    payload: EmailSendRequest,
    current_user: User = Depends(get_operator_user)
):
    """Dispatch outbound SMTP email transmission simulator."""
    result = send_smtp_email(
        to_email=payload.to_email,
        subject=payload.subject,
        body=payload.body
    )
    return result

@router.get(
    "/email/logs",
    responses={401: {"model": ErrorResponse}}
)
async def get_email_logs(
    current_user: User = Depends(get_operator_user)
):
    """Fetch history of dispatched outbound emails."""
    return email_log

@router.get(
    "/ticket/registry",
    responses={401: {"model": ErrorResponse}}
)
async def get_ticket_registry(
    current_user: User = Depends(get_operator_user)
):
    """Fetch history of escalated support tickets."""
    return list(ticket_registry.values())
