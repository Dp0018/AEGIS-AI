import { apiClient } from "@/lib/api-client";
import { DocumentResponse } from "../types";

export async function uploadDocumentRequest(
    file: File,
    onProgress?: (percent: number) => void
): Promise<DocumentResponse> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await apiClient.post<DocumentResponse>("/documents/upload", formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
            if (onProgress && progressEvent.total) {
                const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
                onProgress(percent);
            }
        }
    });
    return response.data;
}

export async function listDocumentsRequest(): Promise<DocumentResponse[]> {
    const response = await apiClient.get<DocumentResponse[]>("/documents/");
    return response.data;
}

export async function deleteDocumentRequest(id: string): Promise<{ detail: string }> {
    const response = await apiClient.delete<{ detail: string }>(`/documents/${id}`);
    return response.data;
}
