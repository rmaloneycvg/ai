# Frontend Pipeline Contract

## Why This Exists

The frontend orchestrator delegates work to specialized sub-agents running on different models optimized for their task type. Without a standardized communication format, sub-agents produce inconsistent output that the orchestrator can't reliably parse, chain, or retry. This contract defines the exact JSON schema every sub-agent receives as input and must produce as output.

## Sub-Agent Roster

| Agent | Model | Purpose |
|-------|-------|---------|
| `fe-scaffold` | claude-haiku-4.5 | Generate component files, stories, tests, barrel exports |
| `fe-architecture` | claude-opus-4.8 | Component decomposition, server/client boundaries, data flow decisions |
| `fe-styling` | claude-haiku-4.5 | Tailwind CSS, shadcn/ui composition, responsive design, accessibility |
| `fe-testing` | claude-sonnet-5 | Vitest unit tests, Playwright e2e, Storybook stories |
| `fe-refactor` | claude-opus-4.7 | Component/hook extraction, state migration, performance optimization |

## Pipeline Input Schema

Every sub-agent receives this structure as its task context from the orchestrator:

```json
{
  "task_type": "scaffold",
  "input": {
    "description": "Create a UserProfile component that displays user avatar, name, role, and edit button",
    "target_files": ["src/components/user-profile/"],
    "constraints": [
      "must be a client component (needs onClick)",
      "use shadcn/ui Avatar and Button primitives",
      "support loading skeleton state"
    ],
    "upstream_decisions": [
      {
        "from_agent": "fe-architecture",
        "decisions": [
          "client component — needs interactivity for edit button",
          "receive user data as props from server parent",
          "use Zustand for edit modal open/close state"
        ]
      }
    ]
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_type` | enum | ✅ | One of: `scaffold`, `architecture`, `styling`, `testing`, `refactoring` |
| `input.description` | string | ✅ | Human-readable description of what needs to be done |
| `input.target_files` | string[] | ❌ | File or directory paths this task targets. Empty for greenfield work. |
| `input.constraints` | string[] | ❌ | Hard requirements the sub-agent must follow |
| `input.upstream_decisions` | object[] | ❌ | Decisions from earlier pipeline stages that constrain this work |
| `input.upstream_decisions[].from_agent` | string | ✅ | Which sub-agent produced these decisions |
| `input.upstream_decisions[].decisions` | string[] | ✅ | List of decisions to follow |

## Pipeline Output Schema

Every sub-agent must produce this structure via the `summary` tool's `taskResult` field (as a JSON string):

```json
{
  "task_type": "scaffold",
  "output": {
    "status": "success",
    "files_created": [
      "src/components/user-profile/index.ts",
      "src/components/user-profile/user-profile.tsx",
      "src/components/user-profile/user-profile.stories.tsx",
      "src/components/user-profile/user-profile.test.tsx"
    ],
    "files_modified": [],
    "decisions_made": [
      "used forwardRef for potential parent ref access",
      "extracted UserProfileSkeleton as named export for Suspense fallback"
    ],
    "follow_up_suggestions": [
      "needs styling pass — currently using placeholder classes",
      "add Playwright test for edit button flow"
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

## Error Schema

Each entry in the `errors` array:

```json
{
  "type": "type_error",
  "message": "Property 'onEdit' does not exist on type 'UserProfileProps'",
  "file": "src/components/user-profile/user-profile.tsx",
  "line": 24,
  "attempt": 2
}
```

### Error Types

| Type | Description | Typical Source |
|------|-------------|----------------|
| `type_error` | TypeScript compilation error | `npx tsc --noEmit` |
| `lint_error` | ESLint or formatting issue | `npx eslint` |
| `test_failure` | Test assertion failed | `npx vitest run` |
| `build_error` | Build/bundler error | `npx next build` or `npx vite build` |
| `validation_error` | Zod schema or runtime validation failure | Application logic |

### Error Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | enum | ✅ | One of the error types above |
| `message` | string | ✅ | Human-readable error message |
| `file` | string | ❌ | File path where error occurred |
| `line` | number | ❌ | Line number (if available) |
| `attempt` | number | ✅ | Which attempt this error was encountered on (1-indexed) |

## Retry Context

```json
{
  "attempts_made": 2,
  "max_attempts": 3,
  "strategies_tried": [
    "added missing import for UserProfileProps",
    "changed interface to extend HTMLAttributes for className support"
  ],
  "should_escalate": false
}
```

### Retry Rules

1. **Max 3 attempts** per sub-agent invocation
2. **`strategies_tried`** records what was attempted — prevents the orchestrator from re-invoking with the same strategy
3. **`should_escalate`** signals the orchestrator to stop retrying and either:
   - Try a different sub-agent (if the error is outside this agent's domain)
   - Ask the user for guidance (if the error requires human judgment)

### When to Set `should_escalate: true`

- `attempts_made >= max_attempts` — exhausted retries
- Error type is outside the sub-agent's domain (e.g., a test agent finds a source code bug it cannot fix)
- Error requires a design decision the sub-agent cannot make autonomously
- Conflicting constraints that cannot be resolved without human input

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

## Pipeline Patterns

### New Component (full pipeline)

```
fe-architecture → fe-scaffold → fe-styling → fe-testing
```

1. **fe-architecture**: Analyze requirements → produce decisions (server/client, data flow, state)
2. **fe-scaffold**: Receive architecture decisions as `upstream_decisions` → generate files
3. **fe-styling**: Receive `files_created` → apply Tailwind/shadcn styling
4. **fe-testing**: Receive `files_created` + `files_modified` → write and run tests

### Refactoring

```
fe-refactor → fe-testing
```

1. **fe-refactor**: Apply refactoring with green baseline verification
2. **fe-testing**: Validate existing tests still pass, add coverage for new structure

### Standalone Tasks

- **"Style this component"** → `fe-styling` alone
- **"Write tests for X"** → `fe-testing` alone
- **"Extract this into a hook"** → `fe-refactor` alone
- **"How should I structure this page?"** → `fe-architecture` alone

## Examples by Task Type

### Architecture Output

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

### Testing Output (with errors)

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

### Refactoring Output (successful retry)

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

## Anti-Patterns

- ❌ Sub-agent producing freeform text instead of JSON in summary `taskResult`
- ❌ Omitting `retry_context` — orchestrator cannot make retry decisions
- ❌ Setting `should_escalate: false` after exhausting `max_attempts` — forces infinite retry loop
- ❌ Empty `strategies_tried` after multiple attempts — orchestrator re-invokes with no new information
- ❌ Putting file contents in the output — only paths, never content (too large for pipeline transfer)
- ❌ Sub-agent ignoring `upstream_decisions` constraints — breaks pipeline coherence
- ❌ Orchestrator retrying without adding previous errors to constraints — agent repeats same failure
