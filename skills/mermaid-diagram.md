---
name: mermaid-diagram
description: Use when the user asks to create, update, or modify ANY diagram, flowchart, architecture visualization, sequence flow, state machine, ER diagram, class diagram, or visual representation of a system or process. ALL diagrams must be Mermaid syntax in markdown code blocks — never use draw.io, Excalidraw, ASCII art, PlantUML, or any other diagramming tool. Covers flowcharts, sequence diagrams, state diagrams, ER diagrams, class diagrams, and Gantt charts. Ensures diagrams render without errors by avoiding known parser bugs (smart quotes, em-dashes, composite state self-transitions, Unicode characters). NOT for general documentation updates (use general-documentation).
---

# Mermaid Diagram Authoring

## Role & Tone

Act as a diagramming specialist who writes Mermaid that renders correctly on the first attempt. Be precise about syntax. When updating existing diagrams, preserve the intent while fixing rendering issues.

## Environment Scope

**write+validate** — Writes/updates Mermaid blocks in markdown files. Validates syntax by checking against known failure patterns. Does NOT execute mmdc CLI unless available (instructs user to run validation if needed).

## Workflow

1. **Check Existing State** — If updating: read the target markdown file, locate the mermaid block(s). If creating: identify where in the file the diagram belongs.
2. **Determine Diagram Type** — Select the correct diagram type based on what's being communicated:
   - Flowchart: processes, decisions, system architecture
   - Sequence: service interactions, request flows, temporal ordering
   - State: lifecycles, status machines, workflow states
   - ER: data models, relationships
   - Class: code architecture, inheritance
   - Gantt: timelines, project schedules
3. **Draft Diagram** — Write the mermaid code following all guardrails below.
4. **Validate Against Guardrails** — Check every line against the Known Failures checklist. Fix before presenting.
5. **Implement** — Insert or replace the mermaid block in the target file.
6. **Verify** — If `npx mmdc` (mermaid-cli) is available, run: `npx mmdc -i <file> -o /tmp/mermaid-test.svg -e svg`. Otherwise, report that manual verification is needed.

### Failure Recovery (max 3 retries)

6a. Read error output — identify the specific syntax failure
6b. Check against Known Failures list — apply the documented fix
6c. Re-run validation
6d. After 3 failures — present the error and diagram to user, ask for guidance

### Rollback

If the diagram breaks an existing file:
1. Restore the previous mermaid block from git: `git checkout -- <file>`
2. Report what went wrong and propose an alternative approach

## Guardrails

### NEVER Use These (Known Renderer Failures)

| Pattern | Failure Mode | Fix |
|---------|-------------|-----|
| Smart/curly quotes `"` `"` `'` `'` | Parser error: unexpected token | Use only ASCII `"` (0x22) and `'` (0x27) |
| Em-dash `—` (U+2014) | Parser error or silent rendering break | Use `--` or reword |
| En-dash `–` (U+2013) | Parser error | Use `-` or `--` |
| Unicode arrows `→` `←` `↓` `↑` | Inconsistent rendering across tools | Use mermaid arrow syntax `-->` or text descriptions |
| Any non-ASCII in node text | Rendering varies by platform | Use HTML entities or ASCII only |
| `stateDiagram-v2` self-transition on composite state | TypeError: Cannot set properties of undefined (setting 'order') | Use internal loop within the nested state, or switch to flowchart with subgraphs |
| `stateDiagram-v2` transitions between composite states | Same TypeError or layout corruption | Flatten to flowchart with subgraphs instead |
| Tabs for indentation | Inconsistent parsing | Use spaces only (4-space indent) |
| Unquoted special chars in labels: `(`, `)`, `[`, `]`, `{`, `}` | Parser treats them as syntax | Wrap label in `["text with (parens)"]` |
| Pipe `\|` inside node text without quotes | Breaks edge label parsing | Quote the node: `A["text \| more"]` |
| Empty lines inside a subgraph | Some renderers close the subgraph early | Keep subgraph content contiguous |
| Comment `%%` mid-line | Some parsers fail | Put `%%` comments on their own line |

### ALWAYS Do These

- **ASCII only** inside mermaid blocks — no Unicode characters of any kind
- **Quote node labels** that contain special characters: `A["Label with (parens) and <html>"]`
- **HTML entities** for angle brackets in labels: `&lt;` and `&gt;` instead of `<` and `>`
- **4-space indentation** consistently throughout
- **One blank line** before and after the mermaid code fence in the markdown
- **Test composite state diagrams as flowcharts** — if you need nested states, use `flowchart` with `subgraph` blocks instead of `stateDiagram-v2` with `state X { }` 
- **Keep diagrams under 30 nodes** — larger diagrams should be split into multiple focused diagrams
- **Use descriptive node IDs** — `OrderService` not `A`, `PaymentGW` not `B` (unless it's a simple linear flow)

### Diagram Type Selection Rules

| If you need... | Use | Not |
|---------------|-----|-----|
| Process flow with decisions | `flowchart TD/LR` | `stateDiagram-v2` |
| Service-to-service calls with timing | `sequenceDiagram` | `flowchart` |
| Lifecycle states (SIMPLE, no nesting) | `stateDiagram-v2` (flat only) | — |
| Lifecycle states (COMPLEX, nested) | `flowchart` with `subgraph` | `stateDiagram-v2` with `state X {}` |
| Database relationships | `erDiagram` | `classDiagram` |
| Code architecture/inheritance | `classDiagram` | `flowchart` |
| Timeline/schedule | `gantt` | `flowchart LR` |

### Safe stateDiagram-v2 Usage

Only use `stateDiagram-v2` for FLAT state machines with NO nested composite states:

```
%% SAFE: flat states, no nesting
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : submit
    Processing --> Complete : success
    Processing --> Failed : error
    Failed --> Idle : retry
    Complete --> [*]
```

If you need nested states (phases containing sub-states), ALWAYS use flowchart with subgraphs:

```
%% SAFE: subgraphs replace composite states
flowchart TD
    subgraph Phase1["Initialization"]
        A[Connect] --> B[Authenticate]
    end
    subgraph Phase2["Processing"]
        C[Validate] --> D[Execute]
        D --> E[Confirm]
    end
    B --> C
    E --> F[Done]
```

### Style Blocks

Always place `style` declarations at the END of the diagram, after all nodes and edges are defined:

```
flowchart TD
    A[Start] --> B[End]
    style A fill:#e8f5e9
    style B fill:#e1f5fe
```

## Quick Reference: Arrow Syntax

| Diagram Type | Arrow | Meaning |
|-------------|-------|---------|
| flowchart | `-->` | Solid line with arrow |
| flowchart | `-.->` | Dotted line with arrow |
| flowchart | `==>` | Thick line with arrow |
| flowchart | `-->\|text\|` | Labeled edge |
| sequence | `->>` | Solid with arrowhead |
| sequence | `-->>` | Dotted with arrowhead |
| sequence | `--)` | Async message |
| state | `-->` | Transition |

## References

- `steering/conventions/documentation.md` — README structure and diagram validation commands
