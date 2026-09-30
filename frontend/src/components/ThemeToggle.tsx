"use client";

import React from "react";
import { useTheme } from "./ThemeProvider";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle() {
    const { theme, toggleTheme } = useTheme();

    return (
        <button
            onClick={toggleTheme}
            className="relative flex h-9 w-[76px] items-center justify-between rounded-full bg-muted/80 p-1 border border-border/80 cursor-pointer select-none transition-colors focus:outline-none"
            aria-label="Toggle Theme"
        >
            {/* Sliding background indicator pill */}
            <div
                className={`absolute h-7 w-7 rounded-full bg-card shadow-sm border border-border/40 transition-all duration-300 ${
                    theme === "dark" 
                        ? "translate-x-[36px]" 
                        : "translate-x-0"
                }`}
            />
            
            {/* Sun Icon (Left) */}
            <div className={`relative z-10 flex h-7 w-7 items-center justify-center transition-colors duration-300 ${
                theme === "light" 
                    ? "text-primary" 
                    : "text-muted-foreground hover:text-foreground"
            }`}>
                <Sun className="h-[1.05rem] w-[1.05rem]" />
            </div>

            {/* Moon Icon (Right) */}
            <div className={`relative z-10 flex h-7 w-7 items-center justify-center transition-colors duration-300 ${
                theme === "dark" 
                    ? "text-primary" 
                    : "text-muted-foreground hover:text-foreground"
            }`}>
                <Moon className="h-[1.05rem] w-[1.05rem]" />
            </div>
        </button>
    );
}
