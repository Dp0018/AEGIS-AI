"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listDocumentsRequest, deleteDocumentRequest } from "../api/documents";
import { toast } from "@/components/ui/toast";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { 
    FileText, 
    Trash2, 
    Loader2, 
    FolderOpen,
    CheckCircle,
    Clock,
    AlertTriangle,
    Database
} from "lucide-react";

export function DocumentList() {
    const queryClient = useQueryClient();

    // Fetch documents, poll every 5s to update background processing status automatically
    const { data: documents, isLoading, error } = useQuery({
        queryKey: ["documents"],
        queryFn: listDocumentsRequest,
        refetchInterval: 5000,
    });

    // Delete Mutation
    const deleteMutation = useMutation({
        mutationFn: (id: string) => deleteDocumentRequest(id),
        onSuccess: () => {
            toast.add({
                title: "Document Deleted",
                description: "Document and its vector segments successfully removed.",
                type: "success",
            });
            queryClient.invalidateQueries({ queryKey: ["documents"] });
        },
        onError: (err: any) => {
            toast.add({
                title: "Deletion Failed",
                description: err.message || "Failed to delete the document.",
                type: "error",
            });
        },
    });

    const formatBytes = (bytes: number): string => {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    };

    const getStatusBadge = (status: string) => {
        switch (status) {
            case "completed":
                return (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-500">
                        <CheckCircle className="h-3.5 w-3.5" />
                        Completed
                    </span>
                );
            case "processing":
                return (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-blue-500/20 bg-blue-500/10 px-2.5 py-0.5 text-xs font-semibold text-blue-500 animate-pulse">
                        <Loader2 className="h-3.5 w-3.5 animate-spin" />
                        Processing
                    </span>
                );
            case "pending":
                return (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-yellow-500/20 bg-yellow-500/10 px-2.5 py-0.5 text-xs font-semibold text-yellow-500">
                        <Clock className="h-3.5 w-3.5" />
                        Queued
                    </span>
                );
            case "failed":
                return (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-destructive/20 bg-destructive/10 px-2.5 py-0.5 text-xs font-semibold text-destructive">
                        <AlertTriangle className="h-3.5 w-3.5" />
                        Failed
                    </span>
                );
            default:
                return (
                    <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted px-2.5 py-0.5 text-xs font-semibold text-muted-foreground">
                        Unknown
                    </span>
                );
        }
    };

    if (isLoading) {
        return (
            <Card className="border border-border/80 bg-card/40 shadow-xl backdrop-blur-xl">
                <CardContent className="flex min-h-[300px] flex-col items-center justify-center gap-2">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    <span className="text-sm font-medium text-muted-foreground">Loading documents list...</span>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card className="border border-destructive/20 bg-destructive/5 shadow-xl backdrop-blur-xl">
                <CardContent className="flex min-h-[300px] flex-col items-center justify-center text-center p-6 gap-3">
                    <AlertTriangle className="h-10 w-10 text-destructive" />
                    <div>
                        <h3 className="font-bold text-foreground">Failed to Load Documents</h3>
                        <p className="text-sm text-muted-foreground mt-1">{(error as any).message || "Database connection error."}</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    const hasDocs = documents && documents.length > 0;

    return (
        <Card className="border border-border/80 bg-card/40 shadow-xl backdrop-blur-xl flex flex-col h-full">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-6">
                <div>
                    <CardTitle className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
                        <Database className="h-5 w-5 text-primary" />
                        Ingested Documents
                    </CardTitle>
                    <CardDescription className="text-muted-foreground text-xs leading-relaxed mt-1">
                        Metadata database records sync status with vector cluster embeddings.
                    </CardDescription>
                </div>
                {hasDocs && (
                    <span className="rounded-md border border-border bg-background px-2.5 py-1 text-xs font-bold text-foreground">
                        {documents.length} Total
                    </span>
                )}
            </CardHeader>
            <CardContent className="flex-1 overflow-auto">
                {!hasDocs ? (
                    <div className="flex min-h-[220px] flex-col items-center justify-center text-center p-6 border border-dashed border-border/80 rounded-xl bg-background/10">
                        <FolderOpen className="h-10 w-10 text-muted-foreground" />
                        <p className="mt-3 text-sm font-semibold text-foreground">No documents found</p>
                        <p className="mt-1 text-xs text-muted-foreground">Upload your first document to populate the knowledge base.</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {documents.map((doc) => (
                            <div 
                                key={doc.id} 
                                className="flex flex-col sm:flex-row sm:items-center justify-between rounded-xl border border-border/80 bg-background/40 hover:bg-background/70 transition-all p-4 gap-4"
                            >
                                {/* File details column */}
                                <div className="flex items-center gap-3 min-w-0">
                                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/5 text-primary">
                                        <FileText className="h-5 w-5" />
                                    </div>
                                    <div className="min-w-0">
                                        <h4 className="truncate text-sm font-bold text-foreground" title={doc.filename}>
                                            {doc.filename}
                                        </h4>
                                        <div className="flex items-center gap-2 mt-0.5 text-xs text-muted-foreground">
                                            <span>{formatBytes(doc.file_size)}</span>
                                            <span>•</span>
                                            <span className="uppercase text-[9px] font-bold bg-muted px-1.5 py-0.5 rounded">
                                                {doc.content_type.split("/")[1] || "doc"}
                                            </span>
                                            {doc.chunks_count !== null && doc.chunks_count > 0 && (
                                                <>
                                                    <span>•</span>
                                                    <span className="text-primary font-semibold">{doc.chunks_count} segments</span>
                                                </>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Status column and actions */}
                                <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0 border-t border-border/30 pt-3 sm:border-none sm:pt-0">
                                    {getStatusBadge(doc.status)}
                                    
                                    {/* Action button */}
                                    <button
                                        onClick={() => deleteMutation.mutate(doc.id)}
                                        disabled={deleteMutation.isPending && deleteMutation.variables === doc.id}
                                        className="rounded-lg border border-border p-2 text-muted-foreground hover:bg-destructive hover:text-destructive-foreground transition-all disabled:opacity-50"
                                        aria-label="Delete Ingestion"
                                    >
                                        {deleteMutation.isPending && deleteMutation.variables === doc.id ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Trash2 className="h-4 w-4" />
                                        )}
                                    </button>
                                </div>

                                {/* Error Log Display */}
                                {doc.status === "failed" && doc.error_log && (
                                    <div className="w-full text-xs bg-destructive/5 text-destructive p-3 rounded-lg border border-destructive/15 mt-1">
                                        <strong>Ingestion Error:</strong> {doc.error_log}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
}
