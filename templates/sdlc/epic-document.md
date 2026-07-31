# Epic: [E001] [Epic Title]

**Priority:** Critical | High | Medium | Low
**Status:** Draft | Planning | In Progress | Complete
**Owner:** [Name]
**Blocking:** [Yes — list what it blocks] | No
**Target Sprint:** [Sprint X – Sprint Y]
**Time Estimate:** [X hours total] (Dev: X | Test: X | Review: X)

---

## Description

<!-- What does this epic deliver? Why does it matter? Who benefits? -->

## Dependencies

| Depends On | Type | Status |
|-----------|------|--------|
| [E000 - Repository Foundation] | Must complete first | <!-- Done / In Progress / Not Started --> |
| [External: API availability] | External blocker | <!-- Available / Pending / Blocked --> |

## Related Architecture Documents

- [Use Case Diagram](<!-- path -->)
- [Data Flow Diagram](<!-- path -->)
- [ERD](<!-- path -->)
- [Cloud Architecture](<!-- path -->)

## Wireframes / UI Specs

- [Figma: Feature Name](<!-- link -->)
- [Loveable: Prototype](<!-- link -->)

---

## Stories

### [E001-S001] [Story Title]

**Assignee:** [Name] | **Sprint:** [Sprint X] | **Estimate:** [X hours]

**Description:** <!-- What the user can do after this story ships -->

**Related Docs:**
- [Architecture: use-case-xxx.md](<!-- path -->)
- [Data Flow: df-xxx.md](<!-- path -->)

**Wireframe:** [Link](<!-- url -->)

#### Acceptance Criteria

- [ ] GIVEN [context] WHEN [action] THEN [result]
- [ ] GIVEN [context] WHEN [error] THEN [error handling]
- [ ] Idempotent: safe to retry without duplication
- [ ] PII: [fields] encrypted at rest and in transit
- [ ] Performance: p95 < [X]ms at [Y] rps
- [ ] Storybook: [component] story created/updated
- [ ] Performance test: [endpoint] load tested

#### Risks

- <!-- Risk 1 -->
- <!-- Risk 2 -->

#### Subtasks

| ID | Type | Title | Depends On | Estimate | Assignee |
|----|------|-------|-----------|----------|----------|
| E001-S001-T001 | task | [description] | — | [X]h dev + [X]h test + [X]h review | [name] |
| E001-S001-T002 | task | [description] | T001 | [X]h dev + [X]h test + [X]h review | [name] |
| E001-S001-T003 | task | [description] | T001 | [X]h dev + [X]h test + [X]h review | [name] |

---

### [E001-S002] [Story Title]

**Assignee:** [Name] | **Sprint:** [Sprint X] | **Estimate:** [X hours]

<!-- Repeat story format -->

---

## Task Detail: [E001-S001-T001] [Task Title]

**Type:** task | bug | proto
**Assignee:** [Name]
**Depends On:** [None | task IDs]
**Estimate:** Dev [X]h | Test [X]h | Review [X]h

### Scope

**Files affected:** <!-- specific paths: src/features/x/api.ts, src/features/x/schema.ts -->

**Inputs:** <!-- What data/state this task receives -->

**Outputs:** <!-- What data/state this task produces -->

### Acceptance Criteria

- [ ] <!-- Specific testable criterion -->
- [ ] <!-- Unit test covers: [scenarios] -->
- [ ] <!-- Error handling: [strategy] -->
- [ ] <!-- Shared state: [mechanism] -->
- [ ] <!-- Idempotent: [yes/no and how] -->

### Test Plan

**Unit Tests:**

| Scenario | Input | Expected Output |
|----------|-------|----------------|
| Happy path | <!-- input --> | <!-- output --> |
| Invalid input | <!-- input --> | <!-- validation error --> |
| Edge case | <!-- input --> | <!-- handled gracefully --> |

**Integration Tests:**

| Scenario | Input | Expected Output |
|----------|-------|----------------|
| Full flow | <!-- request --> | <!-- response --> |

**Performance Tests:** (if applicable)

| Metric | Target | Method |
|--------|--------|--------|
| p95 latency | <!-- ms --> | <!-- tool and approach --> |
| Throughput | <!-- rps --> | <!-- tool and approach --> |

### API Examples (if applicable)

**Request:**
```http
POST /api/v1/[resource] HTTP/1.1
Authorization: Bearer <token>
Content-Type: application/json

{
  "field": "value"
}
```

**Response (Success):**
```http
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "uuid",
  "field": "value",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

**Response (Error):**
```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "field is required",
    "details": [{"field": "field", "message": "must not be empty"}]
  }
}
```

### Notes

<!-- Implementation hints, edge cases, links to architecture docs, known gotchas -->

---

## Summary

| Metric | Value |
|--------|-------|
| Total Stories | <!-- count --> |
| Total Tasks | <!-- count --> |
| Total Estimate | <!-- hours --> |
| Critical Path Length | <!-- sprints --> |
| Risk Items | <!-- count --> |
| Dependencies (external) | <!-- count --> |
