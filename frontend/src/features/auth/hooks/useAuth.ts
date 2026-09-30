"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { LoginPayload, RegisterPayload, UserSession } from "../types";
import { loginRequest, registerRequest, logoutRequest } from "../api/auth";
import { toast } from "@/components/ui/toast";

export function parseJwt(token: string): any {
    try {
        const base64Url = token.split(".")[1];
        const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
        const jsonPayload = decodeURIComponent(
            window
                .atob(base64)
                .split("")
                .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
                .join("")
        );
        return JSON.parse(jsonPayload);
    } catch {
        return null;
    }
}

export function useAuth() {
    const queryClient = useQueryClient();
    const router = useRouter();

    // Query to fetch and decode the current user session from localStorage
    const { data: user, isLoading } = useQuery<UserSession | null>({
        queryKey: ["user"],
        queryFn: () => {
            if (typeof window === "undefined") return null;

            const token = localStorage.getItem("access_token");
            const storedEmail = localStorage.getItem("user_email");
            const storedName = localStorage.getItem("user_name");

            if (token) {
                const claims = parseJwt(token);
                if (claims && claims.sub) {
                    const now = Math.floor(Date.now() / 1000);
                    if (claims.exp && claims.exp < now) {
                        // Expired, perform cleanup
                        localStorage.removeItem("access_token");
                        localStorage.removeItem("refresh_token");
                        localStorage.removeItem("user_email");
                        localStorage.removeItem("user_name");
                        return null;
                    }
                    const rawRole = claims.role || "operator";
                    const normalizedRole = rawRole.toLowerCase().replace("userrole.", "");
                    return {
                        id: claims.sub,
                        email: storedEmail || "user@aegisai.com",
                        full_name: storedName || "Operator User",
                        role: normalizedRole as any,
                    };
                }
            }
            return null;
        },
        staleTime: Infinity, // Keep session memory active
    });

    // Login Mutation
    const loginMutation = useMutation({
        mutationFn: async (payload: LoginPayload) => {
            const response = await loginRequest(payload);
            localStorage.setItem("access_token", response.access_token);
            localStorage.setItem("refresh_token", response.refresh_token);
            localStorage.setItem("user_email", payload.email);

            const claims = parseJwt(response.access_token);
            const rawRole = claims?.role || "operator";
            const normalizedRole = rawRole.toLowerCase().replace("userrole.", "");
            const userSession: UserSession = {
                id: claims?.sub || "",
                email: payload.email,
                full_name: claims?.name || "Operator User",
                role: normalizedRole as any,
            };

            localStorage.setItem("user_name", userSession.full_name);
            return userSession;
        },
        onSuccess: (userSession) => {
            queryClient.setQueryData(["user"], userSession);
            toast.add({
                title: "Signed In Successfully",
                description: `Welcome back, ${userSession.full_name}!`,
                type: "success",
            });
            router.push("/");
        },
        onError: (err: any) => {
            toast.add({
                title: "Login Failed",
                description: err.message || "Invalid email or password.",
                type: "error",
            });
        },
    });

    // Register Mutation
    const registerMutation = useMutation({
        mutationFn: (payload: RegisterPayload) => registerRequest(payload),
        onSuccess: (data) => {
            toast.add({
                title: "Account Created Successfully",
                description: user ? "New profile has been registered." : "You can now log in to the console.",
                type: "success",
            });
            if (user) {
                router.push("/");
            } else {
                router.push("/login");
            }
        },
        onError: (err: any) => {
            toast.add({
                title: "Registration Failed",
                description: err.message || "Could not register new profile.",
                type: "error",
            });
        },
    });

    // Logout Mutation
    const logoutMutation = useMutation({
        mutationFn: async () => {
            const refreshToken = localStorage.getItem("refresh_token");
            if (refreshToken) {
                try {
                    await logoutRequest(refreshToken);
                } catch (err) {
                    console.error("Logout request error:", err);
                }
            }
        },
        onSettled: () => {
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            localStorage.removeItem("user_email");
            localStorage.removeItem("user_name");

            queryClient.setQueryData(["user"], null);
            toast.add({
                title: "Logged Out Successfully",
                description: "Your session has been terminated.",
                type: "info",
            });
            router.replace("/login");
        },
    });

    return {
        user,
        isLoading,
        login: loginMutation.mutateAsync,
        isLoggingIn: loginMutation.isPending,
        loginError: loginMutation.error ? loginMutation.error.message : null,
        clearLoginError: () => loginMutation.reset(),

        register: registerMutation.mutateAsync,
        isRegistering: registerMutation.isPending,
        registerError: registerMutation.error ? registerMutation.error.message : null,
        clearRegisterError: () => registerMutation.reset(),

        logout: logoutMutation.mutateAsync,
        isLoggingOut: logoutMutation.isPending,
    };
}
