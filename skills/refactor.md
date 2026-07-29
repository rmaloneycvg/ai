---
name: refactor
description: Refactor existing application code — extracting components, migrating state management, restructuring API layers, or improving performance/accessibility. NOT for refactoring Kiro skills (use refactor-kiro-skill) or adding new features (use react-components or backend-rest-api-feature).
---

# Refactor Code

## Environment Scope

**write+validate** — Modifies existing source files. Runs existing test suite (`npx vitest run` or project test command) to validate no regressions. Does NOT deploy or start services.

## Workflow

1. **Check Existing State** — Run existing tests to establish a green baseline. If tests fail before refactoring, STOP and report — never refactor against a broken test suite.
2. **Gather Context** — Read the files targeted for refactoring. Identify callers/consumers of the code being changed (bounded: read only direct importers, not the whole codebase).
3. **Generate Spec** — List: what will change, what stays, files affected, expected behavior preservation. If extracting a component, show the proposed interface.
4. **Await Approval** — Present the spec. Do NOT modify code until user confirms.
5. **Implement** — Apply changes in small, atomic steps. One concept per commit-sized change.
6. **Verify** — Run full test suite. Expected: all tests that passed before still pass. If failures, enter failure loop.
7. **Document** — Update imports in consumers. Note breaking interface changes in PR description.

### Failure Recovery (max 3 retries)

6a. Read test failure → identify which behavioral contract was broken
6b. Fix the refactored code (not the test) to restore the contract
6c. Re-run test suite
6d. After 3 failures → revert to pre-refactor state, show user what's failing, ask for guidance

### Rollback

If user cancels or tests can't be fixed:
1. `git checkout -- <all modified files>` to restore pre-refactor state
2. Re-run tests to confirm green baseline restored
3. Report which files were reverted

## Component Extraction

- Identify reusable UI patterns (3+ usages or clear domain boundary)
- Extract into its own directory with story and test
- Replace original usages with the new component
- Preserve existing prop interfaces; extend rather than break

```tsx
// Before: inline JSX repeated in multiple places
// After: extracted <StatusBadge status={status} />
```

## State Management Migration

- Audit current state location (local, context, global store)
- Prefer colocated state; lift only when shared across siblings
- Migration path: local state → context → global store (zustand)
- Move one slice at a time; keep old and new running in parallel during transition
- Remove old state only after all consumers are migrated and tests pass

## API Layer Refactoring

- Consolidate duplicate fetch logic into shared hooks/services
- Normalize error handling (consistent error types, retry logic)
- Introduce TanStack Query if not already present
- Update types alongside API changes — never leave stale types

## Performance Optimization

- Profile first: React DevTools Profiler, Lighthouse, bundle analyzer
- Common wins:
  - Memoize expensive computations (`useMemo`, `React.memo`)
  - Virtualize long lists (`react-window` / `react-virtuoso`)
  - Code-split routes and heavy components (`React.lazy`)
  - Reduce re-renders by stabilizing references (`useCallback`, extract static objects)
- Measure after every change to confirm improvement

## Accessibility Improvements

- Run axe-core or Lighthouse accessibility audit first
- Fix in priority order: critical → serious → moderate
- Common fixes:
  - Add missing labels, alt text, ARIA attributes
  - Ensure keyboard navigation and focus management
  - Check color contrast ratios (4.5:1 minimum)
  - Add skip links and landmark regions
- Add accessibility tests to prevent regressions

## Guardrails

- NEVER refactor and add features in the same operation — keep them separate
- NEVER refactor without a green test baseline — write characterization tests first if none exist
- NEVER break existing public interfaces without explicit user approval
- NEVER leave stale types, imports, or dead code after refactoring
- NEVER skip re-running the full test suite after changes
- NEVER modify test assertions to make them pass — fix the code instead

## References

- `steering/conventions/code-style.md` — Naming conventions, file organization, import ordering to follow during refactoring
- `steering/preferences/stack/react/dependency-graph.md` — Component hierarchy, allowed imports, and state management preferences
- `steering/orchestration/local.md` — Running the full stack locally to validate refactors end-to-end
