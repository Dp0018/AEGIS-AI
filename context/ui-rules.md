# UI Design Rules & Interaction Principles

Our goal is a premium, developer-focused, dark-mode first design that feels responsive and responsive.

## Principles

### 1. Dark Mode First
- All pages must have dark backgrounds (`bg-background`).
- Avoid stark black backgrounds unless mapping panel borders. Use deep slate values (`#09090b` or `#0e0e11`) to prevent eye fatigue.

### 2. Glassmorphism & Translucency
- Modals, popovers, headers, and sidebars should use transparency:
  `bg-card/85 backdrop-blur-md border border-border`
- Headers must remain sticky, blurring background details as content scrolls.

### 3. Dynamic Micro-Animations
- Implement transitions on all interactive components:
  `transition-all duration-200 ease-in-out`
- Hover states for buttons, navigation links, and list rows should feel fast and fluid.

### 4. Resizable Multi-Panel Layouts
- The main control dashboard uses split-screen interfaces:
  - Left panel: Inbox tickets.
  - Middle panel: active ticket and timeline reasoning steps.
  - Right panel: context documents and memory stats.
- Keep panels resizable and collapsible to make dashboard layouts customizable.

### 5. Live State Indicators
- Running agents should display pulsing neon rings (e.g. green pulse for running, purple pulse for coordinating, orange for human approval).
- Error messages must be displayed inline inside standard error cards with red icons.
