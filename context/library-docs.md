# Core Library Documentation Hooks

Reference templates and configuration details for critical system packages.

## SQLAlchemy 2.0 (Async Syntax)

Always use SQLAlchemy 2.0's type-mapped properties and async session lookups.

### Model Mapping Template
```python
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class Entity(Base):
    __tablename__ = "entities"
    name: Mapped[str] = mapped_column(nullable=False)
```

### Async Query Template
```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def get_entities(db: AsyncSession):
    query = select(Entity).order_by(Entity.name)
    result = await db.execute(query)
    return result.scalars().all()
```

---

## FastAPI (Lifespan & Dependency Injection)

Use FastAPI lifespan hooks for setup/teardown and dependencies for security/DB connection.

### Lifespan Hook
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    yield
    # Shutdown actions
```

### Dependency Injection Hook
```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db_session

@router.get("/")
async def list_items(db: AsyncSession = Depends(get_db_session)):
    ...
```

---

## LangGraph (Workflow StateGraph)

Create standard LangGraph StateGraphs containing state properties, nodes, and edges.

### State & Node Hook
```python
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class AgentState(TypedDict):
    input: str
    context: list
    response: str

def coordinator_node(state: AgentState):
    return {"response": "draft"}

# Initialize Graph
workflow = StateGraph(AgentState)
workflow.add_node("coordinator", coordinator_node)
workflow.set_entry_point("coordinator")
workflow.add_edge("coordinator", END)
app = workflow.compile()
```
