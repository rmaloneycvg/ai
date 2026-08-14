---
name: efcore-antipattern-refactor
description: Use when refactoring C# code to fix EF Core anti-patterns — N+1 queries, missing projections, DbContext misuse, tracking overhead, lazy loading traps, incorrect lifetimes, missing CancellationToken, raw SQL injection, and bulk operation issues. NOT for adding new features or migrating away from EF Core entirely (use general-refactor for those).
---

# Refactor EF Core Anti-Patterns

## Role & Tone

Act as a senior .NET engineer who has debugged production EF Core performance disasters. Be direct about what's wrong and why. Minimal code in examples — show the anti-pattern signature and the fix pattern, not full implementations.

## Environment Scope

**write+validate** — Modifies existing C# source files. Runs `dotnet build` and existing test suite to validate. Does NOT run migrations, alter databases, or deploy.

## Workflow

1. **Check Existing State** — Run `dotnet build` on the target project. If it fails, STOP. Identify the test runner (`dotnet test`, or check for xUnit/NUnit in csproj) and verify tests pass.
2. **Scan for Anti-Patterns** — Read files the user identifies (or scan repository/service layer). Categorize each finding by anti-pattern type from the catalog in the steering doc. Report a summary table: file, line range, anti-pattern, severity (critical/high/medium).
3. **Generate Spec** — For each finding, state: what's wrong, why it matters (perf/correctness/thread-safety), the fix pattern. List files to modify.
4. **Await Approval** — Present findings and proposed fixes. Do NOT modify code until user confirms which fixes to apply.
5. **Implement** — Apply fixes one anti-pattern category at a time. Keep changes minimal and reviewable.
6. **Verify** — Run `dotnet build` + `dotnet test`. If failures, enter failure recovery.
7. **Document** — Add brief comments on non-obvious fixes (e.g., why AsNoTracking is used). Update PR description with before/after.

### Failure Recovery (max 3 retries)

6a. Read build/test error output → identify root cause.
6b. Fix the specific issue (usually a missing Include, wrong return type, or broken test expectation).
6c. Re-run build + tests.
6d. After 3 failures → report error + diagnosis, ask for guidance.

### Rollback

If user cancels mid-implementation: `git checkout` all modified files. Report which files were reverted.

## Anti-Pattern Summary

Full detection signatures and code examples are in the steering doc. This table drives the scan output.

| # | Anti-Pattern | Severity | Detection Signal |
|---|---|---|---|
| 1 | N+1 Queries | Critical | Navigation property access in loop without Include |
| 2 | Missing Projection | High | Full entity returned to API/view when only few fields needed |
| 3 | Tracking Overhead on Reads | High | No `AsNoTracking()` on read-only query paths |
| 4 | DbContext Lifetime Misuse | Critical | Singleton/static DbContext or shared across threads |
| 5 | Missing CancellationToken | Medium | Async EF calls without `ct` parameter |
| 6 | ToList Before Filter | Critical | `.ToList().Where()` — full table loaded into memory |
| 7 | Unbounded Queries | High | No `Take`/`Skip` on list queries |
| 8 | Find/First Without Index | Medium | Filter on non-indexed column |
| 9 | SaveChanges in Loop | Critical | `SaveChangesAsync` inside `foreach` |
| 10 | Implicit Lazy Loading | High | `UseLazyLoadingProxies()` enabled |
| 11 | String Interpolation in FromSqlRaw | Critical | `FromSqlRaw($"...{input}")` — SQL injection |
| 12 | Missing Query Splitting | Medium | 2+ collection Includes without `AsSplitQuery()` |
| 13 | Captive DbContext in Singleton | Critical | Scoped DbContext injected into singleton service |
| 14 | Missing Compiled Query on Hot Path | Medium | >100 req/sec without `EF.CompileAsyncQuery` |
| 15 | Exposing IQueryable from Repository | Medium | Repository returns `IQueryable<T>` to callers |

## Severity Guide

| Severity | Impact | Action |
|----------|--------|--------|
| **Critical** | Data loss, security vulnerability, production crashes | Fix immediately |
| **High** | Performance degradation under load, memory leaks | Fix before next release |
| **Medium** | Suboptimal performance, maintainability debt | Fix when touching the file |

## Guardrails

- NEVER begin fixing code until the anti-pattern scan is presented and approved
- NEVER remove `Include()` calls without verifying downstream usage won't null-reference
- NEVER change DbContext lifetime without auditing all consumers for thread-safety implications
- NEVER introduce `AsNoTracking()` on paths that subsequently call `SaveChangesAsync` on the same entities
- NEVER replace `FromSqlRaw` with `FromSqlInterpolated` without verifying the interpolated version parameterizes correctly (check generated SQL)
- NEVER add `AsSplitQuery()` blindly — it trades cartesian explosion for extra round-trips; measure both
- NEVER modify files outside the scope defined in the spec

## References

- `steering/preferences/stack/csharp/efcore-antipatterns.md` — Full anti-pattern catalog with code examples (detection signatures + fix patterns)
- `steering/preferences/stack/csharp/dotnet-architecture-cheatsheet.md` — EF Core vs Dapper patterns, DbContext thread safety, captive dependency details
- `steering/preferences/stack/csharp/api-caching.md` — caching patterns that complement read-side optimizations
- `skills/efcore-query-author.md` — proactive companion: interactive diagnostic for writing new EF Core queries correctly from the start
