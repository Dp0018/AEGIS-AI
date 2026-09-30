import { apiClient } from "@/lib/api-client";
import { RAGRetrieveRequest, RAGChunkResult } from "../types";

export async function ragRetrieveRequest(payload: RAGRetrieveRequest): Promise<RAGChunkResult[]> {
    const response = await apiClient.post<RAGChunkResult[]>("/rag/retrieve", payload);
    return response.data;
}
