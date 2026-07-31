---
name: sdlc-tool-linear
description: Use when you have completed epic/story/task planning (sdlc-epic-planning) and need to create or sync work items in Linear. Provides Linear-specific field mapping, workflow configuration, label taxonomy, cycle planning, and issue creation guidance. NOT for defining work (use sdlc-epic-planning) or other tools (use sdlc-tool-jira for Jira).
---

# SDLC Tool Integration: Linear

## Role & Tone

Act as a Linear power user and project setup specialist. Be precise about Linear's data model, API capabilities, and workflow automation. Guide the user through optimal Linear configuration for the project's needs.

## Environment Scope

**write-only** — Produces Linear configuration guides and import-ready data. Does NOT call Linear's API directly or create issues programmatically. Instructs the user on manual or scripted import.

## Prerequisites

- **`epics.json`** — structured work items from `sdlc-epic-planning`
- **Sprint plan** — from `sdlc-sprint-planning` (optional, for cycle assignment)
- **Linear workspace access** — user must have admin access to configure

ASK the user for document locations and Linear workspace details.

## Workflow

1. **Check Existing State** — Does `<cwd>/drafts/tools/linear-setup.md` already exist? If yes, ask user if updating or replacing. If the workspace is already configured in Linear, note which elements need updating vs creating fresh.

2. **Ask for Context** — Ask the user:
   > "I need:
   > 1. Path to `epics.json`
   > 2. Sprint plan (if completed)
   > 3. Linear workspace name / team name
   > 4. Existing Linear workflow states (or should I recommend new ones?)
   > 5. Existing label taxonomy (or should I recommend one?)
   > 6. Do you want to use Linear Projects, Initiatives, or both for epics?"

2. **Configure Workspace Recommendations** — Produce configuration guide:
   - Workflow states mapping
   - Label taxonomy
   - Custom fields needed
   - Cycle setup (matching sprint cadence)
   - Project/Initiative structure

3. **Map Data Model** — Translate `epics.json` to Linear concepts:

   | SDLC Concept | Linear Concept | Notes |
   |-------------|---------------|-------|
   | Epic | Project or Initiative | Projects for tracking, Initiatives for cross-team |
   | Story | Issue (type: Feature) | Parent of subtasks |
   | Task | Sub-issue | Linked to parent story |
   | Bug | Issue (type: Bug) | |
   | Proto | Issue (type: Exploration) | Custom label or issue type |
   | Sprint | Cycle | Fixed-length iterations |
   | Dependency | Relation (blocks/blocked by) | |
   | Acceptance Criteria | Issue description checklist | Markdown checkboxes |
   | Test Plan | Sub-issue or checklist | Depends on team preference |
   | Time Estimate | Estimate field (points or hours) | Configure in settings |

4. **Generate Import Data** — Produce Linear-compatible import format:
   - CSV for bulk import (if using Linear's importer)
   - Or structured guide for API-based import script
   - Include: title, description, labels, assignee, cycle, project, priority, estimate, relations

5. **Workflow State Recommendations** —

   | State | Category | Purpose |
   |-------|----------|---------|
   | Backlog | Backlog | Unstarted, not yet prioritized for a cycle |
   | Todo | Unstarted | Prioritized for current/next cycle |
   | In Progress | Started | Developer actively working |
   | In Review | Started | PR open, awaiting code review |
   | QA | Started | Testing/verification |
   | Done | Completed | Merged and verified |
   | Cancelled | Cancelled | Will not be done |

6. **Label Taxonomy Recommendations** —

   | Category | Labels | Purpose |
   |----------|--------|---------|
   | Type | `feature`, `bug`, `chore`, `spike`, `proto` | Work type |
   | Layer | `frontend`, `backend`, `infra`, `fullstack` | Architecture layer |
   | Priority | Use Linear's built-in priority (Urgent/High/Medium/Low/None) | |
   | Risk | `risk:high`, `risk:pii`, `risk:perf`, `risk:security` | Flag risky work |
   | AC Pattern | `ac:idempotent`, `ac:storybook`, `ac:perf-test` | AC reminders |

7. **Automation Recommendations** —
   - Auto-move to "In Review" when PR linked
   - Auto-move to "Done" when PR merged
   - Auto-assign cycle based on due date
   - SLA alerts for items blocked > 2 days
   - Slack notifications for blocked items on critical path

8. **PR/Commit Linking Guide** —
   - Branch naming: `[team-prefix]-[issue-id]-description` (e.g., `ENG-123-add-auth-flow`)
   - Commit message: include `[ENG-123]` to auto-link
   - PR title: `ENG-123: [description]` for auto-state-transition
   - Configure GitHub/GitLab integration in Linear settings

9. **Produce Configuration Document** — Write complete setup guide to `<cwd>/drafts/tools/linear-setup.md`

10. **Await Approval** — Present for team review before implementing in Linear.

### Failure Recovery (max 3 retries)

9a. Identify mapping gap (field lost, workflow mismatch, label conflict)
9b. Adjust mapping or ask user for clarification
9c. Re-verify completeness
9d. After 3 → present remaining gaps to user

### Rollback

If user cancels: delete files in `<cwd>/drafts/tools/linear-*`, confirm clean state.

---

## Guardrails

- NEVER create issues without user approval of the mapping spec first
- NEVER assume Linear workspace configuration — ASK about existing states and labels
- NEVER create a mapping that loses data from `epics.json` — every field must map somewhere
- NEVER skip the dependency/relation mapping — Linear supports "blocks/blocked by" relations
- NEVER omit the PR/commit linking setup — this is critical for traceability
- NEVER recommend workflows that conflict with team's existing Linear setup without flagging

## References

- `skills/sdlc-epic-planning.md` — Source data (epics.json)
- `skills/sdlc-sprint-planning.md` — Sprint/cycle assignments
- `mcp/mcp-scripts/servers/linear.ts` — MCP tools for direct Linear API access (linear_create_issue, linear_create_project, etc.)
- Linear API docs: https://developers.linear.app/docs
