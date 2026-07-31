# Pipeline Contract

## Why This Exists

Orchestrators delegate work to specialized sub-agents running on different models optimized for their task type. Without a standardized communication format, sub-agents produce inconsistent output that the orchestrator can't reliably parse, chain, or retry. This contract defines the exact JSON schema every sub-agent receives as input and must produce as output — regardless of domain.

---

## Pipeline Input Schema

Every sub-agent receives this structure as its task context from the orchestrator:

```json
{
  "task_type": "<domain-specific-type>",
  "input": {
    "description": "Human-readable description of what needs to be done",
    "target_files": ["paths/to/target/"],
    "constraints": [
      "hard requirement the sub-agent must follow"
    ],
    "upstream_decisions": [
      {
        "from_agent": "<agent-name>",
        "decisions": [
          "decision from earlier pipeline stage that constrains this work"
        ]
      }
    ]
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_type` | string | ✅ | Domain-specific task classification (e.g., `scaffold`, `architecture`, `testing`) |
| `input.description` | string | ✅ | Human-readable description of what needs to be done |
| `input.target_files` | string[] | ❌ | File or directory paths this task targets. Empty for greenfield work. |
| `input.constraints` | string[] | ❌ | Hard requirements the sub-agent must follow |
| `input.upstream_decisions` | object[] | ❌ | Decisions from earlier pipeline stages that constrain this work |
| `input.upstream_decisions[].from_agent` | string | ✅ | Which sub-agent produced these decisions |
| `input.upstream_decisions[].decisions` | string[] | ✅ | List of decisions to follow |

---

## Pipeline Output Schema

Every sub-agent must produce this structure via the `summary` tool's `taskResult` field (as a JSON string):

```json
{
  "task_type": "<domain-specific-type>",
  "output": {
    "status": "success",
    "files_created": [],
    "files_modified": [],
    "decisions_made": [],
    "follow_up_suggestions": [],
    "errors": [],
    "error_count": 0,
    "retry_context": {
      "attempts_made": 1,
      "max_attempts": 3,
      "strategies_tried": [],
      "should_escalate": false
    }
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `output.status` | enum | ✅ | `success` — task completed, `partial` — some work done but not all, `failed` — could not complete |
| `output.files_created` | string[] | ✅ | Paths of new files created (empty array if none) |
| `output.files_modified` | string[] | ✅ | Paths of existing files modified (empty array if none) |
| `output.decisions_made` | string[] | ✅ | Notable implementation decisions for downstream agents or user awareness |
| `output.follow_up_suggestions` | string[] | ❌ | Recommendations for the orchestrator or user about next steps |
| `output.errors` | object[] | ✅ | Array of errors encountered (empty if none) |
| `output.error_count` | number | ✅ | Total count of errors in the errors array |
| `output.retry_context` | object | ✅ | Retry state for orchestrator decision-making |

---

## Error Schema

Each entry in the `errors` array:

```json
{
  "type": "<error_type>",
  "message": "Human-readable error description",
  "file": "path/to/file.ext",
  "line": 24,
  "attempt": 2
}
```

### Standard Error Types

| Type | Description | Typical Source |
|------|-------------|----------------|
| `type_error` | Type system / compilation error | Language compiler or type checker |
| `lint_error` | Linting or formatting issue | Linter (ESLint, pylint, clippy) |
| `test_failure` | Test assertion failed | Test runner |
| `build_error` | Build or bundler error | Build tool |
| `validation_error` | Schema or runtime validation failure | Application logic |
| `runtime_error` | Execution error during verification | Runtime environment |

### Error Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | ✅ | One of the standard types above, or domain-specific extension |
| `message` | string | ✅ | Human-readable error message |
| `file` | string | ❌ | File path where error occurred |
| `line` | number | ❌ | Line number (if available) |
| `attempt` | number | ✅ | Which attempt this error was encountered on (1-indexed) |

---

## Retry Context

```json
{
  "attempts_made": 2,
  "max_attempts": 3,
  "strategies_tried": [
    "description of what was attempted on retry 1",
    "description of what was attempted on retry 2"
  ],
  "should_escalate": false
}
```

### Retry Rules

1. **Max 3 attempts** per sub-agent invocation (configurable per pipeline)
2. **`strategies_tried`** records what was attempted — prevents the orchestrator from re-invoking with the same strategy
3. **`should_escalate`** signals the orchestrator to stop retrying and either:
   - Try a different sub-agent (if the error is outside this agent's domain)
   - Ask the user for guidance (if the error requires human judgment)

### When to Set `should_escalate: true`

- `attempts_made >= max_attempts` — exhausted retries
- Error type is outside the sub-agent's domain (e.g., a test agent finds a source code bug it cannot fix)
- Error requires a design decision the sub-agent cannot make autonomously
- Conflicting constraints that cannot be resolved without human input

---

## Orchestrator Decision Logic

When the orchestrator receives pipeline output from a sub-agent:

```
if output.status == "success":
    → proceed to next pipeline stage (if any)
    → or report success to user

if output.status == "partial":
    → check follow_up_suggestions for what's missing
    → invoke next appropriate sub-agent to complete remaining work

if output.status == "failed":
    if retry_context.should_escalate == true:
        → report to user with error details and strategies_tried
        → ask user how to proceed
    if retry_context.attempts_made < retry_context.max_attempts:
        → re-invoke same sub-agent with hint about what to try differently
        → include previous errors in constraints so agent avoids same approach
    else:
        → escalate to user
