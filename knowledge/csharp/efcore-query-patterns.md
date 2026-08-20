---
inclusion: manual
---

# EF Core Query Patterns & Guardrails

## Why This Exists

EF Core makes it trivially easy to write queries that work in development but collapse under production load — N+1 queries hiding behind lazy navigation properties, cartesian explosions from multiple collection Includes, unbounded result sets, and thread-safety violations from shared DbContext instances. Without a structured diagnostic process, developers (and AI agents) default to the simplest query shape and discover the performance cliff after deployment.

This document defines an interactive diagnostic framework that agents MUST follow before writing any EF Core LINQ query. The diagnostic determines the optimal pattern based on operation type, data volume, relationship depth, tracking needs, concurrency requirements, and execution frequency. Every combination of answers maps to a specific, prescriptive implementation pattern.

---

## 1. Interactive Diagnostic Questions

The agent MUST ask these questions before writing any EF Core query. Ask 2-3 per message to avoid overwhelming the user.

### Question 1: Is This Read-Only?

**Ask:** "Is this query read-only (no entity modification or SaveChanges needed)?"

| Answer | Implication |
|--------|-------------|
| Yes | Candidate for Dapper escape hatch (evaluate further). If staying EF Core: AsNoTracking mandatory, projection preferred. |
| No | EF Core required. Change tracking enabled. Evaluate concurrency model. |

If YES — proceed to the Dapper Escape Hatch evaluation (Section 2) before continuing.

### Question 2: What Operation Type?

**Ask:** "What operation? SELECT / INSERT / UPDATE / DELETE?"

| Answer | Pattern Domain |
|--------|---------------|
| SELECT | Section 3 (projections, includes, split queries, compiled queries) |
| INSERT | Section 4 (Add/AddRange/SqlBulkCopy based on volume) |
| UPDATE | Section 4 (fetch+modify, ExecuteUpdate, Dapper batch based on volume) |
| DELETE | Section 4 (Remove, ExecuteDelete, batch purge based on volume) |

### Question 3: Expected Row Volume?

**Ask:** "How many rows will this operation typically handle?"

| Answer | Implications |
|--------|-------------|
| Single entity (1) | Standard patterns. Find/FirstOrDefault for reads. Add/Remove for writes. |
| Small set (<100) | Standard patterns. List operations. AddRange for inserts. |
| Medium (100–10k) | Chunking required for inserts. ExecuteUpdate/Delete for mutations. Pagination required for reads. |
| Large (10k+) | SqlBulkCopy for inserts. Dapper batch for updates. Keyset pagination for reads. |

### Question 4: Relationship Depth?

**Ask:** "Does this query need related data? Flat entity, 1-level related, or multi-level nested collections?"

| Answer | Implications |
|--------|-------------|
| Flat entity (no relationships) | No Include needed. Simple query. |
| 1-level related (single navigation or one collection) | Include acceptable. Single query fine. |
| Multi-level nested (2+ collections or ThenInclude chains >2 deep) | AsSplitQuery mandatory for 2+ collections. Prefer Select projection over deep ThenInclude. |

### Question 5: Tracking Needs?

**Ask:** "Will you modify and save these entities, or is this read-only display?"

| Answer | Implications |
|--------|-------------|
| Read-only display / API response | AsNoTracking. Projection with Select preferred. |
| Will modify and SaveChanges | Tracked query (default). Concurrency token evaluation needed. |
| Need deduplication without tracking | AsNoTrackingWithIdentityResolution() |

### Question 6: Execution Frequency?

**Ask:** "How often does this query execute? One-off, per-request on a standard endpoint, hot path (>100 req/sec), or background job?"

| Answer | Implications |
|--------|-------------|
| One-off (admin action, migration) | No special optimization. Standard patterns. |
| Per-request, standard endpoint | Standard patterns. Consider compiled query if simple. |
| Hot path (>100 req/sec) | Compiled query recommended. Consider Dapper. Cache evaluation. |
| Background job | Standard patterns. Ensure CancellationToken. Chunking for large volumes. |

---

## 2. Dapper Escape Hatch

### When to Actively Recommend Dapper

If ALL of the following conditions are true, the agent MUST recommend Dapper before proceeding with EF Core:

| Condition | Check |
|-----------|-------|
| Read-only | No entity modification or SaveChanges needed |
| High-frequency | Hot path (>100 req/sec) OR per-request on a high-traffic endpoint |
| Flat projection | No navigation property traversal needed |
| Simple shape | Result maps to a DTO, not an entity graph |

**Agent phrasing when recommending Dapper:**

