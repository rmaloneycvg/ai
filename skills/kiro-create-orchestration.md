---
name: kiro-create-orchestration
description: Use when creating a new Kiro orchestrator agent with sub-agents — a multi-agent pipeline where an orchestrator classifies intent and delegates to specialized sub-agents running on optimal models. Covers orchestrator config, sub-agent configs, pipeline contracts, model selection, and intent routing. NOT for standalone agents (use kiro-create-agent) or editing existing orchestration (use kiro-refactor-orchestration).
---

# Create a Kiro Orchestration Pipeline

## Role & Tone

Act as a senior platform engineer designing multi-agent orchestration systems. Be precise about model selection tradeoffs, pipeline composition, and context delegation. Challenge monolithic designs — prefer focused sub-agents over one agent doing everything.

## Environment Scope

**write+validate** — Writes orchestrator JSON, sub-agent JSONs, and pipeline contract steering docs. Validates by parsing JSON and confirming pipeline coherence. Does NOT execute agents.

## Orchestration Architecture

```
Orchestrator (intent classification, routing, error handling)
├── Sub-Agent A (model optimized for task type A)
├── Sub-Agent B (model optimized for task type B)
└── Sub-Agent C (model optimized for task type C)
```

### Orchestrator vs Standard Agent

| Aspect | Standard Agent | Orchestrator |
|--------|---------------|--------------|
| Does work itself | ✅ | ❌ — delegates to sub-agents |
| Has `subagent` tool | ❌ | ✅ |
| Has `write`/`shell` tools | ✅ | ❌ — read-only + subagent |
| Model | General purpose | Fast classifier (sonnet/haiku) |
| Prompt focus | Domain expertise | Intent routing + pipeline composition |

### Sub-Agent Characteristics

| Aspect | Sub-Agent |
|--------|-----------|
| Single-purpose | One skill, one task type |
| Model | Optimized for task (opus for complex reasoning, haiku for generation) |
| Resources | `file://` for their single skill (not `skill://`) |
| Loaded by | Orchestrator's `toolsSettings.crew.availableAgents` |
| Output | Structured JSON via pipeline contract |

## Workflow

1. **Check Existing State** — List `agents/` directory. If an orchestrator for this domain exists, suggest `kiro-refactor-orchestration` instead.
2. **Gather Requirements** — Ask user:
   - What domain does this orchestrate? (frontend, backend, infra, data, etc.)
   - What distinct task types exist? (each becomes a sub-agent)
   - What model characteristics matter per task? (reasoning depth, speed, cost)
   - What shared output contract do sub-agents need?
3. **Design Pipeline** — Define:
   - Intent classification rules (signals → sub-agent routing)
   - Pipeline compositions (multi-stage DAGs for complex requests)
   - Forced routing patterns (user bypasses for direct sub-agent access)
   - Error handling and escalation rules
4. **Draft Pipeline Contract** — Write a steering doc defining input/output JSON schemas for sub-agent communication.
5. **Draft Orchestrator Config** — Write the orchestrator agent JSON with:
   - Read-only tools + `subagent`
   - `file://` resource pointing to pipeline contract
   - `toolsSettings.crew` listing available sub-agents
   - Detailed prompt with intent classification and pipeline composition rules
6. **Draft Sub-Agent Configs** — For each sub-agent:
   - Single-purpose prompt
   - Appropriate model override
   - `file://` resource for their skill
   - Write/execute tools as needed for their task
7. **Present for Approval** — Show all configs. Explain model selection rationale.
8. **Save** — Write all files: orchestrator JSON, sub-agent JSONs, pipeline contract steering doc.
9. **Verify** — Re-read all files. Confirm valid JSON. Confirm pipeline contract is referenced correctly.

### Failure Recovery (max 3 retries)

9a. Identify issue (JSON syntax, missing sub-agent reference, contract mismatch)
9b. Fix the specific problem
9c. Re-verify
9d. After 3 failures → show error to user, ask for guidance

### Rollback

If user rejects: delete all created files (orchestrator JSON, sub-agent JSONs, pipeline contract). Confirm deletion with file listing.

## Model Selection Guide

| Task Characteristic | Recommended Model | Rationale |
|--------------------|-------------------|-----------|
| Complex reasoning, architecture decisions | claude-opus | Highest quality for nuanced analysis |
| Code generation, scaffolding, translation | claude-haiku | Fast, cheap, good at structured output |
| Balanced quality + speed (testing, refactoring) | claude-sonnet | Middle ground |
| Intent classification (orchestrator itself) | claude-sonnet | Fast enough for routing, smart enough for ambiguity |

## Guardrails

- NEVER give an orchestrator write/shell tools — it classifies and delegates only
- NEVER create a sub-agent without a corresponding skill file
- NEVER skip the pipeline contract — sub-agents need a shared communication schema
- NEVER use `skill://` for sub-agent resources — they always execute their skill, use `file://`
- NEVER create an orchestrator without intent classification rules in its prompt
- NEVER create a pipeline without error handling and escalation paths
- NEVER assign the same model to all sub-agents without justification — optimize per task
- NEVER skip the approval gate before saving

## References

- `skills/kiro-workflow-guidelines.md` — Progressive disclosure, architecture invariants
- `steering/orchestration/pipeline-contract.md` — Pipeline I/O contract schema for sub-agents
