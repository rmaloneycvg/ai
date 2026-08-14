---
inclusion: manual
---

# Dapper Anti-Pattern Catalog

## Why This Exists

This catalog defines the detection signatures and fix patterns used by the `dapper-antipattern-refactor` skill. Each anti-pattern includes the code smell (what triggers detection), why it matters (security/performance/reliability), and the prescriptive fix. Extracted from the skill to keep it under the 200-line budget while preserving the full reference.

---

## Anti-Pattern Catalog

### 1. SQL Injection via String Concatenation (Critical — Security)

**Smell:** User input concatenated or interpolated directly into SQL strings passed to Dapper.

```csharp
// ❌ SQL INJECTION — user input directly in query
var sql = $"SELECT * FROM Users WHERE Email = '{email}'";
var user = await conn.QueryFirstOrDefaultAsync<User>(sql);
```

**Fix:** Always use parameterized queries. Dapper maps anonymous object properties to `@parameters`.

```csharp
// ✅ Parameterized — safe from injection
var user = await conn.QueryFirstOrDefaultAsync<User>(
    "SELECT * FROM Users WHERE Email = @Email", new { Email = email });
```

---

### 2. Connection Leaks — Missing Dispose (Critical)

**Smell:** `new SqlConnection()` without `using` statement. Connection returned to pool only on GC finalization — pool exhaustion under load.

```csharp
// ❌ Connection never explicitly closed — pool exhaustion
var conn = new NpgsqlConnection(connectionString);
conn.Open();
var data = conn.Query<Order>("SELECT * FROM Orders");
// conn is never disposed!
```

**Fix:** Always `await using` (or `using`) to guarantee disposal.

```csharp
// ✅ Connection returned to pool immediately after use
await using var conn = new NpgsqlConnection(connectionString);
var data = await conn.QueryAsync<Order>("SELECT * FROM Orders");
```

---

### 3. Opening Connections Unnecessarily (Medium)

**Smell:** Manually calling `conn.Open()` before Dapper calls. Dapper opens/closes automatically.

```csharp
// ❌ Unnecessary — Dapper handles open/close internally
await using var conn = new NpgsqlConnection(connectionString);
await conn.OpenAsync(ct); // Redundant for single Dapper call
var result = await conn.QueryAsync<User>(sql, parameters);
```

**Fix:** Let Dapper manage the connection state. Only open manually if you need a transaction or multiple calls on the same open connection.

```csharp
// ✅ Dapper opens and closes automatically
await using var conn = new NpgsqlConnection(connectionString);
var result = await conn.QueryAsync<User>(sql, parameters);
```

---

### 4. N+1 Queries in a Loop (Critical)

**Smell:** Executing a query per item in a collection instead of batching.

```csharp
// ❌ 100 orders = 100 separate queries
foreach (var orderId in orderIds)
{
    var order = await conn.QueryFirstAsync<Order>(
        "SELECT * FROM Orders WHERE Id = @Id", new { Id = orderId });
    results.Add(order);
}
```

**Fix:** Use `WHERE IN` with Dapper's array parameter support.

```csharp
// ✅ Single query — Dapper expands the array into IN clause
var results = await conn.QueryAsync<Order>(
    "SELECT * FROM Orders WHERE Id = ANY(@Ids)", new { Ids = orderIds });
```

---

### 5. Missing CancellationToken (Medium)

**Smell:** Async Dapper calls without `CancellationToken`. Client disconnects but query runs to completion.

```csharp
// ❌ No cancellation support
var orders = await conn.QueryAsync<Order>("SELECT * FROM Orders WHERE Status = @Status",
    new { Status = "active" });
```

**Fix:** Use `CommandDefinition` to pass `CancellationToken`.

```csharp
// ✅ Cancellable — aborts if request is cancelled
var orders = await conn.QueryAsync<Order>(new CommandDefinition(
    "SELECT * FROM Orders WHERE Status = @Status",
    new { Status = "active" },
    cancellationToken: ct));
```

---

### 6. Unbounded Queries — No Pagination (High)

**Smell:** Selecting all rows from a table without LIMIT/OFFSET or TOP.

```csharp
// ❌ If table has 1M rows, all loaded into memory
var all = await conn.QueryAsync<AuditLog>("SELECT * FROM AuditLogs");
```