> "This is a strong Dapper candidate: it's read-only, high-frequency, and returns a flat projection. Dapper eliminates expression tree compilation overhead and change tracker allocation — you'll get ~2-5x throughput improvement on hot paths. Want me to write it with Dapper instead, or proceed with EF Core?"

### When to Stay with EF Core

If ANY of the following are true, stay with EF Core:

| Condition | Reason |
|-----------|--------|
| Needs change tracking | Will modify entities and call SaveChanges |
| Uses navigation properties | Include/ThenInclude for related data loading |
| Part of a unit of work | Transaction with other EF operations |
| Global query filters needed | Tenant isolation, soft delete filters applied by DbContext |
| Optimistic concurrency needed | RowVersion checking on SaveChanges |

---

## 3. SELECT Patterns

### 3a. Projection-First Rule (ALWAYS Apply)

**Rule:** Never load full entities for read-only operations. Always project to the exact shape needed.

```csharp
// ❌ Loads all 20 columns, enables change tracking, wastes memory
var patient = await db.Patients.FirstOrDefaultAsync(p => p.Id == id, ct);
return new PatientDto(patient.FirstName, patient.LastName, patient.Email);

// ✅ Only SELECTs 3 columns, no tracking, no wasted memory
var dto = await db.Patients
    .Where(p => p.Id == id)
    .Select(p => new PatientDto(p.FirstName, p.LastName, p.Email))
    .FirstOrDefaultAsync(ct);
```

**Why:** Projections eliminate tracking overhead, reduce network transfer, and prevent over-posting vulnerabilities. EF Core translates `Select()` to a targeted SQL SELECT — only requested columns are fetched.

### 3b. Include/ThenInclude Decision Matrix

| Collection Includes | Strategy | Rationale |
|--------------------|----------|-----------|
| 0 (flat or reference nav only) | Single query | No cartesian risk |
| 1 collection | Single query | Acceptable row duplication |
| 2+ collections | `AsSplitQuery()` MANDATORY | Prevents cartesian explosion |
| ThenInclude >2 levels deep | Prefer `Select()` projection | Deep joins are unreadable and fragile |

**Cartesian Explosion Example:**

```csharp
// ❌ CARTESIAN: 10 orders × 5 lines × 3 payments = 150 rows for 10 orders
var orders = await db.Orders
    .Include(o => o.Lines)        // Collection
    .Include(o => o.Payments)     // Collection — EXPLOSION
    .Where(o => o.CustomerId == customerId)
    .ToListAsync(ct);

// ✅ SPLIT: 3 separate queries, no row multiplication
var orders = await db.Orders
    .Include(o => o.Lines)
    .Include(o => o.Payments)
    .AsSplitQuery()
    .Where(o => o.CustomerId == customerId)
    .ToListAsync(ct);

// ✅ EVEN BETTER: Project only what you need
var orderDtos = await db.Orders
    .Where(o => o.CustomerId == customerId)
    .Select(o => new OrderDto(
        o.Id,
        o.Total,
        o.Lines.Select(l => new LineDto(l.ProductName, l.Quantity)).ToList(),
        o.Payments.Select(p => new PaymentDto(p.Amount, p.Method)).ToList()
    ))
    .ToListAsync(ct);
```

### 3c. AsNoTracking Rules

| Scenario | Method | Why |
|----------|--------|-----|
| Read-only display / API response | `.AsNoTracking()` | No snapshot allocation, ~30% faster |
| Read with potential duplicates in result | `.AsNoTrackingWithIdentityResolution()` | Deduplicates by PK without full tracking |
| Will modify + SaveChanges | Default (tracked) | Change tracker detects modifications |

```csharp
// ✅ Read path — always AsNoTracking
var patients = await db.Patients
    .AsNoTracking()
    .Where(p => p.Status == PatientStatus.Active)
    .Select(p => new PatientListItem(p.Id, p.FullName))
    .ToListAsync(ct);
```

### 3d. Compiled Queries

| Frequency | Recommendation |
|-----------|---------------|
| Hot path (>100 req/sec) | ALWAYS compile |
| Per-request, simple query (no dynamic filters) | CONSIDER compiling |
| One-off, background job | SKIP — compilation overhead not justified |
| Query has dynamic/conditional Includes or filters | SKIP — compiled queries don't support dynamic shapes |

```csharp
// ✅ Compiled query for hot path — eliminates expression tree cost per call
private static readonly Func<AppDbContext, Guid, CancellationToken, Task<PatientDto?>> _getById =
    EF.CompileAsyncQuery((AppDbContext db, Guid id, CancellationToken ct) =>
        db.Patients
            .Where(p => p.Id == id)
            .Select(p => new PatientDto(p.FirstName, p.LastName, p.Email))
            .FirstOrDefault());

// Usage
var dto = await _getById(db, patientId, ct);
```

