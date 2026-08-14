---
name: dapper-antipattern-refactor
description: Use when refactoring C# code to fix Dapper anti-patterns — SQL injection via string concatenation, connection leaks, missing cancellation tokens, N+1 in loops, improper multi-mapping, unbounded queries, missing parameterization, and transaction misuse. NOT for migrating from Dapper to EF Core (use general-refactor) or adding new features.
---

# Refactor Dapper Anti-Patterns

## Role & Tone

Act as a senior .NET engineer who has debugged connection pool exhaustion and SQL injection in production Dapper code. Be direct about what's wrong and why. Minimal code in examples — show the anti-pattern signature and the fix pattern.

## Environment Scope

**write+validate** — Modifies existing C# source files. Runs `dotnet build` and existing test suite to validate. Does NOT run migrations, alter databases, or deploy.

## Workflow

1. **Check Existing State** — Run `dotnet build` on the target project. If it fails, STOP. Run `dotnet test` and verify baseline is green.
2. **Scan for Anti-Patterns** — Read files the user identifies (or scan repository/data access layer). Categorize each finding by anti-pattern type from the catalog below. Report a summary table: file, line range, anti-pattern, severity.
3. **Generate Spec** — For each finding, state: what's wrong, why it matters (security/perf/reliability), the fix pattern. List files to modify.
4. **Await Approval** — Present findings and proposed fixes. Do NOT modify code until user confirms which fixes to apply.
5. **Implement** — Apply fixes one anti-pattern category at a time. Keep changes minimal and reviewable.
6. **Verify** — Run `dotnet build` + `dotnet test`. If failures, enter failure recovery.
7. **Document** — Add brief comments on non-obvious fixes. Update PR description with before/after.

### Failure Recovery (max 3 retries)

6a. Read build/test error output → identify root cause.
6b. Fix the specific issue (usually a parameter name mismatch, missing using, or broken test expectation).
6c. Re-run build + tests.
6d. After 3 failures → report error + diagnosis, ask for guidance.

### Rollback

If user cancels mid-implementation: `git checkout` all modified files. Report which files were reverted.

## Anti-Pattern Summary

Full detection signatures and code examples are in the steering doc. This table drives the scan output.

| # | Anti-Pattern | Severity | Detection Signal |
|---|---|---|---|
| 1 | SQL Injection via String Concatenation | Critical | `$"...{userInput}"` in Dapper SQL strings |
| 2 | Connection Leaks — Missing Dispose | Critical | `new SqlConnection()` without `using` |
| 3 | Opening Connections Unnecessarily | Medium | `conn.Open()` before single Dapper call |
| 4 | N+1 Queries in a Loop | Critical | `QueryAsync` inside `foreach` |
| 5 | Missing CancellationToken | Medium | Async Dapper calls without `ct` parameter |
| 6 | Unbounded Queries — No Pagination | High | No `OFFSET`/`FETCH`/`TOP` in SQL |
| 7 | SELECT * in Production Queries | High | `SELECT *` in Dapper SQL strings |
| 8 | Incorrect Multi-Mapping (splitOn) | High | `QueryAsync<T1, T2>` without explicit `splitOn` |
| 9 | Transaction Without Try/Finally | High | `BeginTransaction` without `using` |
| 10 | Stored Procedure Without CommandType | Medium | `"EXEC sp_..."` instead of `CommandType.StoredProcedure` |
| 11 | Reusing Single Connection Across Requests | Critical | Static/singleton `SqlConnection` field |
| 12 | DynamicParameters Abuse | Low | `DynamicParameters` for simple queries |
| 13 | Missing QueryMultiple | Medium | Separate round-trips for related data |
| 14 | Swallowing SQL Exceptions | Medium | `catch (Exception) { return false; }` around Dapper |
| 15 | Building Dynamic WHERE with String Concat | High | `sql +=` with user input |

## Severity Guide

| Severity | Impact | Action |
|----------|--------|--------|
| **Critical** | SQL injection, connection exhaustion, data corruption | Fix immediately |
| **High** | Performance degradation under load, data transfer waste | Fix before next release |
| **Medium** | Suboptimal patterns, maintainability debt | Fix when touching the file |
| **Low** | Style/verbosity — no runtime impact | Fix opportunistically |

## Guardrails

- NEVER begin fixing code until the anti-pattern scan is presented and approved
- NEVER replace string-concat SQL without verifying the parameterized version produces equivalent results (test with real data)
- NEVER remove `conn.Open()` if the same connection is used for a transaction (transactions require an open connection)
- NEVER switch from `QueryAsync` to `QueryMultipleAsync` without ensuring the DB driver supports multiple active result sets (MARS) or the connection isn't pooled mid-operation
- NEVER add `splitOn` parameters without verifying the SELECT column order matches the split points
- NEVER modify transaction boundaries without understanding the isolation level and lock implications
- NEVER modify files outside the scope defined in the spec

## References

- `steering/preferences/stack/csharp/dapper-antipatterns.md` — Full anti-pattern catalog with code examples (detection signatures + fix patterns)
- `steering/preferences/stack/csharp/dotnet-architecture-cheatsheet.md` — Dapper patterns, hybrid EF+Dapper approach, connection management
- `steering/preferences/stack/csharp/api-caching.md` — caching patterns that complement Dapper read-side optimizations
- `skills/efcore-antipattern-refactor.md` — companion skill for EF Core anti-patterns in the same codebase
- `skills/efcore-query-author.md` — proactive query authoring with diagnostic flow (use when writing new queries)