**Fix:** Always paginate or limit results.

```csharp
// ✅ Bounded result set
var page = await conn.QueryAsync<AuditLog>(
    "SELECT * FROM AuditLogs ORDER BY CreatedAt DESC OFFSET @Offset ROWS FETCH NEXT @Size ROWS ONLY",
    new { Offset = offset, Size = pageSize });
```

---

### 7. SELECT * in Production Queries (High)

**Smell:** Using `SELECT *` instead of explicit columns. Breaks when schema changes, transfers unnecessary data.

```csharp
// ❌ Returns all columns — wastes bandwidth, breaks if columns added/renamed
var users = await conn.QueryAsync<UserDto>("SELECT * FROM Users WHERE IsActive = true");
```

**Fix:** Explicitly name the columns you need. Maps cleanly to DTO properties.

```csharp
// ✅ Explicit columns — predictable, efficient
var users = await conn.QueryAsync<UserDto>(
    "SELECT Id, Name, Email FROM Users WHERE IsActive = true");
```

---

### 8. Incorrect Multi-Mapping (splitOn) (High)

**Smell:** Multi-mapping with wrong or missing `splitOn` parameter — causes incorrect object hydration, null references, or data corruption.

```csharp
// ❌ Default splitOn is "Id" — breaks if second table's PK isn't named "Id"
var results = await conn.QueryAsync<Order, Customer, Order>(sql,
    (order, customer) => { order.Customer = customer; return order; });
// If Customer PK is "CustomerId", the split point is wrong!
```

**Fix:** Always specify `splitOn` explicitly matching the first column of each mapped type.

```csharp
// ✅ Explicit split point
var results = await conn.QueryAsync<Order, Customer, Order>(
    """
    SELECT o.Id, o.Total, o.Status,
           c.CustomerId, c.Name, c.Email
    FROM Orders o JOIN Customers c ON c.CustomerId = o.CustomerId
    """,
    (order, customer) => { order.Customer = customer; return order; },
    splitOn: "CustomerId");
```

---

### 9. Transaction Without Try/Finally (High)

**Smell:** Beginning a transaction without proper rollback on failure — leaves transactions open, locks rows.

```csharp
// ❌ If exception occurs, transaction hangs open — locks held
await conn.OpenAsync(ct);
var txn = await conn.BeginTransactionAsync(ct);
await conn.ExecuteAsync("INSERT INTO Orders ...", order, txn);
await conn.ExecuteAsync("INSERT INTO OrderLines ...", lines, txn);
await txn.CommitAsync(ct);
// Exception before Commit = transaction never rolled back until connection timeout
```

**Fix:** Wrap transaction in `using` — disposal auto-rolls back if not committed.

```csharp
// ✅ Auto-rollback on exception — using handles disposal
await conn.OpenAsync(ct);
await using var txn = await conn.BeginTransactionAsync(ct);
await conn.ExecuteAsync("INSERT INTO Orders ...", order, transaction: txn);
await conn.ExecuteAsync("INSERT INTO OrderLines ...", lines, transaction: txn);
await txn.CommitAsync(ct);
```

---

### 10. Stored Procedure Without CommandType (Medium)

**Smell:** Calling a stored procedure via raw SQL `EXEC` string instead of using `CommandType.StoredProcedure`.

```csharp
// ❌ Fragile — parameter handling differs, no clean output parameter support
var result = await conn.QueryAsync<Report>(
    "EXEC sp_GenerateReport @From, @To", new { From = from, To = to });
```

**Fix:** Use `commandType: CommandType.StoredProcedure` for proper parameter binding.

```csharp
// ✅ Proper stored procedure call — supports output params, correct parameter handling
var result = await conn.QueryAsync<Report>(new CommandDefinition(
    "sp_GenerateReport",
    new { From = from, To = to },
    commandType: CommandType.StoredProcedure,
    cancellationToken: ct));
```

---

### 11. Reusing a Single Connection Across Requests (Critical)

**Smell:** A singleton or static connection instance shared across threads/requests.

```csharp
// ❌ Single connection shared by all request threads — thread-unsafe, pool of 1
public class OrderRepo
{
    private static readonly NpgsqlConnection _conn = new(connStr); // SHARED!
    public Task<Order?> GetAsync(Guid id) => _conn.QueryFirstOrDefaultAsync<Order>(...);
}
```