**Compiled Query Limitations:**
- Cannot use `Include()` (use projections instead)
- Cannot have conditional/dynamic LINQ composition
- Parameters must be scalar (no lists/arrays)
- EF Core 8+: improved compiled query support with better LINQ translation

### 3e. Pagination (MANDATORY for List Queries)

**Rule:** NEVER return unbounded result sets. All list/collection queries MUST be paginated.

| Dataset Size | Strategy | Why |
|-------------|----------|-----|
| Small (known upper bound <1000) | Offset/Skip-Take | Simple, page numbers possible |
| Large or growing | Keyset pagination | No row skipping on concurrent inserts, O(1) seek vs O(n) skip |

```csharp
// ✅ Offset pagination (simple, supports page numbers)
var page = await db.Patients
    .AsNoTracking()
    .Where(p => p.Status == PatientStatus.Active)
    .OrderBy(p => p.LastName)
    .Skip((pageNumber - 1) * pageSize)
    .Take(pageSize)
    .Select(p => new PatientListItem(p.Id, p.FullName))
    .ToListAsync(ct);

// ✅ Keyset pagination (performant for large datasets)
var page = await db.Patients
    .AsNoTracking()
    .Where(p => p.Status == PatientStatus.Active)
    .Where(p => p.Id > lastSeenId) // Keyset cursor
    .OrderBy(p => p.Id)
    .Take(pageSize)
    .Select(p => new PatientListItem(p.Id, p.FullName))
    .ToListAsync(ct);
```

---

## 4. PHI / Always Encrypted Columns

### 4a. Diagnostic Question

**Ask:** "Do any columns in this query contain PHI (encrypted via Always Encrypted)? If so, which columns, and is the encryption deterministic or randomized? How many rows exist BEFORE the PHI filter is applied — can you reduce the set with non-encrypted columns first (e.g., OrganizationId, Status, date range)?"

### 4b. Allowed Operations by Encryption Type

| Operation | Deterministic | Randomized | Unencrypted |
|-----------|:---:|:---:|:---:|
| Equality filter (`WHERE col = @val`) | ✅ Server-side | ❌ Client-side or search index | ✅ |
| Pattern match (LIKE, Contains, StartsWith) | ❌ | ❌ | ✅ |
| ORDER BY | ❌ | ❌ | ✅ |
| GROUP BY / aggregation | ❌ | ❌ | ✅ |
| Range (>, <, BETWEEN) | ❌* | ❌ | ✅ |
| JOIN ON encrypted column | ✅ (same CEK) | ❌ | ✅ |
| String functions (CONCAT, UPPER) | ❌ | ❌ | ✅ |
| Projection (SELECT col) | ✅ Decrypted by driver | ✅ Decrypted by driver | ✅ |

*\*Enclave-based Always Encrypted (SQL Server 2019+ with VBS/SGX) supports range comparisons.*

**Key clarification:** The "client" in Always Encrypted is the API server, not the browser. The ADO.NET driver with `Column Encryption Setting=Enabled` encrypts parameters and decrypts results transparently. Developers pass plain values — the driver handles cryptographic operations.

### 4c. Scale-Based Strategy Decision Matrix

| Pre-filtered set size | Encryption Type | Strategy |
|----------------------|-----------------|----------|
| <10k (after org/status/date filter) | Any | Fetch superset + client-side filter on decrypted values |
| 10k–100k | Deterministic | Server-side equality filter (driver encrypts param) |
| 10k–100k | Randomized | Search index (Redis or Elasticsearch) → ID list → SQL query |
| 100k+ | Deterministic | Server-side equality on SQL. Pattern matching via search index. |
| 100k+ | Randomized | Search index required (Redis or Elasticsearch) |
| Any size + fuzzy/phonetic/autocomplete | Any | Search index required (RediSearch or Elasticsearch) |

### 4d. Pattern: Superset Fetch + Client-Side Filter (Small Sets)

Use when the pre-filtered set (after non-PHI WHERE clauses) is <10k rows.

```csharp
// ✅ Filter server-side on non-encrypted columns, then client-side on PHI
var orgFilter = tenantContext.OrganizationId;
var fetchSize = pageSize * 5; // Larger window for client-side filtering

var candidates = await db.Patients
    .AsNoTracking()
    .Where(p => p.OrganizationId == orgFilter)
    .Where(p => p.Status == PatientStatus.Active)
    .OrderBy(p => p.CreatedAt)
    .Take(fetchSize)
    .Select(p => new { p.Id, p.FirstName, p.LastName, p.Email, p.CreatedAt })
    .ToListAsync(ct);

// Client-side search on decrypted PHI fields
var filtered = candidates
    .Where(p => p.LastName.Contains(searchTerm, StringComparison.OrdinalIgnoreCase))
    .Take(pageSize)
    .ToList();
```

