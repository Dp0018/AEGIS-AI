export interface RAGRetrieveRequest {
    query: string;
    top_k: number;
    document_ids?: string[] | null;
}

export interface RAGChunkResult {
    text: string;
    filename: string;
    score: number;
    document_id: string;
}
