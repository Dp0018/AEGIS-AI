export interface LoginPayload {
    email: string;
    password: string;
}

export interface RegisterPayload {
    email: string;
    full_name: string;
    role: "admin" | "operator" | "viewer";
    password: string;
}

export interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface UserResponse {
    id: string;
    email: string;
    full_name: string;
    role: "admin" | "operator" | "viewer";
    is_active: boolean;
    created_at: string;
}

export interface UserSession {
    id: string;
    email: string;
    full_name: string;
    role: "admin" | "operator" | "viewer";
}