**Fix:** Create a new connection per operation (from connection pool). Inject the connection string, not the connection.

```csharp
// ✅ New pooled connection per call — thread-safe, properly pooled
public class OrderRepo
{
    private readonly string _connStr;
    public OrderRepo(IConfiguration config) => _connStr = config.GetConnectionString("Default")!;

    public async Task<Order?> GetAsync(Guid id, CancellationToken ct)
    {
        await using var conn = new NpgsqlConnection(_connStr);
        return await conn.QueryFirstOrDefaultAsync<Order>(new CommandDefinition(
            "SELECT Id, Total, Status FROM Orders WHERE Id = @Id",
            new { Id = id }, cancellationToken: ct));
    }
}
```

---

### 12. DynamicParameters Abuse for Simple Queries (Low)

**Smell:** Using `DynamicParameters` when a simple anonymous object works. Adds verbosity without benefit.

```csharp
// ❌ Overly verbose for a simple parameterized query
var p = new DynamicParameters();
p.Add("@Id", id);
p.Add("@Status", status);
var order = await conn.QueryFirstAsync<Order>(sql, p);
```

**Fix:** Use anonymous objects for simple cases. Reserve `DynamicParameters` for output params or dynamic WHERE construction.

```csharp
// ✅ Clean and readable
var order = await conn.QueryFirstAsync<Order>(sql, new { Id = id, Status = status });
```

---

### 13. Missing QueryMultiple for Related Datasets (Medium)

**Smell:** Making separate database round-trips for data that should be fetched together.

```csharp
// ❌ Two round-trips for one logical read
var order = await conn.QueryFirstAsync<Order>("SELECT ... FROM Orders WHERE Id = @Id", new { Id = id });
var lines = await conn.QueryAsync<OrderLine>("SELECT ... FROM OrderLines WHERE OrderId = @Id", new { Id = id });
```

**Fix:** Use `QueryMultipleAsync` to batch multiple result sets in one round-trip.

```csharp
// ✅ Single round-trip, multiple result sets
await using var multi = await conn.QueryMultipleAsync(
    "SELECT ... FROM Orders WHERE Id = @Id; SELECT ... FROM OrderLines WHERE OrderId = @Id",
    new { Id = id });
var order = await multi.ReadFirstAsync<Order>();
var lines = (await multi.ReadAsync<OrderLine>()).ToList();
```

---

### 14. Swallowing SQL Exceptions Without Context (Medium)

**Smell:** Catching generic exceptions around Dapper calls without logging the SQL or parameters — makes debugging impossible.

```csharp
// ❌ Swallowed — no idea which query failed or with what input
try { await conn.ExecuteAsync(sql, parameters); }
catch (Exception) { return false; }
```

**Fix:** Log the exception with query context. Rethrow or return meaningful error.

```csharp
// ✅ Logged with context — debuggable
try
{
    await conn.ExecuteAsync(sql, parameters);
}
catch (NpgsqlException ex)
{
    logger.LogError(ex, "Query failed: {Sql} with {@Params}", sql, parameters);
    throw;
}
```

---

### 15. Building Dynamic WHERE with String Concat (High)

**Smell:** Conditionally appending WHERE clauses via string concatenation — SQL injection risk and messy code.

```csharp
// ❌ Injection risk + unmaintainable spaghetti
var sql = "SELECT * FROM Products WHERE 1=1";
if (!string.IsNullOrEmpty(name)) sql += $" AND Name LIKE '%{name}%'"; // INJECTION!
if (minPrice > 0) sql += $" AND Price >= {minPrice}";
```

**Fix:** Use parameterized conditional building, or a query builder like SqlKata/Dapper.SqlBuilder.

```csharp
// ✅ Safe parameterized dynamic SQL
var builder = new SqlBuilder();
var template = builder.AddTemplate("SELECT * FROM Products /**where**/");
if (!string.IsNullOrEmpty(name))
    builder.Where("Name LIKE @Name", new { Name = $"%{name}%" });
if (minPrice > 0)
    builder.Where("Price >= @MinPrice", new { MinPrice = minPrice });

var results = await conn.QueryAsync<Product>(template.RawSql, template.Parameters);
```

---
