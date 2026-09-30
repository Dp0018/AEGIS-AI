import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import (
    get_agent_service,
    get_thread_repository,
    get_memory_service,
    get_operator_user
)
from app.models.user import User
from app.repositories.thread import ThreadRepository
from app.services.agent import AgentService
from app.services.memory import MemoryService
from app.schemas.agent import (
    AgentRunRequest,
    AgentApproveRequest,
    AgentRunResponse,
    MessageResponse,
    MemoryResponse,
    ThreadResponse,
    ActionResponse
)
from app.schemas.common import ErrorResponse

router = APIRouter()

@router.post(
    "/run",
    response_model=AgentRunResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def execute_agent_workflow(
    payload: AgentRunRequest,
    current_user: User = Depends(get_operator_user),
    agent_service: AgentService = Depends(get_agent_service),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
):
    """Start or run the LangGraph workflow on a customer query session, persisting messages."""
    # 1. Resolve or create SQL thread
    await thread_repo.get_or_create_thread(payload.thread_id)
    
    # 2. Persist client query message
    await thread_repo.create_message(payload.thread_id, "user", payload.query)

    config = {"configurable": {"thread_id": str(payload.thread_id)}}
    
    initial_state = {
        "query": payload.query,
        "thread_id": payload.thread_id,
        "context_chunks": [],
        "response": None,
        "escalated": False,
        "requires_approval": False,
        "approved": None,
        "feedback": None
    }
    
    # 3. Run the graph (pauses on respond node)
    await agent_service.graph.ainvoke(initial_state, config)
    
    state = agent_service.graph.get_state(config)
    if not state or not state.values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to run agent or resolve state checkpoint."
        )
        
    values = state.values
    return AgentRunResponse(
        thread_id=payload.thread_id,
        response=values.get("response"),
        requires_approval=values.get("requires_approval", False),
        escalated=values.get("escalated", False)
    )

@router.post(
    "/approve",
    response_model=AgentRunResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def resume_agent_approval(
    payload: AgentApproveRequest,
    current_user: User = Depends(get_operator_user),
    agent_service: AgentService = Depends(get_agent_service),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
):
    """Submit human-in-the-loop approval or revision comments to resume execution, logging feedback."""
    config = {"configurable": {"thread_id": str(payload.thread_id)}}
    
    current_state = agent_service.graph.get_state(config)
    if not current_state or not current_state.values:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation thread state not found."
        )

    # If operator rejected the draft, persist their feedback as an audit message log
    if not payload.approved and payload.feedback:
        await thread_repo.create_message(payload.thread_id, "human_feedback", payload.feedback)
        
    # Update state with approval decision and comments
    agent_service.graph.update_state(
        config,
        {
            "approved": payload.approved,
            "feedback": payload.feedback,
            "requires_approval": not payload.approved
        }
    )
    
    # Resume execution by invoking with None
    await agent_service.graph.ainvoke(None, config)
    
    # Get updated state
    updated_state = agent_service.graph.get_state(config)
    if not updated_state or not updated_state.values:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to resume agent workflow or resolve state checkpoint."
        )
        
    values = updated_state.values
    return AgentRunResponse(
        thread_id=payload.thread_id,
        response=values.get("response"),
        requires_approval=values.get("requires_approval", False),
        escalated=values.get("escalated", False)
    )

@router.get(
    "/thread/{thread_id}/history",
    response_model=List[MessageResponse],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
async def get_thread_history(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_operator_user),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
):
    """Retrieve full history of conversation messages inside a thread."""
    messages = await thread_repo.get_thread_messages(thread_id)
    return messages

@router.get(
    "/thread/{thread_id}/actions",
    response_model=List[ActionResponse],
    responses={
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
async def get_thread_actions_log(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_operator_user),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
):
    """Retrieve all action logs/thoughts generated by the agent inside a thread."""
    actions = await thread_repo.get_thread_actions(thread_id)
    return actions

@router.post(
    "/thread/{thread_id}/summarize",
    response_model=MemoryResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        404: {"model": ErrorResponse}
    }
)
async def trigger_thread_summarization(
    thread_id: uuid.UUID,
    current_user: User = Depends(get_operator_user),
    memory_service: MemoryService = Depends(get_memory_service)
):
    """Trigger distillation of the thread's messages to update the customer's profile memory."""
    memory = await memory_service.summarize_thread(thread_id)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to compile summary. Thread may be empty."
        )
    return memory

@router.get(
    "/threads",
    response_model=List[ThreadResponse],
    responses={401: {"model": ErrorResponse}}
)
async def list_all_operator_threads(
    current_user: User = Depends(get_operator_user),
    thread_repo: ThreadRepository = Depends(get_thread_repository)
):
    """Retrieve metadata for all conversation threads."""
    return await thread_repo.list_all_threads()

from fastapi import WebSocket, WebSocketDisconnect
from app.core.websocket import manager

@router.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    """WebSocket endpoint for streaming real-time agent telemetry logs."""
    await manager.connect(thread_id, websocket)
    try:
        while True:
            # Keep connection alive; discard any client-sent text
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(thread_id, websocket)
