# UI Components Registry

This file cataloges the reusable client components, panels, and layouts for AegisAI.

## Primary Layouts & Dashboards

### 1. DashboardLayout
- **Location**: `frontend/src/components/layout/DashboardLayout.tsx`
- **Purpose**: Unified layout hosting the sidebar, collapsible panel toggles, and user profile settings.
- **Interactions**: Left-aligned sticky sidebar containing notifications and quick-link views.

### 2. InboxFeed
- **Location**: `frontend/src/components/inbox/InboxFeed.tsx`
- **Purpose**: Displays a list of active support threads, emails, and tickets.
- **Indicators**: Pulses to show running agents, human-in-the-loop validation requests, and ticket priority levels.

### 3. ReasoningTimeline
- **Location**: `frontend/src/components/timeline/ReasoningTimeline.tsx`
- **Purpose**: Renders the step-by-step reasoning steps of the LangGraph execution flow.
- **Details**: Exposes which nodes were executed (Coordinator, Research, Response, Escalation), what tools were run (e.g. database lookups, vector retrievals), token details, and latency.

### 4. ActionsPanel
- **Location**: `frontend/src/components/actions/ActionsPanel.tsx`
- **Purpose**: Operator controls for tickets flagged for human approval.
- **Controls**: `Approve Response`, `Edit Draft Response`, `Reject & Rerun`, `Manual Escalate`.

### 5. DocumentSidebar
- **Location**: `frontend/src/components/docs/DocumentSidebar.tsx`
- **Purpose**: Renders retrieved document text segments and similarity scores.
