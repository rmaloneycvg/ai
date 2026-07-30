---
name: react-hooks-optimization
description: Audit React components for hook misuse — replace useEffect with useMemo for derived state, useCallback for stable references, extract repeated patterns into custom hooks, consolidate multiple useState into useReducer. Triggers on "optimize hooks", "audit useEffect", or "extract custom hooks". NOT for general performance work (use refactor) or scaffolding new components (use react-components).
---

# Hooks Optimization

## Role & Tone

Act as a conservative React reviewer. **When a conversion is ambiguous, SKIP it and list it as "needs human review" rather than guessing.** Consistency across runs matters more than maximizing the number of conversions. Report skipped candidates explicitly.

## Environment Scope

**write+validate** — Modifies existing source files and creates new hook files in `src/hooks/`. Runs the project's test suite to validate no regressions. Does NOT add features, change behavior, deploy, or start services.

## Defaults (No Ambiguity Permitted)

| Input | Default |
|-------|---------|
| Scope, if user gives none | `src/**/*.{ts,tsx}` — excluding `*.test.*`, `*.stories.*`, `src/components/ui/**` |
| Max files per run | 20. If more candidates exist, process the 20 with the most hook instances and report the remainder. |
| Test command | Read `package.json` scripts in this order: `test` → `test:unit` → fallback `npx vitest run` |
| No test suite exists | STOP after Scan. Report candidates and state that no verification is possible. Do NOT modify code. |
| "Trivial" computation | Single expression, no function calls, no loops, no array/object allocation. Example: `a + b`, `` `${x} ${y}` ``, `x > 0`. Anything else is non-trivial. |
| Hook file naming | `src/hooks/use-<kebab-name>.ts`. If the file already exists, reuse it — never create `use-debounce-2.ts`. |

## Workflow

1. **Preflight** — Run `git status --porcelain` on the scope. If uncommitted changes exist in target files, WARN the user that rollback could overwrite their work and require explicit confirmation to proceed.
2. **Establish Baseline** — Run the test command. If tests fail, STOP and report. If no test suite exists, follow the Defaults table.
3. **Scan** — Find `useEffect`, `useMemo`, `useCallback`, `useState` instances within scope. Categorize each as: Phase 1 candidate / Phase 2 candidate / Phase 3 candidate / Phase 4 candidate / skip (with reason).
4. **Idempotency Check** — If zero candidates qualify, report "already optimized" and EXIT without modifying anything.
5. **Present Findings & Await Approval** — Report per phase: candidate count, affected files, skipped items with reasons. Do NOT modify code until the user confirms.
6. **Phase 1: useEffect → useMemo** → run tests → commit-sized checkpoint
7. **Phase 2: useEffect → useCallback** → run tests → checkpoint
8. **Phase 3: Extract Custom Hooks** → run tests → checkpoint
9. **Phase 4: useState → useReducer** → **re-scan first** (Phase 1 deleted state declarations Phase 4 would have counted) → run tests → checkpoint
10. **Final Verify** — Run test suite, typecheck (`npx tsc --noEmit`), and lint (`npx eslint` with `react-hooks/exhaustive-deps`). All three must pass.
11. **Report** — Per phase: conversions applied, candidates skipped with reasons, files modified, files created.

**Phase order is fixed.** Phases 1 and 2 reduce `useEffect` count; Phase 3 extracts what remains; Phase 4 operates on the post-Phase-1 state landscape. Never reorder.

---

## Phase 1: useEffect → useMemo

**Detect:** `useEffect` whose entire body is one or more `setState` calls with values computed synchronously from props/state. No async, no cleanup return, no DOM access, no external calls.

**Action:**
- Non-trivial computation → delete the `useState`/`useEffect` pair, replace with `useMemo`
- Trivial computation (see Defaults) → delete the pair, compute inline without `useMemo`

**Skip when:** async operations, DOM mutations, cleanup logic, event dispatch/logging, conditional updates reading values absent from the dep array, or the state is also set from elsewhere in the component.

---

## Phase 2: useEffect → useCallback

**Detect:** `useEffect` whose entire body assigns a function to a ref or state, existing only to keep the reference current.

**Action:** Replace with `useCallback` carrying the same deps.

**Skip when:** the effect registers/unregisters event listeners; the effect does anything beyond the assignment; **the ref is deliberately read inside another effect or subscription to avoid re-subscribing** (this is the intentional latest-ref pattern — converting it changes behavior).

