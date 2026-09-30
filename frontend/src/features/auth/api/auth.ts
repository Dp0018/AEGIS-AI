import { apiClient } from "@/lib/api-client";
import { RegisterPayload, LoginPayload, AuthResponse, UserResponse } from "../types";

export async function loginRequest(payload: LoginPayload): Promise<AuthResponse> {
    const params = new URLSearchParams();
    params.append("username", payload.email);
    params.append("password", payload.password);

    const response = await apiClient.post<AuthResponse>("/auth/token", params, {
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
    });
    return response.data;
}

export async function registerRequest(payload: RegisterPayload): Promise<UserResponse> {
    const response = await apiClient.post<UserResponse>("/auth/register", payload);
    return response.data;
}

export async function logoutRequest(refreshToken: string): Promise<{ detail: string }> {
    const response = await apiClient.post<{ detail: string }>("/auth/logout", {
        refresh_token: refreshToken,
    });
    return response.data;
}

export async function listUsersRequest(): Promise<UserResponse[]> {
    const response = await apiClient.get<UserResponse[]>("/auth/users");
    return response.data;
}
