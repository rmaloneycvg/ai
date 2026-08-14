---
inclusion: manual
---

# EF Core Anti-Pattern Catalog

## Why This Exists

This catalog defines the detection signatures and fix patterns used by the `efcore-antipattern-refactor` skill. Each anti-pattern includes the code smell (what triggers detection), why it matters (perf/correctness/thread-safety), and the prescriptive fix. Extracted from the skill to keep it under the 200-line budget while preserving the full reference.

---

## Anti-Pattern Catalog

### 1. N+1 Queries (Critical)

**Smell:** Querying related data inside a loop, or accessing navigation properties without eager loading.

```csharp
// ❌ Each iteration fires a separate SQL query
var orders = await db.Orders.ToListAsync();
foreach (var order in orders)
    Console.WriteLine(order.Customer.Name); // Lazy load per row
```

**Fix:** Eager load with `Include`, or project with `Select`.

```csharp
// ✅ Single query with join
var orders = await db.Orders.Include(o => o.Customer).ToListAsync();

// ✅ Even better — project only what you need
var orders = await db.Orders
    .Select(o => new { o.Id, CustomerName = o.Customer.Name })
    .ToListAsync();
```

---

### 2. Missing Projection — Loading Entire Entities for Display (High)

**Smell:** Returning full entities to API responses or views when only a few fields are needed.

```csharp
// ❌ Loads all columns + enables change tracking for a read operation
var user = await db.Users.FirstOrDefaultAsync(u => u.Id == id);
return new UserDto(user.Name, user.Email);
```

**Fix:** Project in the query. Avoids tracking, reduces data transfer, prevents over-posting.

```csharp
// ✅ Only SELECT the columns you need — no tracking, less memory
var dto = await db.Users
    .Where(u => u.Id == id)
    .Select(u => new UserDto(u.Name, u.Email))
    .FirstOrDefaultAsync();
```

---

### 3. Tracking Overhead on Read-Only Queries (High)

**Smell:** Read-only endpoints using default tracked queries.

```csharp
// ❌ Change tracker snapshots every entity — wasted CPU + memory on reads
var products = await db.Products.Where(p => p.IsActive).ToListAsync();
```

**Fix:** Use `AsNoTracking()` for read paths, or configure it at the DbContext level for query-only contexts.

```csharp
// ✅ No change tracking overhead
var products = await db.Products
    .AsNoTracking()
    .Where(p => p.IsActive)
    .ToListAsync();
```

---

### 4. DbContext Lifetime Misuse (Critical)

**Smell:** DbContext registered as Singleton, or shared across threads via `Task.WhenAll` / `Parallel.ForEach`.

```csharp
// ❌ Singleton DbContext — corrupts change tracker across requests
services.AddSingleton<AppDbContext>();

// ❌ Concurrent access — DbContext is NOT thread-safe
var tasks = ids.Select(id => db.Orders.FindAsync(id).AsTask());
await Task.WhenAll(tasks);
```

**Fix:** Always Scoped lifetime. For parallel work, create separate scopes.

```csharp
// ✅ Scoped (default with AddDbContext)
services.AddDbContext<AppDbContext>(o => o.UseNpgsql(conn));

// ✅ Parallel with separate scopes
await Parallel.ForEachAsync(ids, async (id, ct) =>
{
    using var scope = scopeFactory.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
    await db.Orders.FindAsync(new object[] { id }, ct);
});
```

---

### 5. Missing CancellationToken (Medium)

**Smell:** Async EF methods called without passing `CancellationToken`. Client disconnects but query runs to completion.

```csharp
// ❌ No cancellation — query runs even if client disconnects
var orders = await db.Orders.ToListAsync();
```

**Fix:** Thread `CancellationToken` from controller/endpoint through to every async EF call.

```csharp
// ✅ Cancellable — aborts if request is cancelled
var orders = await db.Orders.ToListAsync(ct);
```

---

### 6. Calling ToList() Before Filtering (Critical)

**Smell:** Materializing the full table into memory, then filtering with LINQ-to-Objects.

```csharp
// ❌ Downloads ENTIRE table, then filters in C# memory
var active = db.Products.ToList().Where(p => p.IsActive);
```

**Fix:** Filter before materializing — let the database do the work.

```csharp
// ✅ WHERE clause in SQL, only matching rows returned
var active = await db.Products.Where(p => p.IsActive).ToListAsync(ct);
```

---

### 7. Unbounded Queries — No Pagination (High)

**Smell:** Returning all rows from a table without `Take`/`Skip` or any limit.

```csharp
// ❌ If table has 1M rows, this loads 1M objects into memory
var all = await db.AuditLogs.ToListAsync(ct);
```

**Fix:** Always paginate or limit results. Use keyset pagination for large datasets.

```csharp
// ✅ Bounded result set
var page = await db.AuditLogs
    .OrderByDescending(a => a.CreatedAt)
    .Skip(offset).Take(pageSize)
    .ToListAsync(ct);
```

---

### 8. Using Find/First Without Index Awareness (Medium)

**Smell:** Filtering on columns that don't have database indexes, causing full table scans.

```csharp
// ❌ If Email has no index, this is a full table scan
var user = await db.Users.FirstOrDefaultAsync(u => u.Email == email, ct);
```

**Fix:** Ensure the column has an index. Configure via Fluent API or migration.

```csharp
// ✅ Add index in OnModelCreating or migration
modelBuilder.Entity<User>().HasIndex(u => u.Email).IsUnique();
```

