"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Logo } from "@/components/Logo";
import { 
    MessageSquare, 
    FileText, 
    BarChart3, 
    LogOut, 
    Menu, 
    X,
    Activity,
    Cpu,
    Users
} from "lucide-react";

export function DashboardLayout({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const { user, logout } = useAuth();
    const [isMobileOpen, setIsMobileOpen] = useState(false);

    const baseNavigation = [
        { name: "Chat Console", href: "/dashboard/chat", icon: MessageSquare },
        { name: "Documents Ingestion", href: "/dashboard/documents", icon: FileText },
        { name: "Retrieval Analytics", href: "/dashboard/analytics", icon: BarChart3 },
        { name: "System Observability", href: "http://localhost:3100", icon: Activity, external: true },
    ];

    const navigation = user?.role === "admin"
        ? [...baseNavigation, { name: "Team Management", href: "/dashboard/users", icon: Users }]
        : baseNavigation;

    const getActivePageName = () => {
        const activeItem = navigation.find(item => !item.external && pathname.startsWith(item.href));
        return activeItem ? activeItem.name : "Operations Control";
    };

    return (
        <div className="relative flex h-screen w-full overflow-hidden bg-background px-4 py-4 font-sans text-foreground antialiased transition-colors duration-200">
            
            {/* Dynamic Background Grid Pattern underneath floating cards */}
            <div 
                className="absolute inset-0 opacity-[0.12] dark:opacity-[0.18]"
                style={{
                    backgroundImage: `linear-gradient(to right, var(--border) 1px, transparent 1px), linear-gradient(to bottom, var(--border) 1px, transparent 1px)`,
                    backgroundSize: "4rem 4rem",
                    maskImage: "radial-gradient(ellipse 60% 50% at 50% 50%, #000 60%, transparent 100%)",
                    WebkitMaskImage: "radial-gradient(ellipse 60% 50% at 50% 50%, #000 60%, transparent 100%)",
                }}
            />

            {/* Glowing blur mesh effect behind main viewport */}
            <div className="absolute top-1/3 right-1/4 h-[350px] w-[350px] rounded-full bg-primary/5 blur-[90px] dark:bg-primary/10" />

            {/* 1. Desktop Floating Sidebar (Hidden on Mobile) */}
            <aside className="relative z-20 hidden w-64 shrink-0 flex-col rounded-2xl border border-border/80 bg-card/60 shadow-xl backdrop-blur-xl transition-all duration-300 md:flex">
                {/* Brand Header */}
                <div className="flex h-16 items-center gap-3 border-b border-border/40 px-6">
                    <Logo className="h-9 w-9 shrink-0" />
                    <div className="flex flex-col">
                        <span className="text-sm font-extrabold tracking-tight text-foreground leading-tight">Aether Control</span>
                        <span className="text-[9px] uppercase font-bold tracking-wider text-primary/80">Operations Console</span>
                    </div>
                </div>

                {/* Sidebar Navigation */}
                <nav className="flex-1 space-y-2 px-4 py-6">
                    {navigation.map((item) => {
                        if (item.external) {
                            return (
                                <a
                                    key={item.name}
                                    href={item.href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-muted-foreground hover:bg-accent/60 hover:text-foreground transition-all"
                                >
                                    <item.icon className="h-4.5 w-4.5 shrink-0" />
                                    {item.name}
                                </a>
                            );
                        }
                        const isActive = pathname.startsWith(item.href);
                        return (
                            <Link
                                key={item.name}
                                href={item.href}
                                className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition-all ${
                                    isActive
                                        ? "bg-primary text-primary-foreground shadow-lg shadow-primary/10"
                                        : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                                }`}
                            >
                                <item.icon className="h-4.5 w-4.5 shrink-0" />
                                {item.name}
                            </Link>
                        );
                    })}
                </nav>

                {/* Bottom Control deck */}
                <div className="border-t border-border/40 p-4 space-y-4">
                    {/* User profile card details */}
                    {user && (
                        <div className="flex items-center gap-3 rounded-xl bg-background/40 border border-border/40 p-3 backdrop-blur-md">
                            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary font-bold">
                                {user.full_name.charAt(0).toUpperCase()}
                            </div>
                            <div className="min-w-0 flex-1">
                                <p className="truncate text-xs font-bold text-foreground">{user.full_name}</p>
                                <p className="truncate text-[10px] text-muted-foreground capitalize">{user.role}</p>
                            </div>
                        </div>
                    )}

                    {/* Capsule theme toggle and logout */}
                    <div className="flex items-center justify-between gap-2">
                        <ThemeToggle />
                        <button
                            onClick={() => logout()}
                            className="flex h-9 items-center justify-center gap-2 rounded-full border border-border bg-muted/40 px-4 text-xs font-bold text-foreground transition-all hover:bg-destructive hover:text-destructive-foreground active:scale-95"
                        >
                            <LogOut className="h-3.5 w-3.5" />
                            Log Out
                        </button>
                    </div>
                </div>
            </aside>

            {/* 2. Floating Main Page Container */}
            <div className="relative z-10 flex flex-1 flex-col overflow-hidden rounded-2xl border border-border/80 bg-card/15 shadow-2xl backdrop-blur-md ml-0 md:ml-4">
                
                {/* Embedded Navbar Header */}
                <header className="flex h-16 shrink-0 items-center justify-between border-b border-border/40 bg-card/30 px-6 backdrop-blur-md">
                    {/* Mobile Hamburger menu */}
                    <button
                        onClick={() => setIsMobileOpen(true)}
                        className="rounded-xl border border-border p-2 text-muted-foreground hover:bg-accent/60 hover:text-foreground md:hidden"
                        aria-label="Open Sidebar"
                    >
                        <Menu className="h-5 w-5" />
                    </button>
                    
                    {/* Dynamic Breadcrumbs */}
                    <div className="hidden items-center gap-2 text-sm font-semibold md:flex">
                        <span className="text-muted-foreground">Console</span>
                        <span className="text-muted-foreground/60">/</span>
                        <span className="text-foreground">{getActivePageName()}</span>
                    </div>

                    {/* Cloud System telemetry metrics */}
                    <div className="flex items-center gap-4">
                        <div className="hidden items-center gap-1.5 rounded-lg border border-border/40 bg-background/30 px-2.5 py-1 font-mono text-[10px] text-muted-foreground md:flex">
                            <Activity className="h-3.5 w-3.5 text-emerald-500 animate-pulse" />
                            <span>LATENCY: <strong className="text-foreground">14ms</strong></span>
                        </div>
                        <div className="flex items-center gap-1.5 rounded-lg border border-border/40 bg-background/30 px-2.5 py-1 font-mono text-[10px] text-muted-foreground">
                            <Cpu className="h-3.5 w-3.5 text-primary" />
                            <span>COORDINATOR: <strong className="text-primary font-bold uppercase">Active</strong></span>
                        </div>
                    </div>
                </header>

                {/* Main scrollable view inside the glass container */}
                <main className="flex-1 overflow-y-auto">
                    <div className="p-6 md:p-8">
                        {children}
                    </div>
                </main>
            </div>

            {/* 3. Mobile Sidebar Drawer Overlay */}
            {isMobileOpen && (
                <div className="fixed inset-0 z-50 flex md:hidden">
                    {/* Backdrop */}
                    <div 
                        className="fixed inset-0 bg-background/80 backdrop-blur-sm" 
                        onClick={() => setIsMobileOpen(false)}
                    />
                    
                    {/* Drawer Content */}
                    <aside className="relative flex w-64 max-w-xs flex-col bg-card border-r border-border p-6 shadow-xl animate-fade-in-left">
                        {/* Close button */}
                        <button
                            onClick={() => setIsMobileOpen(false)}
                            className="absolute top-4 right-4 rounded-xl border border-border p-1.5 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                            aria-label="Close Sidebar"
                        >
                            <X className="h-4 w-4" />
                        </button>

                        <div className="flex items-center gap-3 mb-8">
                            <Logo className="h-9 w-9 shrink-0" />
                            <div className="flex flex-col">
                                <span className="text-sm font-extrabold tracking-tight text-foreground leading-tight">Aether Control</span>
                                <span className="text-[9px] uppercase font-bold tracking-wider text-primary/80">Operations</span>
                            </div>
                        </div>

                        <nav className="flex-1 space-y-2">
                            {navigation.map((item) => {
                                if (item.external) {
                                    return (
                                        <a
                                            key={item.name}
                                            href={item.href}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            onClick={() => setIsMobileOpen(false)}
                                            className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold text-muted-foreground hover:bg-accent/60 hover:text-foreground transition-all"
                                        >
                                            <item.icon className="h-4.5 w-4.5 shrink-0" />
                                            {item.name}
                                        </a>
                                    );
                                }
                                const isActive = pathname.startsWith(item.href);
                                return (
                                    <Link
                                        key={item.name}
                                        href={item.href}
                                        onClick={() => setIsMobileOpen(false)}
                                        className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition-all ${
                                            isActive
                                                ? "bg-primary text-primary-foreground"
                                                : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
                                        }`}
                                    >
                                        <item.icon className="h-4.5 w-4.5 shrink-0" />
                                        {item.name}
                                    </Link>
                                );
                            })}
                        </nav>

                        <div className="border-t border-border pt-4 mt-auto space-y-4">
                            {user && (
                                <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3">
                                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary font-bold">
                                        {user.full_name.charAt(0).toUpperCase()}
                                    </div>
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate text-xs font-bold text-foreground">{user.full_name}</p>
                                        <p className="truncate text-[10px] text-muted-foreground capitalize">{user.role}</p>
                                    </div>
                                </div>
                            )}
                            <div className="flex items-center justify-between gap-2">
                                <ThemeToggle />
                                <button
                                    onClick={() => logout()}
                                    className="flex h-9 items-center justify-center gap-2 rounded-full border border-border bg-muted px-4 text-xs font-bold text-foreground transition-all hover:bg-destructive hover:text-destructive-foreground active:scale-95"
                                >
                                    <LogOut className="h-3.5 w-3.5" />
                                    Log Out
                                </button>
                            </div>
                        </div>
                    </aside>
                </div>
            )}
        </div>
    );
}