**Limitation:** This pattern degrades when the search term is selective (few matches in a large set). If the superset fetch must scan too many rows to fill a page, switch to a search index strategy.

### 4e. Pattern: Search Index (Redis) → ID List → SQL Query

Use when pre-filtered set exceeds 10k rows or you need pattern matching/fuzzy search on encrypted columns.

**Write Path (keep index in sync):**

```csharp
// After SaveChanges — update Redis search index with decrypted PHI
// Triggered via domain event, Wolverine handler, or change feed
public async Task Handle(PatientCreated @event, IConnectionMultiplexer redis, CancellationToken ct)
{
    var db = redis.GetDatabase();
    await db.HashSetAsync($"patient:{@event.Id}", new HashEntry[]
    {
        new("firstName", @event.FirstName),  // Decrypted value
        new("lastName", @event.LastName),
        new("email", @event.Email),
        new("orgId", @event.OrganizationId.ToString())
    });
}
```

**Read Path (RediSearch — supports prefix, fuzzy, full-text):**

```csharp
// 1. Search Redis for matching patient IDs
// FT.SEARCH idx:patients "@lastName:smith* @orgId:{orgId}" RETURN 0
var searchResults = await SearchRedisAsync(searchTerm, organizationId, ct);
var patientIds = searchResults.Select(r => r.Id).ToList();

if (patientIds.Count == 0) return EmptyResult();

// 2. Query SQL with the filtered IDs for full data + related entities
var patients = await db.Patients
    .AsNoTracking()
    .Where(p => patientIds.Contains(p.Id))
    .Select(p => new PatientDto(p.Id, p.FirstName, p.LastName, p.Email))
    .ToListAsync(ct);

// 3. For subqueries (e.g., shift history for matched patients)
var shifts = await db.ShiftHistory
    .AsNoTracking()
    .Where(s => patientIds.Contains(s.PatientId))
    .OrderByDescending(s => s.ShiftDate)
    .ToListAsync(ct);
```

**Redis Search Index Setup (RediSearch module):**

```
FT.CREATE idx:patients ON HASH PREFIX 1 patient:
  SCHEMA firstName TEXT SORTABLE
         lastName TEXT SORTABLE
         email TEXT
         orgId TAG
```

**Sorted Set alternative (exact + prefix only, no fuzzy):**

```csharp
// Write: ZADD idx:lastname:{orgId} 0 "smith:{patientId}"
// Read: ZRANGEBYLEX idx:lastname:{orgId} "[smith" "[smith\xff"
```

### 4f. Pattern: Search Index (Elasticsearch) → ID List → SQL Query

Use when you need advanced search capabilities: fuzzy matching, phonetic search (Soundex/Metaphone), relevance scoring, or multi-field weighted search across encrypted columns.

**Write Path (keep index in sync):**

```csharp
// After SaveChanges — index decrypted PHI in Elasticsearch
// Triggered via domain event or outbox pattern
public async Task Handle(PatientCreated @event, IElasticClient elastic, CancellationToken ct)
{
    await elastic.IndexAsync(new PatientSearchDocument
    {
        Id = @event.Id,
        FirstName = @event.FirstName,   // Decrypted value
        LastName = @event.LastName,
        Email = @event.Email,
        OrganizationId = @event.OrganizationId
    }, idx => idx.Index("patients"), ct);
}
```

**Read Path:**

```csharp
// 1. Search Elasticsearch for matching patient IDs
var searchResponse = await elastic.SearchAsync<PatientSearchDocument>(s => s
    .Index("patients")
    .Query(q => q
        .Bool(b => b
            .Must(
                m => m.MultiMatch(mm => mm
                    .Query(searchTerm)
                    .Fields(f => f
                        .Field(p => p.LastName, boost: 3)
                        .Field(p => p.FirstName, boost: 2)
                        .Field(p => p.Email))
                    .Fuzziness(Fuzziness.Auto)),
                m => m.Term(t => t
                    .Field(p => p.OrganizationId)
                    .Value(organizationId)))
        ))
    .Size(pageSize)
    .Source(false) // Only return IDs, not full documents
    , ct);

var patientIds = searchResponse.Hits.Select(h => h.Id).ToList();

// 2. Query SQL with the filtered IDs
var patients = await db.Patients
    .AsNoTracking()
    .Where(p => patientIds.Contains(p.Id))
    .Select(p => new PatientDto(p.Id, p.FirstName, p.LastName, p.Email))
    .ToListAsync(ct);
```