---

### 9. SaveChanges in a Loop (Critical)

**Smell:** Calling `SaveChangesAsync` inside a loop, creating N round-trips.

```csharp
// ❌ 1000 inserts = 1000 database round-trips
foreach (var item in items)
{
    db.Products.Add(item);
    await db.SaveChangesAsync(ct);
}
```

**Fix:** Batch changes, call SaveChanges once. For large volumes, use bulk extensions.

```csharp
// ✅ Single round-trip — EF batches the INSERT statements
db.Products.AddRange(items);
await db.SaveChangesAsync(ct);
```

---

### 10. Implicit Lazy Loading Without Awareness (High)

**Smell:** `UseLazyLoadingProxies()` enabled but developers unaware — hidden N+1 queries appear under load.

```csharp
// ❌ Every .Customer access fires a hidden SELECT — invisible in code review
services.AddDbContext<AppDbContext>(o => o
    .UseNpgsql(conn)
    .UseLazyLoadingProxies()); // Danger: makes N+1 invisible
```

**Fix:** Remove lazy loading. Use explicit `Include()` or projections. Make data access intentional.

```csharp
// ✅ No lazy loading — forces developers to be explicit about joins
services.AddDbContext<AppDbContext>(o => o.UseNpgsql(conn));
```

---

### 11. String Interpolation in Raw SQL (Critical — Security)

**Smell:** Using `FromSqlRaw` with interpolated strings — SQL injection vulnerability.

```csharp
// ❌ SQL INJECTION — user input directly in query string
var results = db.Orders
    .FromSqlRaw($"SELECT * FROM Orders WHERE Status = '{status}'")
    .ToList();
```

**Fix:** Use `FromSqlInterpolated` (auto-parameterizes) or `FromSqlRaw` with explicit parameters.

```csharp
// ✅ Parameterized — safe from injection
var results = await db.Orders
    .FromSqlInterpolated($"SELECT * FROM Orders WHERE Status = {status}")
    .ToListAsync(ct);
```

---

### 12. Ignoring Query Splitting for Collection Includes (Medium)

**Smell:** Multiple collection `Include()` calls causing cartesian explosion (one query with massive JOINs).

```csharp
// ❌ Cartesian explosion — 10 orders × 5 lines × 3 discounts = 150 rows returned
var order = await db.Orders
    .Include(o => o.Lines)
    .Include(o => o.Discounts)
    .Include(o => o.Payments)
    .FirstOrDefaultAsync(o => o.Id == id, ct);
```

**Fix:** Use `AsSplitQuery()` to issue separate SQL queries per collection.

```csharp
// ✅ Separate queries — avoids row explosion
var order = await db.Orders
    .Include(o => o.Lines)
    .Include(o => o.Discounts)
    .Include(o => o.Payments)
    .AsSplitQuery()
    .FirstOrDefaultAsync(o => o.Id == id, ct);
```

---

### 13. Captive DbContext in Singleton (Critical)

**Smell:** A Singleton service injecting DbContext directly — captured forever, leaks memory, thread-unsafe.

```csharp
// ❌ Singleton captures scoped DbContext — never disposed, shared across threads
public class CacheService // Registered as Singleton
{
    private readonly AppDbContext _db; // CAPTURED — scoped in a singleton
    public CacheService(AppDbContext db) => _db = db;
}
```

**Fix:** Inject `IServiceScopeFactory` and create short-lived scopes.

```csharp
// ✅ Create scope on demand — DbContext properly scoped and disposed
public class CacheService
{
    private readonly IServiceScopeFactory _scopeFactory;
    public CacheService(IServiceScopeFactory sf) => _scopeFactory = sf;

    public async Task RefreshAsync(CancellationToken ct)
    {
        using var scope = _scopeFactory.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        // Use db within this scope only
    }
}
```

---

### 14. Not Using Compiled Queries for Hot Paths (Medium)

**Smell:** High-frequency queries (>1000 req/sec) paying expression tree compilation cost on every call.

```csharp
// ❌ Expression tree compiled to SQL on every invocation
var order = await db.Orders.FirstOrDefaultAsync(o => o.Id == id, ct);
```

**Fix:** Use `EF.CompileAsyncQuery` for frequently-called queries.

```csharp
// ✅ Compiled once, reused — eliminates per-call overhead
private static readonly Func<AppDbContext, Guid, CancellationToken, Task<Order?>> _getById =
    EF.CompileAsyncQuery((AppDbContext db, Guid id, CancellationToken ct) =>
        db.Orders.FirstOrDefault(o => o.Id == id));
```

---

### 15. Exposing IQueryable from Repositories (Medium)

**Smell:** Repository returns `IQueryable<T>` — leaks EF concerns into business/application layer, untestable, encourages ad-hoc filtering.

```csharp
// ❌ Caller can add arbitrary .Include(), .Where(), etc. — no encapsulation
public IQueryable<Order> GetOrders() => db.Orders;
```

**Fix:** Return materialized results (`Task<List<T>>` or `Task<T?>`). Keep query logic inside the repository.

```csharp
// ✅ Repository owns the query — testable, encapsulated
public Task<List<OrderSummary>> GetActiveOrdersAsync(CancellationToken ct) =>
    db.Orders.Where(o => o.Status == Active)
        .Select(o => new OrderSummary(o.Id, o.Total))
        .ToListAsync(ct);
```

---

