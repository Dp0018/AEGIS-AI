"use client";

import React, { useState, useRef } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadDocumentRequest } from "../api/documents";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { toast } from "@/components/ui/toast";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadCloud, FileText, X } from "lucide-react";

export function DocumentUpload() {
    const queryClient = useQueryClient();
    const [file, setFile] = useState<File | null>(null);
    const [dragActive, setDragActive] = useState(false);
    const [uploadProgress, setUploadProgress] = useState(0);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const uploadMutation = useMutation({
        mutationFn: async (targetFile: File) => {
            setUploadProgress(0);
            return await uploadDocumentRequest(targetFile, (pct) => {
                setUploadProgress(pct);
            });
        },
        onSuccess: (data) => {
            toast.add({
                title: "Document Ingested",
                description: `"${data.filename}" uploaded. Processing started in background.`,
                type: "success",
            });
            setFile(null);
            setUploadProgress(0);
            queryClient.invalidateQueries({ queryKey: ["documents"] });
        },
        onError: (err: any) => {
            toast.add({
                title: "Ingestion Failed",
                description: err.message || "Failed to parse and upload the document.",
                type: "error",
            });
            setUploadProgress(0);
        },
    });

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            validateAndSetFile(e.dataTransfer.files[0]);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            validateAndSetFile(e.target.files[0]);
        }
    };

    const validateAndSetFile = (selectedFile: File) => {
        const allowedTypes = [
            "application/pdf",
            "text/plain",
            "text/markdown",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ];

        if (!allowedTypes.includes(selectedFile.type) && !selectedFile.name.endsWith(".md")) {
            toast.add({
                title: "Unsupported File",
                description: "Allowed formats are PDF, DOCX, TXT, and Markdown.",
                type: "warning",
            });
            return;
        }

        setFile(selectedFile);
    };

    const triggerFileInput = () => {
        fileInputRef.current?.click();
    };

    const removeFile = () => {
        setFile(null);
        setUploadProgress(0);
    };

    const handleUpload = () => {
        if (file) {
            uploadMutation.mutate(file);
        }
    };

    const formatBytes = (bytes: number): string => {
        if (bytes === 0) return "0 Bytes";
        const k = 1024;
        const sizes = ["Bytes", "KB", "MB"];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    };

    return (
        <Card className="border border-border/80 bg-card/40 shadow-xl backdrop-blur-xl">
            <CardHeader>
                <CardTitle className="text-xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
                    <UploadCloud className="h-5 w-5 text-primary" />
                    Document Ingestion
                </CardTitle>
                <CardDescription className="text-muted-foreground text-xs leading-relaxed">
                    Upload documents to feed the RAG search indexes. Supported files: PDF, DOCX, TXT, MD (max 20MB).
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                
                {/* Drag Box */}
                {!file ? (
                    <div
                        onDragEnter={handleDrag}
                        onDragOver={handleDrag}
                        onDragLeave={handleDrag}
                        onDrop={handleDrop}
                        onClick={triggerFileInput}
                        className={`group relative flex min-h-[220px] cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-all ${
                            dragActive
                                ? "border-primary bg-primary/5"
                                : "border-border/80 bg-background/30 hover:border-primary/50 hover:bg-background/50"
                        }`}
                    >
                        <input
                            ref={fileInputRef}
                            type="file"
                            onChange={handleFileChange}
                            accept=".pdf,.docx,.txt,.md"
                            className="hidden"
                        />
                        <div className="rounded-full bg-muted/60 p-3.5 transition-colors group-hover:bg-primary/10">
                            <UploadCloud className="h-6 w-6 text-muted-foreground transition-colors group-hover:text-primary" />
                        </div>
                        <p className="mt-4 text-sm font-semibold text-foreground">
                            Drag & drop file here
                        </p>
                        <p className="mt-1 text-xs text-muted-foreground">
                            or click to browse local files
                        </p>
                    </div>
                ) : (
                    /* Selected File Display card */
                    <div className="flex items-center justify-between rounded-xl border border-border/80 bg-background/50 p-4">
                        <div className="flex items-center gap-3 min-w-0">
                            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                                <FileText className="h-6 w-6" />
                            </div>
                            <div className="min-w-0">
                                <p className="truncate text-sm font-semibold text-foreground">{file.name}</p>
                                <p className="text-[10px] text-muted-foreground">{formatBytes(file.size)}</p>
                            </div>
                        </div>
                        <button
                            onClick={removeFile}
                            disabled={uploadMutation.isPending}
                            className="rounded-lg border border-border p-1.5 text-muted-foreground hover:bg-destructive hover:text-destructive-foreground disabled:opacity-50"
                            aria-label="Remove File"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    </div>
                )}

                {/* Progress bar tracker */}
                {uploadMutation.isPending && (
                    <div className="space-y-1.5 pt-2">
                        <div className="flex justify-between text-xs font-semibold text-foreground">
                            <span>Ingesting files...</span>
                            <span className="tabular-nums">{uploadProgress}%</span>
                        </div>
                        <Progress value={uploadProgress} className="h-1.5" />
                    </div>
                )}

                {/* Confirm upload action button */}
                {file && (
                    <Button
                        onClick={handleUpload}
                        disabled={uploadMutation.isPending}
                        className="w-full h-12 font-bold tracking-wide transition-all bg-primary text-primary-foreground hover:bg-primary/95"
                    >
                        {uploadMutation.isPending ? "Parsing & Indexing..." : "Ingest Document"}
                    </Button>
                )}
            </CardContent>
        </Card>
    );
}
