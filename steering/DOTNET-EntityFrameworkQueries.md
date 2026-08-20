---
inclusion: manual
fileMatchPattern: [
  "**/*Controller.cs",
  "**/*Endpoint.cs",
  "**/*Endpoints.cs",
  "**/*Query.cs", 
  "**/*QueryHandler.cs", 
  "**/*Repository.cs", 
  "**/*Specification.cs", 
  "**/*Spec.cs", 
  "**/Features/**/*.cs",
  "**/*DbContext.cs"
]
---
# EF Core & Architecture Steering Protocol

## 1. Agent Diagnostic Mandate & Fallbacks

* **Mandatory Diagnostic Interception:** DO NOT generate data access logic blindly. You MUST ask targeted questions regarding Operation constraints, API type (default to CQRS), Volume, Frequency, and PHI. Use the responses to explicitly lock in the correct architectural data pattern (e.g., Dapper, Staging Tables, Split Queries) *before* writing any code.
* **Scope Enforcement:** Verify file path context. If in `*Controller.cs` or `*Endpoint.cs`, refuse raw LINQ generation and instruct delegation to a Handler, Repository, or Feature slice.

## 2. Execution & Query Guardrails

* **Dapper Escape Hatch:** Recommend Dapper over EF Core ONLY IF the query is read-only, high-frequency (>100 req/sec), requires a flat projection, and maps to a simple DTO.
* **Read Constraints:** `.AsNoTracking()` and `.Select(dto)` are MANDATORY for API responses. Unbounded queries are forbidden (enforce Offset or Keyset pagination).
* **Relationship Limits:** `.AsSplitQuery()` is MANDATORY for 2+ collections. Deep `.ThenInclude()` chains are forbidden (use direct projections).
* **Mutation Thresholds:** 
  * **< 1,000 rows:** Use standard tracked operations (`Add`, `AddRange`, `Remove`) + `SaveChangesAsync()`.
  * **1,000 – 10,000 rows:** Use set-based `ExecuteUpdateAsync` or `ExecuteDeleteAsync` (bypasses change tracker).
  * **10,000+ rows:** Bypass EF Core. Use `SqlBulkCopy` for pure inserts, or the **Staging Table Pattern** (bulk load to `#TempTable` + raw SQL JOIN) for mass updates/upserts.
* **CQRS Mutations:** For asynchronous write operations, save the entity in a "pending" state and use the Transactional Outbox pattern to publish an integration event to the message queue. DO NOT couple data-access logic directly to websocket/SignalR pushes.

## 3. Security, Tenancy & Auditing

* **PHI Logging:** DO NOT serialize entity state in `catch` blocks (especially `DbUpdateConcurrencyException`/`SqlException`). Log only `Entity.Id` and the exception message.
* **Dapper Filter Trap:** When using Dapper, manually append multi-tenancy (`TenantId`) and soft-delete (`IsDeleted = 0`) WHERE clauses, as it bypasses EF Global Query Filters.
* **ExecuteUpdate Audit Trap:** Before using `ExecuteUpdate/Delete`, verify if the entity requires audit logging (e.g., `UpdatedAt`). If so, manually set audit fields in the `.SetProperty()` chain or revert to tracked mutations.

### Cross-Database Encryption (SQL Server vs. PostgreSQL)

* **Driver-Specific Behavior:** You CANNOT assume transparent encryption applies across database engines. While SQL Server's `Microsoft.Data.SqlClient` handles Always Encrypted transparently, PostgreSQL's `Npgsql` driver does not.
* **PostgreSQL / Agnostic Fallback:** When writing encryption logic for PostgreSQL or cross-database implementations, you MUST implement Application-Level Encryption (ALE) using EF Core Value Converters (encrypting in API memory before passing to the driver).

```csharp
// ✅ CORRECT: Database-agnostic Application-Level Encryption via Value Converters
protected override void OnModelCreating(ModelBuilder modelBuilder)
{
    var encryptionConverter = new ValueConverter<string, string>(
        plainText => _cryptoProvider.Encrypt(plainText),
        cipherText => _cryptoProvider.Decrypt(cipherText)
    );

    modelBuilder.Entity<Patient>()
        .Property(p => p.SocialSecurityNumber)
        .HasConversion(encryptionConverter);
}

```

* **Anti-patterns:** Using database-side cryptographic extensions (like `pgcrypto`) directly in EF Core raw SQL; assuming Value Converters bypass encrypted sorting rules.
* **Telemetry Metrics:** Track the CPU overhead and execution latency of `_cryptoProvider` operations during `DbContext` materialization to spot memory/CPU bottlenecks.
* **Other Design Options:** If cross-database compatibility is required, offload encrypted sorting and fuzzy searching entirely to a secure external Search Index (Elasticsearch or Redis), or use a standardized library like `EntityFrameworkCore.DataEncryption`.

### Encrypted Sorting & Filtering Guardrail

