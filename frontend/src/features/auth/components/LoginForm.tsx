"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "../hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function LoginForm() {
    const { login, isLoggingIn, loginError, clearLoginError } = useAuth();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [validationError, setValidationError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setValidationError(null);
        clearLoginError();

        if (!email.trim() || !password.trim()) {
            setValidationError("Please fill in all fields.");
            return;
        }

        try {
            await login({ email, password });
        } catch {
            // Handled by react-query mutation
        }
    };

    return (
        <div className="w-full max-w-md animate-fade-in p-6">
            <div className="space-y-6">
                
                {/* Node Status Indicator */}
                <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                    <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-500/90">
                        Node Authentication Gateway
                    </span>
                </div>

                {/* Left-Aligned Header with brand accent line */}
                <div className="relative border-l-2 border-primary pl-4 space-y-1">
                    <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
                        Operator Sign In
                    </h1>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        Provide credentials to unlock the Aether Control dashboard.
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    {/* Error Alerts */}
                    {(loginError || validationError) && (
                        <div className="flex items-center gap-3 rounded-xl border border-destructive/25 bg-destructive/10 p-4 text-sm text-destructive backdrop-blur-md">
                            <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>{validationError || loginError}</span>
                        </div>
                    )}

                    <div className="space-y-4">
                        {/* Email Input */}
                        <div className="space-y-2">
                            <Label htmlFor="email" className="text-xs font-bold uppercase tracking-wider text-foreground/70">
                                Email Address
                            </Label>
                            <Input
                                id="email"
                                type="email"
                                placeholder="operator@aegisai.com"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="h-12 px-4 text-base border-border bg-card/40 backdrop-blur-md text-foreground transition-all focus:bg-background focus:ring-1 focus:ring-primary focus:border-primary placeholder:text-muted-foreground/45"
                                disabled={isLoggingIn}
                            />
                        </div>

                        {/* Password Input */}
                        <div className="space-y-2">
                            <Label htmlFor="password" className="text-xs font-bold uppercase tracking-wider text-foreground/70">
                                Password
                            </Label>
                            <Input
                                id="password"
                                type="password"
                                placeholder="••••••••"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="h-12 px-4 text-base border-border bg-card/40 backdrop-blur-md text-foreground transition-all focus:bg-background focus:ring-1 focus:ring-primary focus:border-primary placeholder:text-muted-foreground/45"
                                disabled={isLoggingIn}
                            />
                        </div>
                    </div>

                    <Button
                        type="submit"
                        className="h-12 w-full bg-primary text-primary-foreground text-base font-bold tracking-wide shadow-lg hover:shadow-primary/20 transition-all active:scale-[0.99] hover:bg-primary/90"
                        disabled={isLoggingIn}
                    >
                        {isLoggingIn ? (
                            <span className="flex items-center justify-center gap-2">
                                <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                Authenticating...
                            </span>
                        ) : (
                            "Establish Session"
                        )}
                    </Button>

                    <div className="text-center text-sm text-muted-foreground border-t border-border/40 pt-6 mt-6">
                        New Operator Node?{" "}
                        <Link href="/register" className="font-semibold text-primary hover:underline hover:text-primary/95">
                            Register Profile
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
}
