import { apiClient } from "@/lib/api-client";
import { 
    ThreadResponse, 
    MessageResponse, 
    ActionResponse, 
    AgentRunRequest, 
    AgentApproveRequest, 
    AgentRunResponse 
} from "../types";

export async function listThreadsRequest(): Promise<ThreadResponse[]> {
    const response = await apiClient.get<ThreadResponse[]>("/agent/threads");
    return response.data;
}

export async function getThreadHistoryRequest(threadId: string): Promise<MessageResponse[]> {
    const response = await apiClient.get<MessageResponse[]>(`/agent/thread/${threadId}/history`);
    return response.data;
}

export async function getThreadActionsRequest(threadId: string): Promise<ActionResponse[]> {
    const response = await apiClient.get<ActionResponse[]>(`/agent/thread/${threadId}/actions`);
    return response.data;
}

export async function runAgentWorkflowRequest(payload: AgentRunRequest): Promise<AgentRunResponse> {
    const response = await apiClient.post<AgentRunResponse>("/agent/run", payload);
    return response.data;
}

export async function submitAgentApprovalRequest(payload: AgentApproveRequest): Promise<AgentRunResponse> {
    const response = await apiClient.post<AgentRunResponse>("/agent/approve", payload);
    return response.data;
}

export async function triggerSummarizationRequest(threadId: string): Promise<any> {
    const response = await apiClient.post<any>(`/agent/thread/${threadId}/summarize`);
    return response.data;
}