**Elasticsearch Index Mapping:**

```json
{
  "mappings": {
    "properties": {
      "firstName": { "type": "text", "analyzer": "standard", "fields": { "keyword": { "type": "keyword" } } },
      "lastName": { "type": "text", "analyzer": "standard", "fields": { "keyword": { "type": "keyword" } } },
      "email": { "type": "text", "analyzer": "email_analyzer" },
      "organizationId": { "type": "keyword" }
    }
  }
}
```

### 4g. Redis vs Elasticsearch Decision

| Concern | Redis (RediSearch) | Elasticsearch |
|---------|-------------------|---------------|
| **Latency** | Sub-millisecond | Low milliseconds (1-10ms) |
| **Fuzzy/phonetic search** | Basic (Levenshtein via FT.SEARCH) | Advanced (phonetic analyzers, Soundex, Metaphone, n-grams) |
| **Relevance scoring** | Basic | Full BM25 + custom boosting |
| **Multi-field weighted search** | Supported | Superior (field boosting, cross-field queries) |
| **Autocomplete/suggest** | Supported | Superior (completion suggester, edge n-grams) |
| **Operational complexity** | Lower (single Redis instance, module) | Higher (cluster, shard management, JVM tuning) |
| **Memory usage** | In-memory only | Disk-backed with memory caching |
| **Dataset size** | Best <10M documents | Handles 100M+ documents |
| **Already in stack?** | Check if Redis is deployed | Check if ES/OpenSearch is deployed |
| **HIPAA audit** | Manual (log access in application) | Built-in audit logging |

**Choose Redis when:** Already using Redis, dataset <10M records, need sub-ms latency, simple search (exact + prefix + basic fuzzy).

**Choose Elasticsearch when:** Need advanced NLP (phonetic, synonyms, stemming), multi-field relevance scoring, dataset >10M, need built-in audit logging, or already have ES/OpenSearch in the stack.

### 4h. Search Index Security Requirements

Regardless of Redis or Elasticsearch, the search index contains decrypted PHI:

| Requirement | Implementation |
|-------------|---------------|
| Encryption at rest | Redis: enable RDB/AOF encryption. ES: encrypted-at-rest nodes. |
| Encryption in transit | TLS connections mandatory |
| Access control | Redis ACLs or ES role-based access. Only the API service connects. |
| Audit logging | Log every search query with user identity + timestamp |
| Data lifecycle | Delete from index when patient is purged from SQL |
| Backup security | Index backups encrypted, same retention as SQL backups |
| Network isolation | Same network segment as API — never exposed publicly |
| Consistency | Eventual consistency acceptable. Write-through or event-driven sync. |
| Failure mode | If index unavailable, degrade to superset-fetch pattern (if set size permits) or return error |

### 4i. Keeping the Search Index in Sync

| Strategy | When | Trade-off |
|----------|------|-----------|
| **Write-through** (update index in same handler as SaveChanges) | Low volume, consistency matters | Couples write path to search infra availability |
| **Domain event** (Wolverine/MediatR handler reacts to entity event) | Medium volume, decoupled | Eventual consistency (milliseconds delay) |
| **Transactional outbox** (outbox pattern with Wolverine) | High reliability required | Most complex, but guarantees delivery |
| **Change Data Capture** (Debezium on SQL Server) | Very high volume, minimal app changes | Operational complexity, latency (seconds) |

```csharp
// ✅ Recommended: Domain event via Wolverine cascading
// SaveChanges fires PatientCreated → handler updates search index
// Outbox ensures delivery even if Redis/ES is temporarily down
public static async Task Handle(
    PatientCreated @event,
    ISearchIndexService searchIndex,
    CancellationToken ct)
{
    await searchIndex.IndexPatientAsync(@event.Id, @event.FirstName,
        @event.LastName, @event.Email, @event.OrganizationId, ct);
}
```

---

## 5. Mutation Patterns (INSERT / UPDATE / DELETE)

### 5a. Volume-Based Decision Matrix

| Volume | INSERT | UPDATE | DELETE |
|--------|--------|--------|--------|
| **Single (1)** | `Add` + `SaveChangesAsync` | Fetch + modify + `SaveChangesAsync` | `Remove` + `SaveChangesAsync` OR `ExecuteDeleteAsync` |
| **Small (<100)** | `AddRange` + `SaveChangesAsync` | Fetch all + modify + `SaveChangesAsync` | `ExecuteDeleteAsync` with `Where` |
| **Medium (100–10k)** | `AddRange` + chunking (500) + `ChangeTracker.Clear()` | `ExecuteUpdateAsync` (no entity loading) | `ExecuteDeleteAsync` (no entity loading) |
| **Large (10k+)** | `SqlBulkCopy` with DataTable | Dapper `Execute` with batched params | `ExecuteDeleteAsync` or Dapper batched |

