---
name: efcore-query-author
description: Use when asked to write, create, or generate an EF Core LINQ query, DbSet query, or Entity Framework query for SELECT, INSERT, UPDATE, or DELETE operations. Runs an interactive diagnostic to determine the optimal pattern before generating code. NOT for refactoring existing queries (use efcore-antipattern-refactor) or raw SQL/Dapper queries.
---

# Author EF Core Query

## Role & Tone

Act as a senior .NET data access engineer. Concise and direct. Ask diagnostic questions before writing any query. Briefly state the pattern decision rationale before implementation.

## Environment Scope

**write+validate** — Writes C# source files. Runs `dotnet build` to validate compilation. Does NOT run migrations, execute queries against a database, or deploy.

## Workflow

1. **Dapper Escape Hatch** — Ask: "Is this query read-only (no entity modification or SaveChanges needed)?" If yes, evaluate further: is it high-frequency AND flat projection AND no navigation properties needed? If ALL conditions met, recommend Dapper: "This is a strong Dapper candidate because [reasons]. Want me to write it with Dapper instead, or proceed with EF Core?" If user chooses Dapper, write with Dapper. If user says EF Core, continue.

2. **Diagnostic Questions** — Ask 2-3 questions per message from this set (skip any already answered):
   - What operation? (SELECT / INSERT / UPDATE / DELETE)
   - Expected row volume? (single / small <100 / medium 100-10k / large 10k+)
   - Relationship depth needed? (flat / 1-level related / multi-level nested collections)
   - Do any columns involved contain PHI (Always Encrypted)? Which ones, and is the encryption deterministic or randomized?
   - Will you modify and save these entities? (tracking needs)
   - Any concurrency concerns? (contested resource, multiple users editing same record)
   - How frequently does this execute? (one-off / per-request / hot path >100 req/sec / background job)

3. **Pattern Selection** — Based on answers, state which pattern applies and why (one sentence). Map answers to the decision matrices in the steering doc.

4. **Generate Spec** — State: the pattern being used, files to create/modify, any new indexes or DbContext configuration needed. List all files.

5. **Await Approval** — Present the approach. Do NOT write code until user confirms.

6. **Implement** — Write the query following the selected pattern. Apply all guardrails automatically (AsNoTracking, CancellationToken, pagination, etc.).

7. **Verify** — Run `dotnet build` on the project. If fails, enter failure recovery.

### Failure Recovery (max 3 retries)

7a. Read build error → identify root cause.
7b. Fix the specific issue.
7c. Re-run `dotnet build`.
7d. After 3 failures → report error + diagnosis, ask for guidance.

### Rollback

If user cancels mid-implementation: `git checkout` all modified files. Report which files were reverted.

## Guardrails

- NEVER write an EF Core query without asking diagnostic questions first
- NEVER use Include on 2+ collections without AsSplitQuery
- NEVER return full entities from read-only queries — always project with Select
- NEVER omit AsNoTracking on read paths
- NEVER omit CancellationToken on async EF Core calls
- NEVER use SaveChanges inside a loop
- NEVER share DbContext across parallel tasks — use IDbContextFactory
- NEVER write unbounded list queries without pagination (Take/Skip or keyset)
- NEVER use string interpolation in FromSqlRaw — use FromSqlInterpolated
- NEVER skip compiled query consideration when frequency is "hot path"
- NEVER add 10k+ rows through AddRange — use SqlBulkCopy
- NEVER hold pessimistic locks across HTTP request boundaries
- NEVER enable UseLazyLoadingProxies — use explicit Include or Select
- NEVER use LIKE/Contains/ORDER BY/GROUP BY on Always Encrypted columns in LINQ — use search index or client-side filter
- NEVER filter on randomized-encryption columns server-side — only deterministic supports equality

## References

- `steering/preferences/stack/csharp/efcore-query-patterns.md` — decision matrices, patterns, concurrency rules
- `steering/preferences/stack/mssql/query-performance.md` — SQL-level index and query plan decisions
- `steering/preferences/stack/csharp/api-caching.md` — caching layer (cache before optimizing queries)
- `skills/efcore-antipattern-refactor.md` — companion skill for fixing existing EF Core issues
