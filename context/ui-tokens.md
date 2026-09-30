# UI Design System: Design Tokens

This file specifies colors, fonts, spacing, and styling tokens for the AegisAI client.

## Color System (Dark-Mode Primary Palette)

Our theme is dark-mode first, inspired by Vercel, Linear, and Stripe dashboards.

| CSS Variable | Tailwind Utility | HSL / Hex Code | Description |
|---|---|---|---|
| `--background` | `bg-background` | `hsl(240, 10%, 3.9%)` | Dark slate background |
| `--foreground` | `text-foreground` | `hsl(0, 0%, 98%)` | Pure white primary text |
| `--card` | `bg-card` | `hsl(240, 10%, 5.9%)` | Dark card background |
| `--border` | `border-border` | `hsl(240, 5.9%, 15%)` | Sleek border highlights |
| `--primary` | `bg-primary` / `text-primary` | `hsl(263.4, 70%, 50.4%)` | Accent Indigo |
| `--muted` | `text-muted` | `hsl(240, 5%, 64.9%)` | Muted descriptions |
| `--success` | `text-success` | `hsl(142.1, 76.2%, 36.3%)` | Action successes |
| `--destructive`| `text-destructive` | `hsl(0, 72.2%, 50.6%)` | Warning indicators |

---

## Typography

* **Sans Font Family**: Inter, Roboto, Outfit, sans-serif
* **Mono Font Family**: JetBrains Mono, Fira Code, monospace
* **Sizes**:
  * Heading 1 (`h1`): `text-3xl font-extrabold tracking-tight`
  * Heading 2 (`h2`): `text-xl font-semibold tracking-tight`
  * Body (`p`): `text-sm font-normal text-muted-foreground`
  * Code (`code`): `text-xs font-mono bg-muted p-1 rounded`

---

## Elevation & Transparency
* **Glassmorphic panels**: `bg-background/80 backdrop-blur-md`
* **Gradients**: Subtle radial gradients for backdrops and hover states.
