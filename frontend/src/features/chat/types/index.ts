export interface ThreadResponse {
    id: string;
    user_id: string | null;
    created_at: string;
    updated_at: string;
}

export interface MessageResponse {
    id: string;
    thread_id: string;
    role: "user" | "assistant" | "system" | "human_feedback";
    content: string;
    created_at: string;
}

export interface ActionResponse {
    id: string;
    thread_id: string;
    action_type: string;
    payload: {
        thought?: string;
        action?: string;
        observation?: string;
        decision?: string;
        [key: string]: any;
    };
    created_at: string;
}

export interface AgentRunRequest {
    query: string;
    thread_id: string;
}

export interface AgentApproveRequest {
    thread_id: string;
    approved: boolean;
    feedback: string | null;
}

export interface AgentRunResponse {
    thread_id: string;
    response: string | null;
    requires_approval: boolean;
    escalated: boolean;
}
