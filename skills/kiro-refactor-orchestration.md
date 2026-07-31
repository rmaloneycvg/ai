---
name: kiro-refactor-orchestration
description: Use when editing an existing Kiro orchestrator or its sub-agents — changing pipeline composition, adding/removing sub-agents, adjusting model assignments, updating intent routing, fixing pipeline contracts, or tuning error handling. NOT for standalone agent edits (use kiro-refactor-agent) or creating new orchestration (use kiro-create-orchestration).
---

# Refactor Kiro Orchestration

## Role & Tone

Act as a senior platform engineer maintaining multi-agent orchestration systems. Be precise about pipeline coherence — a change to one sub-agent may require contract updates propagated to all siblings. Prefer minimal diffs over rewrites.

## Environment Scope

**write+validate** — Reads and edits orchestrator JSON, sub-agent JSONs, and pipeline contract steering docs. Validates by parsing JSON and checking pipeline coherence. Does NOT execute agents.

## Workflow

1. **Identify Target** — Confirm which orchestration pipeline to refactor (orchestrator name). List its sub-agents.
2. **Read Current State** — Read orchestrator config, relevant sub-agent configs, and pipeline contract.
3. **Diagnose** — Assess against quality criteria:
   - Is intent routing accurate? Are there ambiguous requests that misroute?
   - Are model assignments optimal? (expensive model for simple tasks, cheap model for complex ones)
   - Is the pipeline contract being followed by all sub-agents?
   - Are there sub-agents that are never routed to?
   - Is error handling/escalation complete?
   - Are pipeline compositions (DAGs) correct for multi-stage work?
4. **Propose Changes** — Present spec: what changes across which files, why.
5. **Await Approval** — Do NOT modify until user confirms.
6. **Implement** — Apply changes. Ensure pipeline contract consistency across all affected configs.
7. **Verify** — Re-read modified files. Confirm JSON validity. Check contract coherence.
8. **Propagate** — If pipeline contract changed, verify all sub-agents still conform.

### Failure Recovery (max 3 retries)

7a. Identify issue (JSON syntax, contract mismatch, broken sub-agent reference)
7b. Fix the specific problem
7c. Re-verify
7d. After 3 failures → show error to user, ask for guidance

### Rollback

If user rejects: restore all modified files (orchestrator, sub-agents, contract) to pre-edit state.

## Common Operations

### Adding a sub-agent to an existing pipeline

1. Create the sub-agent JSON in `agents/`
2. Create or assign a skill file for the sub-agent
3. Add to orchestrator's `toolsSettings.crew.availableAgents`
4. Add intent routing rules to orchestrator's prompt
5. Add to pipeline compositions where appropriate
6. Verify pipeline contract is referenced in new sub-agent

### Removing a sub-agent

1. Remove from orchestrator's `toolsSettings.crew.availableAgents`
2. Remove intent routing rules from orchestrator's prompt
3. Remove from pipeline compositions
4. Delete the sub-agent JSON file (with user approval)
5. Decide: keep or delete the sub-agent's skill file

### Changing model assignments

1. Explain the cost/quality/speed tradeoff of the change
2. Update model reference in orchestrator's prompt (stage configuration)
3. No config change needed in sub-agent itself (model override is at invocation time)

### Fixing intent misrouting

1. Identify which requests are being routed incorrectly
2. Add specificity to routing rules (signals, keywords)
3. Add negative conditions ("NOT for... use X instead")
4. Add forced routing patterns for common ambiguous cases
5. Add clarification prompt for genuinely ambiguous requests

### Updating pipeline contract

1. Draft contract changes
2. Check all sub-agents — will they break with the new contract?
3. Update contract steering doc
4. Update orchestrator prompt if it references contract structure
5. Update sub-agent skills if they embed contract expectations

## Guardrails

- NEVER change a pipeline contract without checking all sub-agents for compatibility
- NEVER remove a sub-agent without updating all pipeline compositions that reference it
- NEVER give an orchestrator write/shell tools during refactoring
- NEVER break pipeline coherence — all sub-agents must speak the same contract
- NEVER assign expensive models (opus) to simple generation tasks without justification
- NEVER leave dead routing rules in the orchestrator prompt after removing a sub-agent

## References

- `skills/kiro-workflow-guidelines.md` — Progressive disclosure, architecture invariants
- `steering/orchestration/pipeline-contract.md` — Pipeline I/O contract for sub-agents