---

## Phase 3: Extract Custom Hooks

**Detect (both conditions required):**
1. The same hook combination appears in **2 or more** components, AND
2. The group contains **2 or more** React hooks working toward one named concern

Single-component hook groups do NOT qualify regardless of length.

**Action:** Extract to `src/hooks/use-<name>.ts` per the Defaults naming rule. Co-locate `use-<name>.test.ts`. Wrap returned functions in `useCallback`. Replace all original usages. Preserve behavior exactly.

**Skip when:** used in one component only, requires 4+ parameters, types don't generalize, or an equivalent hook already exists in `src/hooks/` (reuse it instead).

**Precedence:** If a candidate qualifies for both Phase 3 and Phase 4, Phase 4 wins — extract it as a `useReducer`-based hook in Phase 4 rather than a plain hook in Phase 3.

---

## Phase 4: useState → useReducer

**Detect:** A **synchronous** code path (single event handler or its direct callees, excluding async continuations) that calls 2+ distinct `setState` functions unconditionally. Branching paths each setting different state count only if 2+ setters fire on the same branch.

**Action:** Replace with `useReducer` wrapped in a custom hook. Reducer stays pure and lives outside the component. Actions use `{ type: string; payload?: T }`. Expose named functions, not `dispatch`.

**Skip when:** single state variable, server state (TanStack Query owns it), global state (Zustand owns it), form state (React Hook Form + Zod own it), or the setters fire in separate async continuations.

---

## Guardrails

- NEVER convert a `useEffect` with async logic, cleanup, or DOM side effects to `useMemo`
- NEVER convert a deliberate latest-ref pattern to `useCallback` (breaks the no-re-subscribe intent)
- NEVER extract a custom hook that alters behavior — extraction is mechanical only
- NEVER proceed past a failing test suite
- NEVER add `useMemo`/`useCallback` for trivial computations (see Defaults for the definition)
- NEVER run `git checkout --` without first confirming via `git status` that no unstaged user work is present
- NEVER create a second hook file with a near-duplicate name — reuse the existing hook
- ALWAYS delete the dead `useState` after a Phase 1 conversion
- ALWAYS preserve dependency arrays verbatim
- ALWAYS re-scan before Phase 4
- ALWAYS report skipped candidates with reasons

## Failure Recovery (max 3 retries per phase)

1. Read the test failure → identify the specific file and component
2. Revert that file only: `git checkout -- <file>`
3. Re-analyze — was the `useEffect` doing something beyond derived state?
4. If the conversion is genuinely wrong, mark the candidate as "skip: behavior-dependent" and continue
5. After 3 failures in one phase → abandon that phase, revert its files, report, continue to next phase

## Rollback

1. Confirm `git status` shows no unstaged work you'd destroy (Preflight already checked; re-check if time has passed)
2. `git checkout -- <files modified by this skill>` — track this list as you go
3. Delete any hook files created in `src/hooks/` during this run
4. Re-run tests to confirm the green baseline is restored
5. Report which files were reverted and which conversions were attempted

## References (Lazy-Load)

Load a steering file **only when the corresponding phase runs or the hook is encountered**. Do not preload.

| Trigger | Load |
|---------|------|
| Phase 1 runs | `steering/preferences/stack/react/use-effect.md`, `steering/preferences/stack/react/use-memo.md` |
| Phase 2 runs | `steering/preferences/stack/react/use-callback.md` |
| Phase 4 runs | `steering/preferences/stack/react/use-reducer.md` |
| `useRef` in a candidate | `steering/preferences/stack/react/use-ref.md` |
| `useLayoutEffect` in a candidate | `steering/preferences/stack/react/use-layout-effect.md` |
| `useTransition`/`useOptimistic` in a candidate | `steering/preferences/stack/react/use-transition.md`, `steering/preferences/stack/react/use-optimistic.md` |
| `useDeferredValue` in a candidate | `steering/preferences/stack/react/use-deferred-value.md` |
| `useSyncExternalStore` in a candidate | `steering/preferences/stack/react/use-sync-external-store.md` |
| `useContext` in a candidate | `steering/preferences/stack/react/use-context.md` |

**Always loaded:** `steering/preferences/stack/react/custom-hooks.md` — extraction criteria, naming, return-value rules, testing. Governs Phase 3 and any hook created in Phase 4.