### 5b. SaveChanges Rules

```csharp
// ❌ CRITICAL: SaveChanges in a loop — 1000 inserts = 1000 round-trips
foreach (var item in items)
{
    db.Patients.Add(item);
    await db.SaveChangesAsync(ct); // N round-trips!
}

// ✅ Single SaveChanges — EF Core batches the INSERT statements
db.Patients.AddRange(items);
await db.SaveChangesAsync(ct); // 1 round-trip, batched SQL

// ✅ Chunked for medium volumes (avoids change tracker bloat)
foreach (var chunk in items.Chunk(500))
{
    db.Patients.AddRange(chunk);
    await db.SaveChangesAsync(ct);
    db.ChangeTracker.Clear(); // Release tracked entities from memory
}
```

### 5c. ExecuteUpdate / ExecuteDelete (EF Core 7+)

Set-based operations that execute a single SQL statement without loading entities. Bypasses change tracker, interceptors, and entity events.

```csharp
// ✅ Bulk UPDATE — single SQL statement, no entities loaded
var affected = await db.Patients
    .Where(p => p.Status == PatientStatus.Active)
    .Where(p => p.LastAppointmentAt < cutoffDate)
    .ExecuteUpdateAsync(setters => setters
        .SetProperty(p => p.Status, PatientStatus.Inactive)
        .SetProperty(p => p.UpdatedAt, DateTime.UtcNow), ct);

// ✅ Bulk DELETE — single SQL statement
var deleted = await db.Patients
    .Where(p => p.Status == PatientStatus.Inactive)
    .Where(p => p.UpdatedAt < purgeDate)
    .ExecuteDeleteAsync(ct);
```

**Important:** ExecuteUpdate/Delete:
- Does NOT fire `SaveChanges` interceptors or domain events
- Does NOT update the change tracker (stale entities if already loaded)
- Does NOT validate entity-level business rules
- DOES respect global query filters (tenant isolation still applies)

### 5d. SqlBulkCopy (10k+ Rows)

For high-volume inserts where EF Core's change tracker becomes a bottleneck:

```csharp
// ✅ 10k+ rows — bypass EF entirely for raw insert throughput
var dataTable = new DataTable();
dataTable.Columns.Add("Id", typeof(Guid));
dataTable.Columns.Add("FirstName", typeof(string));
// ... map all columns

foreach (var item in items)
    dataTable.Rows.Add(item.Id, item.FirstName, /* ... */);

using var connection = new SqlConnection(connectionString);
await connection.OpenAsync(ct);
using var bulkCopy = new SqlBulkCopy(connection)
{
    DestinationTableName = "Patients",
    BatchSize = 5000
};
await bulkCopy.WriteToServerAsync(dataTable, ct);
```

**Trade-offs:**
- No validation, no events, no change tracker
- Column mapping must exactly match database schema
- No navigation property handling — flat table only
- Maximum throughput for pure insert volume

### 5e. EF Core Version Notes

| Feature | EF Core 7 | EF Core 8 | EF Core 9+ |
|---------|:---------:|:---------:|:----------:|
| ExecuteUpdate/Delete | ✓ | ✓ | ✓ (complex expressions) |
| ExecuteUpdate with subqueries | — | ✓ | ✓ |
| Bulk SaveChanges batching | Basic | Improved | Further improved |
| Complex type in ExecuteUpdate | — | — | ✓ |

---

## 6. Concurrency

### 6a. DbContext Thread Safety (ALWAYS Apply)

**Rule: DbContext is NOT thread-safe.** Never share a DbContext instance across concurrent operations.

| Scenario | Safe? | Solution |
|----------|:-----:|----------|
| Sequential awaits on same DbContext | ✅ | Single thread of execution — no issue |
| `Task.WhenAll` with same DbContext | ❌ | Separate DbContext per task via `IDbContextFactory` |
| `Parallel.ForEachAsync` with shared DbContext | ❌ | Create new DbContext per iteration |
| Background service injecting DbContext | ❌ | Use `IServiceScopeFactory` or `IDbContextFactory` |
| `SaveChangesAsync` while streaming results | ❌ | Complete all reads first, then SaveChanges |
| Multiple open readers (MARS) | ⚠️ | Prefer `ToListAsync()` to materialize, or enable MARS |

**IDbContextFactory Pattern (Parallel Operations):**

