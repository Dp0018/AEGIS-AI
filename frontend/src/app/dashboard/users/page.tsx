"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listUsersRequest, registerRequest } from "@/features/auth/api/auth";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { 
    Users, UserPlus, Shield, Activity, 
    CheckCircle2, Loader2, Mail, Lock, User
} from "lucide-react";
import { toast } from "@/components/ui/toast";

export default function UsersPage() {
    const queryClient = useQueryClient();
    const { user: currentAdmin } = useAuth();
    const [email, setEmail] = useState("");
    const [fullName, setFullName] = useState("");
    const [password, setPassword] = useState("");
    const [role, setRole] = useState<"admin" | "operator" | "viewer">("operator");
    const [validationError, setValidationError] = useState<string | null>(null);

    // List all users in system (enabled only if logged in as admin)
    const { data: users, isLoading, error } = useQuery({
        queryKey: ["users-list"],
        queryFn: listUsersRequest,
        enabled: currentAdmin?.role === "admin",
    });

    // Create user mutation
    const { mutate: createUser, isPending } = useMutation({
        mutationFn: registerRequest,
        onSuccess: (newUser) => {
            queryClient.invalidateQueries({ queryKey: ["users-list"] });
            toast.add({
                title: "User Registered Successfully",
                description: `Created new profile for ${newUser.full_name} (${newUser.role})`,
                type: "success",
            });
            // Reset form
            setEmail("");
            setFullName("");
            setPassword("");
            setRole("operator");
            setValidationError(null);
        },
        onError: (err: any) => {
            toast.add({
                title: "Registration Failed",
                description: err.message || "Failed to create user.",
                type: "error",
            });
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setValidationError(null);

        if (!email.trim() || !fullName.trim() || !password.trim()) {
            setValidationError("Please fill in all fields.");
            return;
        }

        if (password.length < 6) {
            setValidationError("Password must be at least 6 characters.");
            return;
        }

        createUser({
            email,
            full_name: fullName,
            password,
            role,
        });
    };

    return (
        <div className="space-y-6 animate-fade-in pb-8">
            {/* Page Header */}
            <div className="flex flex-col gap-1">
                <h1 className="text-2xl font-extrabold tracking-tight text-foreground flex items-center gap-2.5">
                    <Users className="h-6 w-6 text-primary" />
                    Team Management
                </h1>
                <p className="text-sm text-muted-foreground">
                    Register platform operators, grant administration rights, and view coordinate identities.
                </p>
            </div>

            {/* Split Layout */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                {/* Left: Users List (2 cols) */}
                <div className="lg:col-span-2 space-y-4">
                    <div className="rounded-2xl border border-border/80 bg-card/60 p-5 backdrop-blur-sm shadow-sm space-y-4">
                        <h2 className="text-sm font-extrabold text-foreground flex items-center gap-2">
                            <Users className="h-4 w-4 text-primary" />
                            Registered Coordinate Identities
                        </h2>

                        {isLoading && (
                            <div className="flex items-center justify-center p-8">
                                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                            </div>
                        )}

                        {error && (
                            <div className="text-xs text-destructive text-center p-4">
                                Failed to retrieve user profiles.
                            </div>
                        )}

                        {!isLoading && !error && users && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {users.map((u) => (
                                    <div 
                                        key={u.id} 
                                        className="rounded-xl border border-border/60 bg-background/30 p-4 space-y-3 relative hover:border-primary/40 transition-all"
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div className="flex items-center gap-3 min-w-0">
                                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary font-bold text-sm">
                                                    {u.full_name.charAt(0).toUpperCase()}
                                                </div>
                                                <div className="min-w-0">
                                                    <p className="text-xs font-bold text-foreground truncate">{u.full_name}</p>
                                                    <p className="text-[10px] text-muted-foreground truncate">{u.email}</p>
                                                </div>
                                            </div>
                                            <span className={`shrink-0 rounded-lg border px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider ${
                                                u.role === "admin" 
                                                    ? "bg-rose-500/10 border-rose-500/20 text-rose-500" 
                                                    : u.role === "operator"
                                                    ? "bg-primary/10 border-primary/20 text-primary"
                                                    : "bg-muted border-border/60 text-muted-foreground"
                                            }`}>
                                                {u.role}
                                            </span>
                                        </div>

                                        <div className="flex items-center gap-1.5 text-[9px] font-bold text-muted-foreground/80 font-mono">
                                            <Shield className="h-3 w-3 text-cyan-500" />
                                            <span>STATUS: </span>
                                            <span className={u.is_active ? "text-emerald-500" : "text-destructive"}>
                                                {u.is_active ? "ACTIVE" : "INACTIVE"}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right: Registration Form (1 col) */}
                <div className="rounded-2xl border border-border/80 bg-card/60 p-5 backdrop-blur-sm shadow-sm space-y-4 h-fit">
                    <h2 className="text-sm font-extrabold text-foreground flex items-center gap-2">
                        <UserPlus className="h-4 w-4 text-violet-500" />
                        Add Coordinate Profile
                    </h2>

                    <form onSubmit={handleSubmit} className="space-y-4">
                        {(validationError) && (
                            <div className="rounded-xl border border-destructive/25 bg-destructive/10 p-3 text-[11px] text-destructive">
                                {validationError}
                            </div>
                        )}

                        <div className="space-y-3">
                            {/* Full Name */}
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Full Name</label>
                                <div className="relative">
                                    <User className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground/50" />
                                    <input
                                        type="text"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        placeholder="E.g. Darshan Patel"
                                        disabled={isPending}
                                        className="w-full h-10 pl-10 pr-3 rounded-xl border border-border bg-background text-xs text-foreground focus:outline-none focus:border-primary placeholder:text-muted-foreground/50"
                                    />
                                </div>
                            </div>

                            {/* Email */}
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Email Address</label>
                                <div className="relative">
                                    <Mail className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground/50" />
                                    <input
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="E.g. operator@company.com"
                                        disabled={isPending}
                                        className="w-full h-10 pl-10 pr-3 rounded-xl border border-border bg-background text-xs text-foreground focus:outline-none focus:border-primary placeholder:text-muted-foreground/50"
                                    />
                                </div>
                            </div>

                            {/* Role Dropdown */}
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Role Designation</label>
                                <select
                                    value={role}
                                    onChange={(e) => setRole(e.target.value as any)}
                                    disabled={isPending}
                                    className="w-full h-10 px-3 rounded-xl border border-border bg-background text-xs text-foreground focus:outline-none focus:border-primary"
                                >
                                    <option value="viewer">Viewer (Read-only)</option>
                                    <option value="operator">Operator (HITL Reviews)</option>
                                    <option value="admin">Administrator (Full Access)</option>
                                </select>
                            </div>

                            {/* Password */}
                            <div className="space-y-1">
                                <label className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">Secure Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3.5 top-3 h-4 w-4 text-muted-foreground/50" />
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="••••••••"
                                        disabled={isPending}
                                        className="w-full h-10 pl-10 pr-3 rounded-xl border border-border bg-background text-xs text-foreground focus:outline-none focus:border-primary placeholder:text-muted-foreground/50"
                                    />
                                </div>
                            </div>
                        </div>

                        <button
                            type="submit"
                            disabled={isPending}
                            className="w-full h-10 rounded-xl bg-primary text-primary-foreground text-xs font-bold transition-all hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        >
                            {isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <UserPlus className="h-4 w-4" />
                            )}
                            Create Coordinate Profile
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}
