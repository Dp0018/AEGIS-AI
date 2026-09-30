import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
    return (
        <div className="relative flex min-h-screen w-full flex-col bg-background text-foreground transition-colors duration-200 md:flex-row">
            
            {/* Left Panel: Aesthetic Interactive Visual Deck (Hidden on Mobile) */}
            <div className="relative hidden flex-1 flex-col justify-between overflow-hidden border-r border-border/40 bg-zinc-950 p-12 text-white dark:bg-black md:flex">
                {/* Background Grid Pattern */}
                <div 
                    className="absolute inset-0 opacity-15"
                    style={{
                        backgroundImage: `linear-gradient(to right, var(--border) 1px, transparent 1px), linear-gradient(to bottom, var(--border) 1px, transparent 1px)`,
                        backgroundSize: "3rem 3rem",
                    }}
                />
                
                {/* Glowing Core Sphere */}
                <div className="absolute top-1/2 left-1/2 h-[450px] w-[450px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/10 blur-[120px] animate-pulse" />
                
                {/* Top Brand Block */}
                <div className="relative z-10 flex items-center gap-3">
                    <Logo className="h-11 w-11 shrink-0" />
                    <span className="text-xl font-bold tracking-tight">Aether Control</span>
                </div>

                {/* Animated Interactive Core Graphics */}
                <div className="relative z-10 my-auto flex flex-col items-center justify-center text-center">
                    {/* Security Shield Ring Animation */}
                    <div className="relative flex h-52 w-52 items-center justify-center">
                        <div className="absolute inset-0 animate-spin rounded-full border-2 border-dashed border-primary/20 [animation-duration:20s]" />
                        <div className="absolute h-40 w-40 animate-spin rounded-full border border-dotted border-primary/40 [animation-duration:12s] [animation-direction:reverse]" />
                        <div className="absolute h-28 w-28 rounded-full bg-gradient-to-tr from-primary to-primary/40 opacity-15 blur-lg" />
                        
                        <svg className="relative h-20 w-20 text-primary drop-shadow-[0_0_15px_rgba(0,100,255,0.3)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.57-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                        </svg>
                    </div>
                    
                    <h2 className="mt-8 text-3xl font-extrabold tracking-tight">Securing Agent Workflows</h2>
                    <p className="mt-3 max-w-sm text-zinc-400 text-sm leading-relaxed">
                        Real-time verification and control desk for human-in-the-loop coordinator execution nodes.
                    </p>
                </div>

                {/* Simulated Live System Logs console */}
                <div className="relative z-10 rounded-xl border border-white/5 bg-white/5 p-4 font-mono text-xs text-zinc-400 backdrop-blur-md">
                    <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-2">
                        <span className="text-[10px] uppercase font-bold text-primary tracking-wider">Console Terminal</span>
                        <div className="flex gap-1.5">
                            <span className="h-2.5 w-2.5 rounded-full bg-red-500/50" />
                            <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/50" />
                            <span className="h-2.5 w-2.5 rounded-full bg-green-500/50" />
                        </div>
                    </div>
                    <div className="space-y-1 text-left">
                        <p className="text-zinc-500">[17:52:01] DB checks: Postgres & Redis online...</p>
                        <p className="text-emerald-400/80">&gt; Connection pool verified [OK]</p>
                        <p className="text-zinc-500">[17:52:03] Initializing Vector Store adaptors...</p>
                        <p className="text-sky-400/80">&gt; Pinecone local mock indexes ready [HEALTHY]</p>
                        <p className="text-primary animate-pulse">&gt; Waiting for operator console credentials...</p>
                    </div>
                </div>
            </div>

            {/* Right Panel: Clean Control Desk Auth Forms */}
            <div className="relative flex flex-1 flex-col items-center justify-center p-8 transition-colors duration-200">
                {/* Dynamic Background Grid (Only visible on right pane) */}
                <div 
                    className="absolute inset-0 opacity-[0.12] dark:opacity-[0.18]"
                    style={{
                        backgroundImage: `linear-gradient(to right, var(--border) 1px, transparent 1px), linear-gradient(to bottom, var(--border) 1px, transparent 1px)`,
                        backgroundSize: "4rem 4rem",
                        maskImage: "radial-gradient(ellipse 60% 50% at 50% 50%, #000 60%, transparent 100%)",
                        WebkitMaskImage: "radial-gradient(ellipse 60% 50% at 50% 50%, #000 60%, transparent 100%)",
                    }}
                />

                {/* Theme Toggle Positioned Top-Right */}
                <div className="absolute top-6 right-6 z-20">
                    <ThemeToggle />
                </div>

                <div className="z-10 flex w-full justify-center">
                    {children}
                </div>
            </div>

        </div>
    );
}
