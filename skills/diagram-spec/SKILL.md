---
name: diagram-spec
description: edits text in markdown files. use ONLY these mermaid declarations when edit/adding diagrams in markdown files - architecture-beta, flowchart, erDiagram, stateDiagram-v2, sequenceDiagram, journey, eventmodeling, ishikawa-beta
compatibility: documentation files
metadata: 
  assets:
    - puppeteer-config.json
  scripts:
    - validate-mermaid.sh
allowed-tools: Zsh(git:*) Zsh(grep:*) Zsh(./scripts/validate-mermaid.sh) Read Write
---

# Diagram Authoring
## Role & Tone

Act as a diagramming specialist who writes Mermaid that renders correctly on the first attempt. Be precise about syntax. When updating existing diagrams, preserve the intent while fixing rendering issues. 

## Environment Scope

**write+validate** — Writes/updates Mermaid blocks in markdown files. Validates syntax by checking against known failure patterns via a local script.

## Workflow

1. **Check Existing State** — If updating: read the target markdown file, locate the mermaid block(s). If creating: identify where in the file the diagram belongs.
2. **Implement** — Insert or replace the mermaid block in the target file. ONLY edit the contents between ` ```mermaid ` and ` ``` `.
3. **Verify** 
  a. run: `./scripts/validate-mermaid.sh <file>`
  b. Read error output — identify the specific syntax failure and fix
  c. Re-run validation
  d. After 3 failures — present the error and diagram to user, ask for guidance

## Diagram Specifications (Reference Routing)

For concise steering, detailed diagram syntax and examples are loaded on-demand. When creating a new diagram or modifying an unfamiliar one, you MUST read the corresponding specification file before generating Mermaid code.

* For cloud topologies and structural layouts: Read `references/architecture.md`
* For decision trees and logic: Read `references/flowchart.md`
* For data structures and cardinality: Read `references/er-diagram.md`
* For system/object state behavior: Read `references/state-behavior.md`
* For API chronological calls and outbox messages: Read `references/sequence.md`
* For mapping user experiences and phases: Read `references/journey.md`
* For UI/Command/Event flows: Read `references/event-modeling.md`
* For root cause analysis (fishbone): Read `references/ishikawa.md`

## Implementation Notes for Diagram-as-Code

### Anti-patterns:
* **Monolithic Graphs:** Cramming 50+ nodes into a single `flowchart` or `erDiagram`, resulting in unreadable renders and higher LLM hallucination rates.
* **Brittle Formatting:** Forcing hardcoded layouts or manual line-breaks instead of letting Mermaid's layout engine handle spacing.
* **Syntax Mixing:** Attempting to inject standard Markdown formatting into beta diagram labels without the proper backtick-and-quote syntax (e.g., `["`**label**`"]`).

### Telemetry metrics:
* **Render Parsing Success Rate:** Track how often the generated Mermaid syntax fails parser validation inside your workflow.
* **Diagram Generation Latency:** Measure the specific time spent generating the Mermaid block payload relative to the total request execution.
* **Token Complexity Density:** Monitor the size of the generated diagram against its actual node count to detect structural bloat.

### Other design options:
* **Progressive Disclosure:** Generate high-level `architecture-beta` diagrams first, with clickable nodes (using `click` directives in supported charts) that drill down into detailed `sequenceDiagram` or `eventmodeling` charts.
* **Alternative Renderers:** Ensure your skill provides fallback standard JSON schemas or PlantUML formats if the specific Mermaid beta renderer is unavailable in the execution environment.


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
- **Always group related services** into subgraphs or architectural groups representing their Bounded Context to prevent visually cluttered, flat diagrams.