```csharp
// ✅ Safe parallel operations — each task gets its own DbContext
public class BatchProcessor
{
    private readonly IDbContextFactory<AppDbContext> _dbFactory;

    public async Task ProcessInParallelAsync(IEnumerable<Guid> ids, CancellationToken ct)
    {
        await Parallel.ForEachAsync(ids,
            new ParallelOptions { MaxDegreeOfParallelism = 4, CancellationToken = ct },
            async (id, token) =>
            {
                await using var db = await _dbFactory.CreateDbContextAsync(token);
                var entity = await db.Orders.FindAsync(new object[] { id }, token);
                // process entity within this DbContext's scope
            });
    }
}
```

**MARS (Multiple Active Result Sets):**

```
// Connection string — enable only when truly needed
Server=...;Database=...;MultipleActiveResultSets=True
```

**Recommendation:** Prefer materializing with `ToListAsync()` over MARS. MARS adds connection state complexity and can mask N+1 patterns.

```csharp
// ❌ Requires MARS — two open readers simultaneously
var orders = db.Orders.AsAsyncEnumerable();
await foreach (var order in orders)
{
    var payments = await db.Payments.Where(p => p.OrderId == order.Id).ToListAsync(ct);
}

// ✅ No MARS needed — materialize first, then query
var orders = await db.Orders.ToListAsync(ct);
foreach (var order in orders)
{
    var payments = await db.Payments.Where(p => p.OrderId == order.Id).ToListAsync(ct);
}

// ✅ BEST — single query with Include or projection (no N+1)
var orders = await db.Orders
    .Include(o => o.Payments)
    .ToListAsync(ct);
```

### 6b. Database-Level Concurrency

#### Optimistic Concurrency (Preferred for Most Apps)

Use when conflicts are rare (typical CRUD). The database rejects updates where the RowVersion has changed since the entity was read.

**Configuration:**

```csharp
// Entity
public class Order
{
    public Guid Id { get; set; }
    public decimal Total { get; set; }
    public byte[] RowVersion { get; set; } = [];
}

// OnModelCreating
modelBuilder.Entity<Order>(entity =>
{
    entity.Property(e => e.RowVersion)
        .IsRowVersion(); // SQL Server timestamp/rowversion
});
```

**Handling Conflicts:**

```csharp
public async Task UpdateOrderAsync(Guid id, decimal newTotal, CancellationToken ct)
{
    const int maxRetries = 3;
    for (var attempt = 0; attempt < maxRetries; attempt++)
    {
        try
        {
            var order = await db.Orders.FindAsync(new object[] { id }, ct)
                ?? throw new NotFoundException(id);
            order.Total = newTotal;
            await db.SaveChangesAsync(ct);
            return;
        }
        catch (DbUpdateConcurrencyException ex)
        {
            if (attempt == maxRetries - 1) throw;

            // Reload with current database values
            var entry = ex.Entries.Single();
            await entry.ReloadAsync(ct);
            // Loop retries with fresh RowVersion
        }
    }
}
```

#### Pessimistic Locking (Rare — Financial/Inventory)

Use when conflicts are frequent and optimistic retries would be wasteful (e.g., inventory decrement under load).

```csharp
// ✅ Pessimistic lock via raw SQL — holds UPDLOCK for duration of transaction
await using var transaction = await db.Database.BeginTransactionAsync(ct);

var inventory = await db.Inventory
    .FromSqlInterpolated($"""
        SELECT * FROM Inventory WITH (UPDLOCK, ROWLOCK)
        WHERE ProductId = {productId}
        """)
    .FirstOrDefaultAsync(ct);

inventory!.Quantity -= requestedQuantity;
await db.SaveChangesAsync(ct);
await transaction.CommitAsync(ct);
```

**Rules:**
- Keep lock duration minimal (milliseconds, not seconds)
- NEVER hold locks across HTTP request boundaries
- Always use within an explicit transaction
- Always specify ROWLOCK to minimize lock escalation

#### Isolation Levels

| Level | Use When | Trade-off |
|-------|----------|-----------|
| Read Committed (default) | Most CRUD operations | Phantom reads possible, minimal blocking |
| Snapshot | Need repeatable reads without blocking writers | Higher tempdb usage, row versioning overhead |
| Read Committed Snapshot (RCSI) | Want Read Committed behavior without reader-writer blocking | Same as snapshot but at statement level |
| Serializable | Almost never — only for provable correctness requirements | Maximum blocking, deadlock-prone |

```csharp
// ✅ Snapshot isolation for report that needs consistent point-in-time view
await using var transaction = await db.Database
    .BeginTransactionAsync(System.Data.IsolationLevel.Snapshot, ct);
// All reads in this transaction see a consistent snapshot
```