* **Encrypted Sorting & Complex Filtering:** Relational databases cannot sort or perform pattern/range matching on encrypted columns without exposing plaintext keys. You MUST materialize a pre-filtered subset of data into memory using `.ToListAsync()` BEFORE applying `.OrderBy()` or complex `.Where()` clauses to the decrypted properties.

```csharp
// ❌ CRASHES: Database cannot evaluate sorts or patterns on encrypted columns
var badSort = await db.Patients
    .Where(p => p.OrganizationId == orgId)
    .OrderBy(p => p.SocialSecurityNumber) 
    .ToListAsync(ct);

// ✅ CORRECT: Materialize first via API, then sort/filter in memory
var patients = await db.Patients
    .Where(p => p.OrganizationId == orgId) 
    .ToListAsync(ct);

var goodSort = patients
    .Where(p => p.LastName.StartsWith(searchTerm)) 
    .OrderBy(p => p.SocialSecurityNumber) 
    .ToList();

```

* **Anti-patterns:** Passing string constants into queries against encrypted columns (use variables for parameterization); Executing `.ToListAsync()` without a prior unencrypted `Where` clause.
* **Telemetry Metrics:** Track the list count of data sets materialized into API memory before client-side sorting/filtering is applied. Trigger a warning alert if the pre-filtered set exceeds 5,000 items.

### Encrypted Pagination Limitations

* **Memory-Bound Pagination:** When a list endpoint requires sorting by an encrypted column, SQL-level `.Skip()` and `.Take()` are mathematically impossible. You must materialize the *entire* pre-filtered result set into memory first, sort it, and then apply `Skip/Take` in memory.

```csharp
// ❌ WRONG: Paginates before sorting. Returns a random page, then sorts that page.
var badPagination = await db.Patients
    .Where(p => p.OrganizationId == orgId)
    .Take(50) 
    .ToListAsync(ct);

// ✅ CORRECT (Small datasets only): Materialize, sort, then paginate in memory
var allCandidates = await db.Patients
    .Where(p => p.OrganizationId == orgId)
    .ToListAsync(ct);

var page = allCandidates
    .OrderBy(p => p.SocialSecurityNumber) 
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize)
    .ToList();

```

* **Anti-patterns:** Applying `.Skip().Take()` to the `IQueryable` chain before materializing when sorting by an encrypted field; Attempting keyset pagination on randomized encrypted columns.
* **Telemetry Metrics:** Track the duration of the memory-bound pagination operation. Alert on latency spikes.
* **Other Design Options:** For large datasets (>10k rows), query an external Search Index (Redis/Elasticsearch) to return paginated `PatientId`s, then use EF Core to fetch using `.Where(p => ids.Contains(p.Id))`.

## 4. Concurrency & Transactions

* **Thread Isolation:** `DbContext` is NOT thread-safe. Mandate `IDbContextFactory` for parallel execution. Never share context across `Task.WhenAll`.
* **Locking & Retries:** Enforce `[IsRowVersion]` for optimistic concurrency. Catch `DbUpdateConcurrencyException` and `SqlException` 1205 (deadlocks) with exponential backoff retries.
* **Outbox Transactions:** When using Wolverine for domain events, DO NOT manually call `BeginTransactionAsync`. Rely on Wolverine's EF Core outbox middleware to manage the transaction boundary.

## 5. Strict Anti-Patterns & Corrective Measures

| Anti-Pattern | Detection Signal | Mandatory Corrective Measure |
| --- | --- | --- |
| **N+1 Queries** | Navigation property accessed in a loop | Implement `.Include()` or `.Select()` |
| **Loop Mutations** | `SaveChanges` placed inside a loop | Batch via `.AddRange()` + single save |
| **Client-Side Eval** | Calling `.ToList().Where(...)` | Move `.Where()` before materialization |
| **Cartesian Joins** | 2+ collection Includes without split | Apply `.AsSplitQuery()` |
| **Memory Bloat** | Returning tracked entities for display | Append `.AsNoTracking()` and project |
| **Leaky Architecture** | `DbContext` injected into a Controller | Isolate context to Handlers/Repos/Features |
| **Unsafe SQL** | Unsanitized `FromSqlRaw` interpolation | Switch to `FromSqlInterpolated` |
| **Active Readers** | Sequential reads without MARS | Materialize lists before subsequent queries |
| **Generic Globs** | File match patterns using `**/*.cs` | Scope globs to architectural markers |
| **Missing Exists Clause** | Raw SQL Staging Table Upsert lacking a duplicate check | Qualify `INSERT` queries with `WHERE NOT EXISTS` condition to ensure idempotency |

* **Telemetry:** Track query duration (`DbCommandInterceptor`, alert >200ms) and change tracker size (alert >1000 entities per request). Track the ratio of UPDATE vs. INSERT operations per batch to detect malfunctioning upstream message retry loops.
* **Design Options:** Implement caching (Redis/IMemoryCache) before heavy SQL optimization. Apply `EF.CompileAsyncQuery` to static hot-path reads.
