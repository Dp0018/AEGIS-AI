"use client";

import React, { useState } from "react";
import { ThreadList } from "@/features/chat/components/ThreadList";
import { ChatWindow } from "@/features/chat/components/ChatWindow";
import { ReasoningTraces } from "@/features/chat/components/ReasoningTraces";

export default function ChatPage() {
    const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);

    const handleStartNew = () => {
        const newId = crypto.randomUUID();
        setSelectedThreadId(newId);
    };

    return (
        <div className="relative flex flex-col md:grid md:grid-cols-12 gap-0 border border-border/80 rounded-2xl overflow-hidden bg-card/20 backdrop-blur-xl h-[calc(100vh-10rem)] shadow-2xl animate-fade-in">
            {/* Thread Sidebar (3 columns) */}
            <div className="md:col-span-3 h-full overflow-hidden">
                <ThreadList 
                    selectedId={selectedThreadId} 
                    onSelect={setSelectedThreadId} 
                    onStartNew={handleStartNew} 
                />
            </div>

            {/* Chat Conversation Window (6 columns) */}
            <div className="md:col-span-6 h-full flex flex-col overflow-hidden border-r border-border/40">
                <ChatWindow threadId={selectedThreadId} />
            </div>

            {/* Telemetry Reasoning Traces (3 columns) */}
            <div className="md:col-span-3 h-full overflow-hidden">
                <ReasoningTraces threadId={selectedThreadId} />
            </div>
        </div>
    );
}