#### Deadlock Prevention

| Rule | Why |
|------|-----|
| Access tables in consistent alphabetical/logical order | Prevents circular wait |
| Keep transactions short (milliseconds) | Reduces lock hold time |
| Add indexes to filter columns | Reduces rows locked (row-level vs table-level) |
| Use `SET DEADLOCK_PRIORITY LOW` on expendable operations | Let the important operation win |
| Implement retry logic for SqlException 1205 | Deadlock victim should retry |

```csharp
// ✅ Retry logic for deadlock victims
public static async Task WithDeadlockRetryAsync(
    Func<CancellationToken, Task> operation,
    CancellationToken ct,
    int maxRetries = 3)
{
    for (var attempt = 0; attempt < maxRetries; attempt++)
    {
        try
        {
            await operation(ct);
            return;
        }
        catch (SqlException ex) when (ex.Number == 1205) // Deadlock victim
        {
            if (attempt == maxRetries - 1) throw;
            await Task.Delay(TimeSpan.FromMilliseconds(50 * (attempt + 1)), ct);
        }
    }
}
```

---

## 7. Anti-Patterns Quick Reference

| # | Anti-Pattern | Detection Signal | Severity | One-Line Fix |
|---|---|---|---|---|
| 1 | N+1 Queries | Navigation property access in loop without Include | Critical | `Include()` or `Select()` projection |
| 2 | Cartesian Explosion | 2+ collection Includes without SplitQuery | Critical | `AsSplitQuery()` |
| 3 | Full Entity Load for Display | Returning DbSet entities to API without Select | High | `.Select(x => new Dto(...))` |
| 4 | Tracked Read-Only Queries | No AsNoTracking on read paths | High | `.AsNoTracking()` |
| 5 | SaveChanges in Loop | SaveChanges inside foreach | Critical | `AddRange` + single `SaveChanges` |
| 6 | Unbounded Queries | No Take/Skip on list queries | High | Always paginate |
| 7 | ToList Before Filter | `.ToList().Where()` | Critical | `.Where().ToListAsync()` |
| 8 | DbContext Shared Across Threads | `Task.WhenAll` with same context | Critical | `IDbContextFactory` per task |
| 9 | Missing CancellationToken | Async EF calls without ct | Medium | Pass ct to all async methods |
| 10 | Hot Path Without Compiled Query | >100 req/sec without `EF.CompileAsyncQuery` | Medium | Compile the query |
| 11 | String Interpolation in FromSqlRaw | `FromSqlRaw($"...{userInput}")` | Critical | `FromSqlInterpolated` |
| 12 | Lazy Loading Enabled | `UseLazyLoadingProxies()` | High | Remove, use explicit Include/Select |
| 13 | Missing Concurrency Token | Update without RowVersion on contested entity | Medium | Add `IsRowVersion()` |
| 14 | Large Batch via AddRange | 10k+ rows through change tracker | High | SqlBulkCopy |
| 15 | No Index on Filtered Column | FirstOrDefault on non-indexed column | Medium | Add `HasIndex` in OnModelCreating |

---

## 8. EF Core Version Compatibility

| Feature | EF Core 7 | EF Core 8 | EF Core 9+ |
|---------|:---------:|:---------:|:----------:|
| ExecuteUpdate/Delete | ✓ | ✓ | ✓ (enhanced) |
| Compiled Queries | ✓ | ✓ | ✓ |
| JSON Columns | Basic | ✓ | ✓ (enhanced) |
| Bulk operations (native) | — | ✓ | ✓ |
| Complex type support | — | ✓ | ✓ |
| Sentinel values | — | ✓ | ✓ |
| LINQ improvements | — | — | ✓ |
| ExecuteUpdate with subqueries | — | ✓ | ✓ |
| Primitive collections | — | ✓ | ✓ |
| Better GroupBy translation | — | — | ✓ |

---

## References

- `steering/preferences/stack/mssql/query-performance.md` — SQL-level optimization (index decisions, execution plan analysis, DMV diagnostics)
- `steering/preferences/stack/csharp/api-caching.md` — cache before you optimize the query (response caching, output caching, Redis, IMemoryCache)
- `skills/efcore-antipattern-refactor.md` — reactive: find and fix existing EF Core anti-patterns in code
- `skills/efcore-query-author.md` — proactive: interactive skill that uses this steering doc to generate correct queries
- Future: `steering/preferences/stack/csharp/efcore-transactions.md` — transaction management patterns (BeginTransaction, ExecutionStrategy retry, TransactionScope anti-patterns)
