"use client";

import React from "react";
import { DocumentUpload } from "@/features/documents/components/DocumentUpload";
import { DocumentList } from "@/features/documents/components/DocumentList";

export default function DocumentsPage() {
    return (
        <div className="space-y-8 animate-fade-in">
            {/* Page Header */}
            <div>
                <h1 className="text-3xl font-extrabold tracking-tight text-foreground">
                    Knowledge Base Ingestion
                </h1>
                <p className="text-sm text-muted-foreground mt-1 leading-relaxed">
                    Upload documents to split, parse, embed, and store into the Pinecone vector database index.
                </p>
            </div>

            {/* Split Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                <div className="lg:col-span-5">
                    <DocumentUpload />
                </div>
                <div className="lg:col-span-7">
                    <DocumentList />
                </div>
            </div>
        </div>
    );
}