```

---

## Pipeline Composition Patterns

### Sequential (DAG)

```
agent-A → agent-B → agent-C
```

Each stage receives the previous stage's `decisions_made` as `upstream_decisions` and `files_created`/`files_modified` as `target_files`.

### Parallel (independent tasks)

```
agent-A ──┐
agent-B ──┼── agent-D (depends on all)
agent-C ──┘
```

Independent stages run concurrently. Downstream stages receive merged `upstream_decisions` from all predecessors.

### Standalone

Single sub-agent invocation for focused tasks that don't require multi-stage processing.

---

## Domain-Specific Extensions

Each orchestration pipeline defines its own:

1. **Sub-agent roster** — which agents exist, their models, and their purpose
2. **Task types** — the valid `task_type` enum values for that domain
3. **Intent classification rules** — how user requests map to task types
4. **Pipeline compositions** — which DAGs apply to which request patterns
5. **Forced routing patterns** — user shortcuts to bypass intent classification

These domain-specific details belong in the orchestrator's prompt or a domain-specific steering doc that references this contract.

---

## Example: React Frontend Pipeline

### Sub-Agent Roster

| Agent | Model | Purpose |
|-------|-------|---------|
| `react-scaffold` | claude-haiku-4.5 | Generate component files, stories, tests, barrel exports |
| `react-architecture` | claude-opus-4.8 | Component decomposition, server/client boundaries, data flow decisions |
| `react-styling` | claude-haiku-4.5 | Tailwind CSS, shadcn/ui composition, responsive design, accessibility |
| `react-testing` | claude-sonnet-5 | Vitest unit tests, Playwright e2e, Storybook stories |
| `react-refactor` | claude-opus-4.7 | Component/hook extraction, state migration, performance optimization |

### Task Types

`scaffold`, `architecture`, `styling`, `testing`, `refactoring`

### Pipeline Compositions

**New Component (full pipeline):**
```
react-architecture → react-scaffold → react-styling → react-testing
```

**Refactoring:**
```
react-refactor → react-testing
```

**Standalone tasks:**
- "Style this component" → `react-styling` alone
- "Write tests for X" → `react-testing` alone
- "Extract this into a hook" → `react-refactor` alone
- "How should I structure this page?" → `react-architecture` alone

### Example Output: Architecture

```json
{
  "task_type": "architecture",
  "output": {
    "status": "success",
    "files_created": [],
    "files_modified": [],
    "decisions_made": [
      "page.tsx is a Server Component — fetches user data with RSC fetch()",
      "UserProfile is a Client Component — needs onClick for edit button",
      "EditProfileModal managed with Zustand useUIStore (cross-component open/close)",
      "user data passed as props from server parent, not re-fetched on client",
      "form inside modal uses react-hook-form + Zod with Server Action on submit"
    ],
    "follow_up_suggestions": [
      "scaffold UserProfile, EditProfileModal, and update-profile server action",
      "add optimistic update via TanStack Query for profile changes"
    ],
    "errors": [],
    "error_count": 0,
    "retry_context": {
      "attempts_made": 1,
      "max_attempts": 3,
      "strategies_tried": [],
      "should_escalate": false
    }
  }
}
```

### Example Output: Testing (with errors and escalation)

```json
{
  "task_type": "testing",
  "output": {
    "status": "partial",
    "files_created": [
      "src/components/user-profile/user-profile.test.tsx"
    ],
    "files_modified": [],
    "decisions_made": [
      "used MSW to mock /api/user endpoint",
      "tested loading, success, and error states"
    ],
    "follow_up_suggestions": [
      "edit button test blocked by source code issue — onClick handler not wired"
    ],
    "errors": [
      {
        "type": "test_failure",
        "message": "expected onClick to have been called, but it was never called",
        "file": "src/components/user-profile/user-profile.test.tsx",
        "line": 45,
        "attempt": 2
      }
    ],
    "error_count": 1,
    "retry_context": {
      "attempts_made": 2,
      "max_attempts": 3,
      "strategies_tried": [
        "verified button renders with correct role",
        "checked if onClick prop is passed through — confirmed source code missing handler"
      ],
      "should_escalate": true
    }
  }
}
```

### Example Output: Refactoring (successful retry)

```json
{
  "task_type": "refactoring",
  "output": {
    "status": "success",
    "files_created": [
      "src/hooks/use-user-profile.ts"
    ],
    "files_modified": [
      "src/components/user-profile/user-profile.tsx",
      "src/components/user-profile/user-profile.test.tsx"
    ],
    "decisions_made": [
      "extracted useUserProfile hook with fetch + mutation logic",
      "component now receives hook return value as props pattern",
      "kept backward compatibility — old direct usage still works"
    ],
    "follow_up_suggestions": [],
    "errors": [],
    "error_count": 0,
    "retry_context": {
      "attempts_made": 2,
      "max_attempts": 3,
      "strategies_tried": [
        "initial extraction broke test — hook returned different shape than component expected"
      ],
      "should_escalate": false
    }
  }
}
```

---

## Anti-Patterns

- ❌ Sub-agent producing freeform text instead of JSON in summary `taskResult`
- ❌ Omitting `retry_context` — orchestrator cannot make retry decisions
- ❌ Setting `should_escalate: false` after exhausting `max_attempts` — forces infinite retry loop
- ❌ Empty `strategies_tried` after multiple attempts — orchestrator re-invokes with no new information
- ❌ Putting file contents in the output — only paths, never content (too large for pipeline transfer)
- ❌ Sub-agent ignoring `upstream_decisions` constraints — breaks pipeline coherence
- ❌ Orchestrator retrying without adding previous errors to constraints — agent repeats same failure
