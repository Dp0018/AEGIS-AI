# Code Standards & Quality Guidelines

All source code files in the AegisAI workspace must strictly conform to the following standards.

## General Policies

1. **Size Constraint**: No single source code file should exceed 300 lines of code. Split complex modules into focused helper functions or separate classes.
2. **Feature Increments**: Implement changes file-by-file. Verify each change is functional before starting the next.
3. **No Mocking**: Connect real databases, caches, and APIs. Mocking should be used only for external integrations (such as email servers or CRM APIs).

---

## Backend Standards (Python/FastAPI)

* **Asynchronous Programming**: Endpoints, database transactions, and cache operations must use modern `async` and `await` syntax.
* **SQLAlchemy 2.0 Syntax**: Ensure all queries are written using SQLAlchemy 2.0 standards (e.g. `select(...)`). Avoid obsolete 1.x syntax.
* **Typing Type Hints**: Explicitly type all function signatures, parameters, and return types.
* **Validation**: Always use Pydantic models for request bodies and response serializations.
* **Dependency Injection**: Leverage FastAPI's `Depends` for databases, cache connections, and authentication checks.
* **Error Handling**: Never return raw stack traces or exceptions. Wrap all errors in the standard `ErrorResponse` layout.

---

## Frontend Standards (TypeScript/Next.js)

* **Next.js App Router**: Build pages, layouts, and server endpoints under the modern `src/app` routing model.
* **TypeScript Typing**: Avoid using the `any` keyword. Define strict interfaces or types for all components, payloads, and states.
* **Styling**: Style UI elements exclusively with Tailwind CSS. Maintain consistent spacing, sizing, and theme colors.
* **Data Fetching**: Use TanStack Query (`@tanstack/react-query`) for fetching, caching, and updating server-side data.
* **Forms & Validation**: Pair `react-hook-form` with `zod` schema definitions to validate client input parameters.
