from typing import List
from fastapi import APIRouter, Depends, status

from app.core.dependencies import get_rag_service, get_operator_user
from app.models.user import User
from app.services.rag import RAGService
from app.schemas.rag import RAGRetrieveRequest, RAGRetrieveResponse
from app.schemas.common import ErrorResponse

router = APIRouter()

@router.post(
    "/retrieve",
    response_model=List[RAGRetrieveResponse],
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def retrieve_rag_context(
    payload: RAGRetrieveRequest,
    current_user: User = Depends(get_operator_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Retrieve relevant document vector chunks based on cosine similarity context lookup."""
    results = await rag_service.retrieve_context(
        query=payload.query,
        top_k=payload.top_k,
        document_ids=payload.document_ids
    )
    return results

@router.post(
    "/query",
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse}
    }
)
async def query_rag_grounded_prompt(
    payload: RAGRetrieveRequest,
    current_user: User = Depends(get_operator_user),
    rag_service: RAGService = Depends(get_rag_service)
):
    """Execute similarity lookup and compile context into a grounded system prompt template."""
    results = await rag_service.retrieve_context(
        query=payload.query,
        top_k=payload.top_k,
        document_ids=payload.document_ids
    )
    prompt = rag_service.build_grounded_prompt(
        query=payload.query,
        context_chunks=results
    )
    return {
        "prompt": prompt,
        "context_chunks_count": len(results)
    }
