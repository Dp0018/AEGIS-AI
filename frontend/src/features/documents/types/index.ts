export type DocumentStatus = "pending" | "processing" | "completed" | "failed";

export interface DocumentResponse {
    id: string;
    filename: string;
    content_type: string;
    file_size: number;
    status: DocumentStatus;
    chunks_count: number | null;
    error_log: string | null;
    created_at: string;
    updated_at: string;
}
