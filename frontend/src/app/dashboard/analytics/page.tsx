"use client";

import React, { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { ragRetrieveRequest } from "@/features/analytics/api/analytics";
import { RAGChunkResult } from "@/features/analytics/types";
import { listDocumentsRequest } from "@/features/documents/api/documents";
import { 
    Search, Loader2, Database, FileText, 
    BarChart3, Layers, Cpu, ChevronRight, 
    AlertCircle, Sparkles
} from "lucide-react";

// Score to colour mapping helper
function scoreColor(score: number): string {
    if (score >= 0.85) return "text-emerald-500";
    if (score >= 0.70) return "text-primary";
    if (score >= 0.55) return "text-amber-500";
    return "text-rose-500";
}

function scoreBg(score: number): string {
    if (score >= 0.85) return "bg-emerald-500/10 border-emerald-500/20";
    if (score >= 0.70) return "bg-primary/10 border-primary/20";
    if (score >= 0.55) return "bg-amber-500/10 border-amber-500/20";
    return "bg-rose-500/10 border-rose-500/20";
}

function ScoreBar({ score }: { score: number }) {
    const pct = Math.round(score * 100);
    const color = score >= 0.85 ? "bg-emerald-500" : score >= 0.70 ? "bg-primary" : score >= 0.55 ? "bg-amber-500" : "bg-rose-500";
    return (
        <div className="flex items-center gap-2 w-full">
            <div className="flex-1 h-1.5 rounded-full bg-border/60 overflow-hidden">
                <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${pct}%` }} />
            </div>
            <span className={`text-[10px] font-bold tabular-nums shrink-0 ${scoreColor(score)}`}>{pct}%</span>
        </div>
    );
}

export default function AnalyticsPage() {
    const [query, setQuery] = useState("");
    const [topK, setTopK] = useState(5);
    const [results, setResults] = useState<RAGChunkResult[]>([]);
    const [searched, setSearched] = useState(false);

    // Indexed documents list
    const { data: documents } = useQuery({
        queryKey: ["documents"],
        queryFn: listDocumentsRequest,
        refetchInterval: 10000,
    });

    // RAG retrieval mutation
    const { mutate: runSearch, isPending } = useMutation({
        mutationFn: () => ragRetrieveRequest({ query, top_k: topK }),
        onSuccess: (data) => {
            setResults(data);
            setSearched(true);
        },
    });

    const completedDocs = documents?.filter(d => d.status === "completed") ?? [];
    const totalChunks = completedDocs.reduce((acc, d) => acc + (d.chunks_count ?? 0), 0);

    return (
        <div className="space-y-6 animate-fade-in pb-8">
            {/* Page Header */}
            <div className="flex flex-col gap-1">
                <h1 className="text-2xl font-extrabold tracking-tight text-foreground flex items-center gap-2.5">
                    <Sparkles className="h-6 w-6 text-primary" />
                    Retrieval Analytics
                </h1>
                <p className="text-sm text-muted-foreground">
                    Inspect semantic similarity, chunk relevance rankings, and knowledge index coverage.
                </p>
            </div>

            {/* Stats Row */}
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
                {[
                    { label: "Indexed Documents", value: completedDocs.length, icon: Database, color: "text-primary" },
                    { label: "Total Chunks", value: totalChunks, icon: Layers, color: "text-violet-500" },
                    { label: "Vector Index", value: "ChromaDB", icon: Cpu, color: "text-cyan-500" },
                    { label: "Retrieved (last)", value: searched ? results.length : "—", icon: BarChart3, color: "text-emerald-500" },
                ].map((stat) => (
                    <div key={stat.label} className="rounded-2xl border border-border/80 bg-card/60 p-4 backdrop-blur-sm shadow-sm flex items-center gap-3">
                        <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-muted/60 ${stat.color}`}>
                            <stat.icon className="h-5 w-5" />
                        </div>
                        <div className="min-w-0">
                            <p className="text-xs text-muted-foreground truncate">{stat.label}</p>
                            <p className="text-lg font-extrabold text-foreground tabular-nums">{stat.value}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Two-column layout */}
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
                
                {/* Left: Search + Results (2 cols) */}
                <div className="lg:col-span-2 space-y-4">
                    {/* Search Panel */}
                    <div className="rounded-2xl border border-border/80 bg-card/60 p-5 backdrop-blur-sm shadow-sm space-y-4">
                        <h2 className="text-sm font-extrabold text-foreground flex items-center gap-2">
                            <Search className="h-4 w-4 text-primary" />
                            Semantic Knowledge Search
                        </h2>
                        <div className="flex items-center gap-3">
                            <input
                                type="text"
                                value={query}
                                onChange={(e) => setQuery(e.target.value)}
                                onKeyDown={(e) => e.key === "Enter" && query.trim() && runSearch()}
                                placeholder="e.g. 'What is our SLA response time?'"
                                className="flex-1 h-11 rounded-xl border border-border bg-background px-4 text-sm text-foreground placeholder:text-muted-foreground/60 transition-all focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                            />
                            <select
                                value={topK}
                                onChange={(e) => setTopK(Number(e.target.value))}
                                className="h-11 rounded-xl border border-border bg-background px-3 text-sm text-foreground focus:outline-none focus:border-primary"
                            >
                                {[3, 5, 8, 10, 15, 20].map(n => (
                                    <option key={n} value={n}>Top {n}</option>
                                ))}
                            </select>
                            <button
                                onClick={() => query.trim() && runSearch()}
                                disabled={isPending || !query.trim()}
                                className="h-11 px-5 rounded-xl bg-primary text-primary-foreground text-sm font-bold transition-all hover:opacity-90 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shrink-0"
                            >
                                {isPending ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Search className="h-4 w-4" />
                                )}
                                Search
                            </button>
                        </div>
                    </div>

                    {/* Results */}
                    <div className="space-y-3">
                        {!searched && !isPending && (
                            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border/60 bg-card/20 p-12 text-center">
                                <Database className="h-10 w-10 text-muted-foreground/40 mb-3" />
                                <p className="text-sm font-bold text-foreground">Run a semantic search above</p>
                                <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                                    Query the ChromaDB vector index to inspect which knowledge chunks are most relevant to a given question.
                                </p>
                            </div>
                        )}

                        {isPending && (
                            <div className="flex items-center justify-center rounded-2xl border border-border/60 bg-card/20 p-12">
                                <div className="flex flex-col items-center gap-3">
                                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                                    <p className="text-xs font-bold text-muted-foreground font-mono">QUERYING VECTOR INDEX...</p>
                                </div>
                            </div>
                        )}

                        {searched && !isPending && results.length === 0 && (
                            <div className="flex flex-col items-center justify-center rounded-2xl border border-dashed border-border/60 bg-card/20 p-12 text-center">
                                <AlertCircle className="h-8 w-8 text-amber-500 mb-2" />
                                <p className="text-sm font-bold text-foreground">No results found</p>
                                <p className="text-xs text-muted-foreground">Try a different query or upload more documents first.</p>
                            </div>
                        )}

                        {searched && !isPending && results.map((chunk, idx) => (
                            <div
                                key={idx}
                                className={`rounded-2xl border p-5 backdrop-blur-sm shadow-sm space-y-3 transition-all ${scoreBg(chunk.score)}`}
                            >
                                {/* Chunk Header */}
                                <div className="flex items-start justify-between gap-3">
                                    <div className="flex items-center gap-2.5 min-w-0">
                                        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-background/60 border border-border/60 text-xs font-extrabold text-muted-foreground tabular-nums">
                                            {idx + 1}
                                        </div>
                                        <div className="min-w-0">
                                            <p className="text-xs font-bold text-foreground truncate flex items-center gap-1.5">
                                                <FileText className="h-3.5 w-3.5 shrink-0 text-primary" />
                                                {chunk.filename}
                                            </p>
                                            <p className="text-[10px] text-muted-foreground font-mono truncate">
                                                doc/{chunk.document_id.substring(0, 8)}...
                                            </p>
                                        </div>
                                    </div>
                                    <span className={`shrink-0 rounded-lg border px-2 py-1 text-[10px] font-extrabold uppercase tracking-wider ${scoreBg(chunk.score)} ${scoreColor(chunk.score)}`}>
                                        {chunk.score >= 0.85 ? "High Match" : chunk.score >= 0.70 ? "Good Match" : chunk.score >= 0.55 ? "Partial" : "Low Match"}
                                    </span>
                                </div>

                                {/* Score Bar */}
                                <ScoreBar score={chunk.score} />

                                {/* Chunk Text */}
                                <p className="text-xs text-muted-foreground leading-relaxed line-clamp-5 bg-background/40 rounded-xl p-3 border border-border/40 font-mono">
                                    {chunk.text}
                                </p>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right: Document Index Coverage (1 col) */}
                <div className="rounded-2xl border border-border/80 bg-card/60 p-5 backdrop-blur-sm shadow-sm h-fit space-y-4">
                    <h2 className="text-sm font-extrabold text-foreground flex items-center gap-2">
                        <Layers className="h-4 w-4 text-violet-500" />
                        Knowledge Index
                    </h2>

                    {(!documents || documents.length === 0) ? (
                        <div className="text-center py-8 text-muted-foreground">
                            <Database className="h-8 w-8 mx-auto mb-2 opacity-40" />
                            <p className="text-xs">No documents indexed yet.</p>
                            <p className="text-[10px] mt-1">Upload documents on the Ingestion page first.</p>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {documents.map((doc) => (
                                <div key={doc.id} className="flex items-center gap-3 rounded-xl border border-border/60 bg-background/30 p-3">
                                    <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-xs font-extrabold ${
                                        doc.status === "completed" ? "bg-emerald-500/10 text-emerald-500" :
                                        doc.status === "processing" ? "bg-primary/10 text-primary" :
                                        doc.status === "failed" ? "bg-rose-500/10 text-rose-500" :
                                        "bg-muted text-muted-foreground"
                                    }`}>
                                        <FileText className="h-4 w-4" />
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <p className="text-xs font-bold text-foreground truncate">{doc.filename}</p>
                                        <p className="text-[10px] text-muted-foreground">
                                            {doc.status === "completed"
                                                ? `${doc.chunks_count ?? 0} chunks indexed`
                                                : doc.status}
                                        </p>
                                    </div>
                                    <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/40 shrink-0" />
                                </div>
                            ))}
                        </div>
                    )}

                    {/* Index Stats */}
                    {completedDocs.length > 0 && (
                        <div className="rounded-xl border border-border/60 bg-muted/20 p-3 space-y-2">
                            <p className="text-[10px] font-extrabold uppercase tracking-wider text-muted-foreground">Index Summary</p>
                            <div className="flex justify-between text-xs">
                                <span className="text-muted-foreground">Ready</span>
                                <span className="font-bold text-emerald-500">{completedDocs.length} docs</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-muted-foreground">Chunks</span>
                                <span className="font-bold text-foreground">{totalChunks.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between text-xs">
                                <span className="text-muted-foreground">Vector DB</span>
                                <span className="font-bold text-cyan-500">ChromaDB</span>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
