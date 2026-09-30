"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useAuth } from "../hooks/useAuth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function RegisterForm() {
    const { register, isRegistering, registerError, clearRegisterError } = useAuth();
    const [email, setEmail] = useState("");
    const [fullName, setFullName] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState<"admin" | "operator" | "viewer">("operator");
    const [validationError, setValidationError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setValidationError(null);
        clearRegisterError();

        if (!email.trim() || !fullName.trim() || !password.trim()) {
            setValidationError("Please fill in all fields.");
            return;
        }

        if (password.length < 6) {
            setValidationError("Password must be at least 6 characters.");
            return;
        }

        try {
            await register({
                email,
                full_name: fullName,
                password,
                role
            });
        } catch {
            // Handled by react-query mutation
        }
    };

    return (
        <div className="w-full max-w-md animate-fade-in p-6">
            <div className="space-y-6">
                
                {/* Node Status Indicator */}
                <div className="flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-cyan-500 animate-pulse" />
                    <span className="text-[11px] font-bold uppercase tracking-wider text-cyan-500/90">
                        IAM Registration Gateway
                    </span>
                </div>

                {/* Left-Aligned Header with brand accent line */}
                <div className="relative border-l-2 border-primary pl-4 space-y-1">
                    <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
                        Create Profile
                    </h1>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                        Register a new coordinate identity (First user becomes ADMIN).
                    </p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-6 pt-4">
                    {/* Error Alerts */}
                    {(registerError || validationError) && (
                        <div className="flex items-center gap-3 rounded-xl border border-destructive/25 bg-destructive/10 p-4 text-sm text-destructive backdrop-blur-md">
                            <svg className="h-5 w-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span>{validationError || registerError}</span>
                        </div>
                    )}

                    <div className="space-y-4">
                        {/* Full Name Input */}
                        <div className="space-y-2">
                            <Label htmlFor="fullName" className="text-xs font-bold uppercase tracking-wider text-foreground/70">
                                Full Name
                            </Label>
                            <Input
                                id="fullName"
                                type="text"
                                placeholder="Alex Mercer"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="h-12 px-4 text-base border-border bg-card/40 backdrop-blur-md text-foreground transition-all focus:bg-background focus:ring-1 focus:ring-primary focus:border-primary placeholder:text-muted-foreground/45"
                                disabled={isRegistering}
                            />
                        </div>

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
                                disabled={isRegistering}
                            />
                        </div>

                        {/* Role Designation */}
                        <div className="space-y-2">
                            <Label htmlFor="role" className="text-xs font-bold uppercase tracking-wider text-foreground/70">
                                Role Designation
                            </Label>
                            <Select
                                value={role}
                                onValueChange={(val: any) => setRole(val)}
                                disabled={isRegistering}
                            >
                                <SelectTrigger className="h-12 px-4 border-border bg-card/40 backdrop-blur-md text-foreground transition-all focus:bg-background focus:ring-1 focus:ring-primary focus:border-primary">
                                    <SelectValue placeholder="Select a role" />
                                </SelectTrigger>
                                <SelectContent className="border-border bg-card/95 backdrop-blur-2xl text-foreground">
                                    <SelectItem value="viewer">Viewer (Read-only)</SelectItem>
                                    <SelectItem value="operator">Operator (HITL Reviews)</SelectItem>
                                    <SelectItem value="admin">Administrator (IAM & Uploads)</SelectItem>
                                </SelectContent>
                            </Select>
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
                                disabled={isRegistering}
                            />
                        </div>
                    </div>

                    <Button
                        type="submit"
                        className="h-12 w-full bg-primary text-primary-foreground text-base font-bold tracking-wide shadow-lg hover:shadow-primary/20 transition-all active:scale-[0.99] hover:bg-primary/90"
                        disabled={isRegistering}
                    >
                        {isRegistering ? (
                            <span className="flex items-center justify-center gap-2">
                                <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                </svg>
                                Deploying Node...
                            </span>
                        ) : (
                            "Deploy Operator Node"
                        )}
                    </Button>

                    <div className="text-center text-sm text-muted-foreground border-t border-border/40 pt-6 mt-6">
                        Already Registered?{" "}
                        <Link href="/login" className="font-semibold text-primary hover:underline hover:text-primary/95">
                            Establish Session
                        </Link>
                    </div>
                </form>
            </div>
        </div>
    );
}
