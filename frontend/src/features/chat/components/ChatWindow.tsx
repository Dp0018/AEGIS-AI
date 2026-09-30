"use client";

import React, { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getThreadHistoryRequest, runAgentWorkflowRequest, submitAgentApprovalRequest } from "../api/chat";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/ui/toast";
import { 
    Send, 
    Loader2, 
    User, 
    Cpu, 
    CheckCircle, 
    XCircle, 
    AlertTriangle,
    FileCode
} from "lucide-react";

interface ChatWindowProps {
    threadId: string | null;
}

export function ChatWindow({ threadId }: ChatWindowProps) {
    const queryClient = useQueryClient();
    const [inputValue, setInputValue] = useState("");
    const [requiresApproval, setRequiresApproval] = useState(false);
    const [pendingDraft, setPendingDraft] = useState<string | null>(null);
    const [feedback, setFeedback] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);

    // Fetch message history
    const { data: messages, isLoading, error } = useQuery({
        queryKey: ["thread-history", threadId],
        queryFn: () => (threadId ? getThreadHistoryRequest(threadId) : Promise.resolve([])),
        enabled: !!threadId,
        refetchInterval: 3000, // Poll to retrieve background replies
    });

    // Run Agent Mutation
    const runMutation = useMutation({
        mutationFn: (query: string) => {
            if (!threadId) throw new Error("No active thread");
            return runAgentWorkflowRequest({ query, thread_id: threadId });
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["thread-history", threadId] });
            queryClient.invalidateQueries({ queryKey: ["thread-actions", threadId] });
            queryClient.invalidateQueries({ queryKey: ["threads"] });

            if (data.requires_approval) {
                setRequiresApproval(true);
                setPendingDraft(data.response);
            } else {
                setRequiresApproval(false);
                setPendingDraft(null);
            }
        },
        onError: (err: any) => {
            toast.add({
                title: "Agent Error",
                description: err.message || "Failed to execute agent workflow.",
                type: "error",
            });
        },
    });

    // Submit Approval Mutation
    const approveMutation = useMutation({
        mutationFn: (approved: boolean) => {
            if (!threadId) throw new Error("No active thread");
            return submitAgentApprovalRequest({
                thread_id: threadId,
                approved,
                feedback: approved ? null : feedback,
            });
        },
        onSuccess: (data) => {
            toast.add({
                title: approveMutation.variables ? "Response Released" : "Feedback Logged",
                description: approveMutation.variables 
                    ? "Agent draft approved and dispatched." 
                    : "Feedback submitted. Requesting redraft.",
                type: approveMutation.variables ? "success" : "info",
            });

            setRequiresApproval(false);
            setPendingDraft(null);
            setFeedback("");

            queryClient.invalidateQueries({ queryKey: ["thread-history", threadId] });
            queryClient.invalidateQueries({ queryKey: ["thread-actions", threadId] });
            queryClient.invalidateQueries({ queryKey: ["threads"] });
        },
        onError: (err: any) => {
            toast.add({
                title: "Action Failed",
                description: err.message || "Failed to submit operator decision.",
                type: "error",
            });
        },
    });

    // Auto-scroll to bottom
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // Check if the last message in history required approval
    useEffect(() => {
        if (messages && messages.length > 0) {
            const lastMsg = messages[messages.length - 1];
            // If the last message is an unapproved assistant draft, we can show approval box
            if (lastMsg.role === "assistant" && lastMsg.content.includes("requires approval")) {
                setRequiresApproval(true);
                setPendingDraft(lastMsg.content);
            }
        }
    }, [messages]);

    const handleSend = (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputValue.trim() || runMutation.isPending) return;

        runMutation.mutate(inputValue.trim());
        setInputValue("");
    };

    if (!threadId) {
        return (
            <div className="flex h-full min-h-[60vh] flex-col items-center justify-center text-center p-6 text-muted-foreground/60">
                <MessageSquareIcon className="h-10 w-10 mb-3 text-muted-foreground/40" />
                <h3 className="font-bold text-foreground">No Session Selected</h3>
                <p className="text-xs max-w-xs mt-1">Select an active session thread from the sidebar or start a new one to begin.</p>
            </div>
        );
    }

    return (
        <div className="flex h-full flex-col bg-transparent w-full overflow-hidden">
            {/* Scrollable Messages Panel */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-[45vh]">
                {isLoading ? (
                    <div className="flex h-full items-center justify-center">
                        <Loader2 className="h-6 w-6 animate-spin text-primary" />
                    </div>
                ) : error ? (
                    <div className="text-xs text-destructive text-center p-4">
                        Failed to retrieve history logs
                    </div>
                ) : !messages || messages.length === 0 ? (
                    <div className="flex h-full min-h-[300px] flex-col items-center justify-center text-center text-muted-foreground/60">
                        <FileCode className="h-8 w-8 mb-2 opacity-50" />
                        <p className="text-xs font-bold text-foreground">Clean Session Terminal</p>
                        <p className="text-[10px]">Send the first customer query below to activate coordinator nodes.</p>
                    </div>
                ) : (
                    messages.map((msg) => {
                        const isUser = msg.role === "user";
                        const isFeedback = msg.role === "human_feedback";
                        return (
                            <div
                                key={msg.id}
                                className={`flex w-full gap-3 ${
                                    isUser ? "justify-end" : "justify-start"
                                }`}
                            >
                                {/* Left icon for assistant */}
                                {!isUser && (
                                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${
                                        isFeedback ? "bg-amber-500/10 text-amber-500" : "bg-primary/10 text-primary"
                                    }`}>
                                        <Cpu className="h-4 w-4" />
                                    </div>
                                )}

                                {/* Bubble */}
                                <div className={`max-w-[80%] rounded-xl px-4 py-3 text-sm shadow-sm leading-relaxed ${
                                    isUser
                                        ? "bg-primary text-primary-foreground font-medium"
                                        : isFeedback
                                        ? "bg-amber-500/5 border border-amber-500/20 text-amber-600 dark:text-amber-400 font-mono text-xs"
                                        : "bg-card border border-border/80 text-foreground"
                                }`}>
                                    {isFeedback && <strong className="block text-[10px] uppercase font-extrabold tracking-wide mb-1 text-amber-500">Operator Review Feedback</strong>}
                                    <p className="whitespace-pre-wrap">{msg.content}</p>
                                    <span className={`block text-[9px] mt-1.5 text-right ${isUser ? "text-primary-foreground/75" : "text-muted-foreground"}`}>
                                        {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                </div>

                                {/* Right icon for User */}
                                {isUser && (
                                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                                        <User className="h-4 w-4" />
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Human-in-the-Loop (HITL) Approval card */}
            {requiresApproval && (
                <div className="border-t border-amber-500/30 bg-amber-500/5 p-4 space-y-4 backdrop-blur-md animate-fade-in">
                    <div className="flex items-center gap-2 text-amber-600 dark:text-amber-400">
                        <AlertTriangle className="h-4.5 w-4.5 shrink-0 animate-pulse" />
                        <span className="text-xs font-extrabold uppercase tracking-wider">
                            Operator Action Required (Human-in-the-Loop)
                        </span>
                    </div>

                    {pendingDraft && (
                        <div className="rounded-xl border border-border/80 bg-card/60 p-4 text-xs text-foreground max-h-[160px] overflow-y-auto font-sans leading-relaxed">
                            <strong className="block text-[10px] uppercase tracking-wide text-primary mb-1">Proposed Draft Response</strong>
                            <p className="whitespace-pre-wrap">{pendingDraft}</p>
                        </div>
                    )}

                    <div className="space-y-3">
                        <textarea
                            placeholder="Add revision comments here if requesting a redraft..."
                            value={feedback}
                            onChange={(e) => setFeedback(e.target.value)}
                            disabled={approveMutation.isPending}
                            className="w-full min-h-[70px] rounded-xl border border-border bg-background p-3 text-xs text-foreground placeholder:text-muted-foreground/60 transition-all focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                        />
                        <div className="flex items-center justify-between gap-3">
                            <Button
                                onClick={() => approveMutation.mutate(false)}
                                disabled={approveMutation.isPending || !feedback.trim()}
                                variant="outline"
                                className="flex-1 h-11 border-amber-500/40 text-amber-600 hover:bg-amber-500/10 hover:text-amber-700 dark:text-amber-400 font-bold"
                            >
                                <XCircle className="h-4 w-4 mr-2" />
                                Request Redraft
                            </Button>
                            <Button
                                onClick={() => approveMutation.mutate(true)}
                                disabled={approveMutation.isPending}
                                className="flex-1 h-11 bg-emerald-600 text-white hover:bg-emerald-500 hover:shadow-lg hover:shadow-emerald-500/10 font-bold"
                            >
                                <CheckCircle className="h-4 w-4 mr-2" />
                                Approve & Release
                            </Button>
                        </div>
                    </div>
                </div>
            )}

            {/* Standard Input Form */}
            {!requiresApproval && (
                <form onSubmit={handleSend} className="border-t border-border/40 p-4 bg-card/10 backdrop-blur-md flex items-center gap-3">
                    <Input
                        type="text"
                        placeholder="Type customer query to trigger LangGraph workflow..."
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        disabled={runMutation.isPending}
                        className="flex-1 h-12 px-4 text-base border-border bg-background text-foreground transition-all focus:border-primary focus:ring-1 focus:ring-primary"
                    />
                    <Button
                        type="submit"
                        disabled={runMutation.isPending || !inputValue.trim()}
                        className="h-12 w-12 rounded-xl bg-primary text-primary-foreground shrink-0 shadow-lg hover:shadow-primary/10 transition-all active:scale-95"
                    >
                        {runMutation.isPending ? (
                            <Loader2 className="h-5 w-5 animate-spin" />
                        ) : (
                            <Send className="h-5 w-5" />
                        )}
                    </Button>
                </form>
            )}
        </div>
    );
}

// Simple placeholder icon
function MessageSquareIcon({ className }: { className?: string }) {
    return (
        <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.129.166 2.27.293 3.423.379.35.026.67.21.865.501L12 21l2.755-4.133a1.14 1.14 0 01.865-.501 48.172 48.172 0 003.423-.379c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0012 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018z" />
        </svg>
    );
}
