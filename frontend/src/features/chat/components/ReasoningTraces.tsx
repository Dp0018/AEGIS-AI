"use client";

import React, { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getThreadActionsRequest } from "../api/chat";
import { useWebSocket } from "../hooks/useWebSocket";
import { ActionResponse } from "../types";
import { Loader2, Terminal, Cpu, Search, AlertCircle, PlayCircle } from "lucide-react";

interface ReasoningTracesProps {
    threadId: string | null;
}

export function ReasoningTraces({ threadId }: { threadId: string | null }) {
    const [liveActions, setLiveActions] = useState<ActionResponse[]>([]);

    // Reset live actions when switching threads
    useEffect(() => {
        setLiveActions([]);
    }, [threadId]);

    // Initial load of historical actions
    const { data: actions, isLoading, error } = useQuery({
        queryKey: ["thread-actions", threadId],
        queryFn: () => (threadId ? getThreadActionsRequest(threadId) : Promise.resolve([])),
        enabled: !!threadId,
    });

    // Listen for live event streams from Kafka over WebSockets
    useWebSocket(threadId, (message) => {
        if (message.topic === "telemetry-events" && message.data.event_type === "action_created") {
            const newAction = message.data.action as ActionResponse;
            setLiveActions((prev) => {
                if (prev.some((a) => a.id === newAction.id)) return prev;
                return [...prev, newAction];
            });
        }
    });

    // Combine historical logs and real-time streams, filtering out duplicates
    const allActions = useMemo(() => {
        const initial = actions ?? [];
        const uniqueLive = liveActions.filter(
            (la) => !initial.some((ia) => ia.id === la.id)
        );
        return [...initial, ...uniqueLive];
    }, [actions, liveActions]);

    if (!threadId) {
        return (
            <div className="flex h-full flex-col items-center justify-center p-6 text-center text-muted-foreground/60">
                <Terminal className="h-8 w-8 mb-2" />
                <span className="text-xs">No active session selected</span>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex h-full items-center justify-center p-4">
                <Loader2 className="h-5 w-5 animate-spin text-primary" />
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 text-xs text-destructive text-center">
                Failed to load telemetry logs
            </div>
        );
    }

    const hasActions = allActions.length > 0;

    return (
        <div className="flex h-full flex-col bg-card/10 border-l border-border/40 w-full overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-border/40 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" />
                <span className="text-xs font-extrabold uppercase tracking-wider text-muted-foreground">
                    Reasoning Telemetry
                </span>
            </div>

            {/* Traces List */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 font-mono text-[11px] leading-relaxed">
                {!hasActions ? (
                    <div className="flex h-[200px] flex-col items-center justify-center text-center p-4 border border-dashed border-border/60 rounded-xl bg-background/5 text-muted-foreground">
                        <Cpu className="h-8 w-8 mb-2 opacity-50" />
                        <p className="font-bold text-xs">Awaiting execution...</p>
                        <p className="text-[10px]">Intermediate agent thoughts and actions will stream here during query runs.</p>
                    </div>
                ) : (
                    allActions.map((action, idx) => {
                        const payload = action.payload || {};
                        return (
                            <div key={action.id} className="relative pl-4 border-l border-border/80 space-y-2">
                                {/* Dot Indicator */}
                                <div className="absolute -left-[4.5px] top-1.5 h-2 w-2 rounded-full bg-primary" />

                                {/* Meta Tag Header */}
                                <div className="flex items-center justify-between text-zinc-500 text-[10px]">
                                    <span className="font-bold uppercase text-primary">
                                        [{idx + 1}] {action.action_type}
                                    </span>
                                    <span>
                                        {new Date(action.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                    </span>
                                </div>

                                {/* Thought section */}
                                {payload.thought && (
                                    <div className="rounded-lg bg-primary/5 border border-primary/10 p-3 text-foreground/90">
                                        <div className="flex items-center gap-1.5 font-bold text-primary/95 text-[10px] mb-1.5">
                                            <Cpu className="h-3 w-3" />
                                            THOUGHT
                                        </div>
                                        <p>{payload.thought}</p>
                                    </div>
                                )}

                                {/* Action / Command section */}
                                {payload.action && (
                                    <div className="rounded-lg bg-zinc-950 p-3 text-zinc-300 dark:bg-black">
                                        <div className="flex items-center gap-1.5 font-bold text-yellow-500/90 text-[10px] mb-1.5">
                                            <PlayCircle className="h-3 w-3" />
                                            EXECUTE
                                        </div>
                                        <p className="text-zinc-400 font-bold">&gt; {payload.action}</p>
                                    </div>
                                )}

                                {/* Observation section */}
                                {payload.observation && (
                                    <div className="rounded-lg bg-muted/40 border border-border/40 p-3 text-muted-foreground">
                                        <div className="flex items-center gap-1.5 font-bold text-foreground/80 text-[10px] mb-1.5">
                                            <Search className="h-3 w-3" />
                                            OBSERVATION
                                        </div>
                                        <p className="line-clamp-6">{payload.observation}</p>
                                    </div>
                                )}

                                {/* Decision section */}
                                {payload.decision && (
                                    <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/15 p-3 text-emerald-600 dark:text-emerald-400/90">
                                        <div className="flex items-center gap-1.5 font-bold text-emerald-500 text-[10px] mb-1.5">
                                            <AlertCircle className="h-3 w-3" />
                                            DECISION
                                        </div>
                                        <p>{payload.decision}</p>
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
            </div>
        </div>
    );
}
