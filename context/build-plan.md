# Project Build Plan

This plan organizes the implementation of the AegisAI platform into progressive, testable development phases.

## Build Phases

### Phase 1: Identity & Access Management (IAM)
- Set up Database schemas (`users`, `audit_logs`).
- Build password hashing and JWT utility engines.
- Write FastAPI routes for `/auth/register` (Admin Bootstrapping), `/auth/token`, `/auth/refresh`, and `/auth/logout`.
- Implement RBAC authorization checkers (`Admin`, `Operator`, `Viewer`).
- Connect Redis token blacklist revocation middleware.

### Phase 2: Document Ingestion & Processing Pipeline
- Establish Document upload API endpoints.
- Parse text contents from PDF, DOCX, and Markdown formats.
- Integrate langchain document splitters for semantic chunking.
- Add ChromaDB vector store collection mappings.

### Phase 3: RAG Retrieval Service
- Build embedding creation wrappers (`text-embedding-3-large`).
- Implement context retrieve routers executing cosine similarity lookups.
- Setup prompt templates for grounded answers.

### Phase 4: LangGraph Agent Core
- Define StateGraph workflow structures.
- Implement nodes:
  - **Coordinator**: Decides workflows.
  - **Research**: Queries ChromaDB vector contexts.
  - **Response**: Prepares email drafts.
  - **Escalation**: Flags critical tickets.
- Configure state transitions and interrupt hooks for HITL checks.

### Phase 5: Action Tools Integration
- Add execution tool libraries:
  - Vector search lookup.
  - Database customer details queries.
  - Ticketing service integrations.
  - SMTP/Email send simulators.

### Phase 6: Thread and Memory Layer
- Implement `threads`, `messages`, `actions`, and `memory` database schemas.
- Set up thread context builders to track conversation history.
- Write memory Summarizers to extract long-term user logs.

### Phase 7: Next.js Frontend Console
- Connect TanStack Query state managers.
- Design responsive dashboards: Live Inbox, Reasoning Timeline, retrieved documents sidebar, and HITL action controls.

### Phase 8: Event Streaming & Real-Time Sync (Kafka & WebSockets)
- Configure Zookeeper and Apache Kafka services in docker-compose.
- Set up ticket event and audit log Kafka producers/consumers on backend.
- Replace HTTP polling in Chat Console/Telemetry with native WebSocket connections.

### Phase 9: Observability & Monitoring
- Add Prometheus exporter middleware to FastAPI.
- Configure Grafana dashboards to track latency, token usage, and agent execution times.
- Integrate OpenTelemetry for distributed trace observability.

### Phase 10: Cloud Deployment & Orchestration (Docker & Kubernetes)
- Package Frontend and Backend containers in Dockerfiles.
- Build multi-container orchestration in docker-compose.
- Write Kubernetes manifests (Deployments, Services, Ingress, HPA, ConfigMaps, Secrets) for AWS EKS cloud deployment.

