"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { listThreadsRequest } from "../api/chat";
import { Loader2, Plus, MessageSquare, ShieldCheck } from "lucide-react";

interface ThreadListProps {
    selectedId: string | null;
    onSelect: (id: string) => void;
    onStartNew: () => void;
}

export function ThreadList({ selectedId, onSelect, onStartNew }: ThreadListProps) {
    const { data: threads, isLoading, error } = useQuery({
        queryKey: ["threads"],
        queryFn: listThreadsRequest,
        refetchInterval: 6000, // Sync sessions index list
    });

    const formatTimestamp = (isoStr: string) => {
        try {
            const date = new Date(isoStr);
            return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } catch {
            return "Just now";
        }
    };

    if (isLoading) {
        return (
            <div className="flex h-full flex-col items-center justify-center p-4">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
                <span className="text-xs text-muted-foreground mt-2">Loading threads...</span>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 text-xs text-destructive text-center">
                Failed to load threads
            </div>
        );
    }

    const hasThreads = threads && threads.length > 0;

    return (
        <div className="flex h-full flex-col bg-card/10 border-r border-border/40 w-full shrink-0">
            {/* Header with New Session button */}
            <div className="p-4 border-b border-border/40 flex items-center justify-between gap-3">
                <span className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                    Active Threads
                </span>
                <button
                    onClick={onStartNew}
                    className="flex items-center gap-1.5 rounded-lg bg-primary/10 border border-primary/20 px-2.5 py-1.5 text-xs font-bold text-primary transition-all hover:bg-primary hover:text-primary-foreground active:scale-95"
                >
                    <Plus className="h-3.5 w-3.5" />
                    New Session
                </button>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
                {!hasThreads ? (
                    <div className="flex h-[180px] flex-col items-center justify-center text-center p-4 border border-dashed border-border/60 rounded-xl bg-background/5">
                        <MessageSquare className="h-8 w-8 text-muted-foreground/60" />
                        <p className="mt-2 text-xs font-bold text-foreground">No active threads</p>
                        <p className="text-[10px] text-muted-foreground">Start a new session to trigger agent workflows.</p>
                    </div>
                ) : (
                    threads.map((thread) => {
                        const isSelected = selectedId === thread.id;
                        return (
                            <button
                                key={thread.id}
                                onClick={() => onSelect(thread.id)}
                                className={`w-full flex flex-col gap-1.5 text-left rounded-xl p-3.5 transition-all ${
                                    isSelected
                                        ? "bg-primary/10 border border-primary/25 text-foreground shadow-sm"
                                        : "border border-transparent text-muted-foreground hover:bg-accent/40 hover:text-foreground"
                                }`}
                            >
                                <div className="flex items-center justify-between w-full min-w-0 gap-2">
                                    <div className="flex items-center gap-2 min-w-0">
                                        <MessageSquare className={`h-4 w-4 shrink-0 ${isSelected ? "text-primary" : "text-muted-foreground/60"}`} />
                                        <span className="truncate text-xs font-bold text-foreground">
                                            {thread.id.substring(0, 8)}...
                                        </span>
                                    </div>
                                    <span className="text-[9px] text-muted-foreground tabular-nums shrink-0">
                                        {formatTimestamp(thread.updated_at)}
                                    </span>
                                </div>
                                <div className="flex items-center gap-1.5 text-[9px] font-medium text-muted-foreground/80">
                                    <ShieldCheck className="h-3 w-3 text-emerald-500/80" />
                                    <span className="truncate">Operator Node Secure</span>
                                </div>
                            </button>
                        );
                    })
                )}
            </div>
        </div>
    );
}
