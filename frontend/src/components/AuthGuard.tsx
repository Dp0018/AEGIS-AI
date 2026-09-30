"use client";

import React, { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function AuthGuard({ children }: { children: React.ReactNode }) {
    const { user, isLoading } = useAuth();
    const router = useRouter();
    const pathname = usePathname();

    useEffect(() => {
        if (!isLoading) {
            const isPublicRoute = pathname === "/login" || pathname === "/register";
            if (!user && !isPublicRoute) {
                router.replace("/login");
            } else if (user && pathname === "/login") {
                router.replace("/");
            } else if (user && pathname === "/register" && user.role !== "admin") {
                router.replace("/");
            }
        }
    }, [user, isLoading, pathname, router]);

    if (isLoading) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-background text-muted-foreground">
                <div className="flex flex-col items-center gap-3">
                    <svg className="h-8 w-8 animate-spin text-primary" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <span className="text-sm font-medium tracking-wide">Verifying session...</span>
                </div>
            </div>
        );
    }

    const isPublicRoute = pathname === "/login" || pathname === "/register";
    const allowAdminRegister = user && pathname === "/register" && user.role === "admin";
    
    // Prevent screen flashing of guarded content
    if (!user && !isPublicRoute) return null;
    if (user && isPublicRoute && !allowAdminRegister) return null;

    return <>{children}</>;
}
