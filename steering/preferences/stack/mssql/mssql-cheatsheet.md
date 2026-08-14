---
inclusion: manual
---

# MS SQL Server Patterns & Reference

## Why This Exists

This document is the comprehensive SQL Server reference covering query execution fundamentals, indexing strategy, APPLY vs JOIN decisions, query hints, window functions, CTEs/temp tables, execution plan reading, locking/concurrency, anti-patterns (with full code examples), and performance troubleshooting. It complements `query-performance.md` (which provides concise decision matrices and DMV queries for the `mssql-query-performance` skill) by supplying the deep-dive explanations and code patterns.

**Target:** SQL Server 2019+ | **Last updated:** 2026-08-06

---

## Table of Contents

- [Query Execution Fundamentals](#query-execution-fundamentals)
- [Indexing Strategy](#indexing-strategy)
- [APPLY vs JOIN](#apply-vs-join)
- [Query Hints](#query-hints)
- [Window Functions](#window-functions)
- [CTEs and Temp Tables](#ctes-and-temp-tables)
- [Execution Plans](#execution-plans)
- [Locking and Concurrency](#locking-and-concurrency)
- [Anti-Patterns](#anti-patterns)
- [Performance Troubleshooting](#performance-troubleshooting)

---

## Query Execution Fundamentals

### Logical Query Processing Order

SQL Server processes queries in this order (NOT the order you write them):

```
1. FROM        — Table access, joins
2. WHERE       — Row filtering
3. GROUP BY    — Aggregation grouping
4. HAVING      — Aggregate filtering
5. SELECT      — Column projection
6. DISTINCT    — Duplicate removal
7. ORDER BY    — Sorting
8. TOP/OFFSET  — Row limiting
```

**Why this matters:** You can't reference a column alias from SELECT in your WHERE clause because WHERE executes first.

```sql
-- ❌ Won't work — alias doesn't exist yet at WHERE phase
SELECT TotalAmount = Quantity * Price
FROM Orders
WHERE TotalAmount > 100;

-- ✅ Repeat the expression or use a subquery/CTE
SELECT TotalAmount = Quantity * Price
FROM Orders
WHERE Quantity * Price > 100;
```

### SET vs SELECT for Variable Assignment

```sql
-- SET: assigns one variable at a time, ANSI standard
SET @var = (SELECT TOP 1 Name FROM Users WHERE Id = @id);
-- If no rows: @var = NULL (safe)

-- SELECT: can assign multiple, but dangerous with multiple rows
SELECT @var = Name FROM Users WHERE Id = @id;
-- If no rows: @var RETAINS ITS PREVIOUS VALUE (silent bug)
-- If multiple rows: @var gets the LAST value (non-deterministic)
```

**Rule:** Use SET for single assignment. Use SELECT only when assigning multiple variables from the same row.

---

## Indexing Strategy

### Index Types

| Type | Use Case | Notes |
|------|----------|-------|
| Clustered | The table itself, ordered by PK | One per table. Defines physical row order. |
| Non-Clustered | Secondary lookups | Points back to clustered key (or RID if heap) |
| Covering | Query satisfied entirely from index | Include columns via INCLUDE clause |
| Filtered | Subset of rows | Great for sparse columns, soft deletes |
| Columnstore | Analytics/aggregation on large tables | Batch mode processing, massive compression |
| Unique | Enforce uniqueness | Can be clustered or non-clustered |

### Clustered Index Design

The clustered index key should be:

- **Narrow** — it's stored in every non-clustered index as a row locator
- **Unique** — if not unique, SQL Server adds a hidden 4-byte uniquifier
- **Static** — changing the key means physically moving the row
- **Ever-increasing** — prevents page splits (IDENTITY, NEWSEQUENTIALID)

```sql
-- ✅ Good clustered index: narrow, unique, ever-increasing
CREATE CLUSTERED INDEX IX_Orders_Id ON Orders(Id);  -- IDENTITY column

-- ❌ Bad clustered index: wide, frequently updated
CREATE CLUSTERED INDEX IX_Orders_Email ON Orders(CustomerEmail);
```

### Non-Clustered Index Design

```sql
-- Basic index
CREATE NONCLUSTERED INDEX IX_Orders_CustomerId
ON Orders(CustomerId);

-- Composite index — column ORDER MATTERS
-- Supports: WHERE CustomerId = @id AND OrderDate > @date
-- Does NOT support: WHERE OrderDate > @date (alone)
CREATE NONCLUSTERED INDEX IX_Orders_Customer_Date
ON Orders(CustomerId, OrderDate);

-- Covering index with INCLUDE columns
-- Avoids key lookup back to clustered index
CREATE NONCLUSTERED INDEX IX_Orders_Customer_Date_Cover
ON Orders(CustomerId, OrderDate)
INCLUDE (TotalAmount, Status);

-- Filtered index — only index active orders
CREATE NONCLUSTERED INDEX IX_Orders_Active
ON Orders(CustomerId, OrderDate)
WHERE IsDeleted = 0;
```

### Index Column Order Rules

The leftmost columns in a composite index are the most important:

```sql
-- Index: (A, B, C)
-- ✅ Supports: WHERE A = x
-- ✅ Supports: WHERE A = x AND B = y
-- ✅ Supports: WHERE A = x AND B = y AND C = z
-- ✅ Supports: WHERE A = x ORDER BY B
-- ❌ Does NOT support: WHERE B = y (skips leading column)
-- ❌ Does NOT support: WHERE C = z (skips leading columns)
-- ⚠️  Partial: WHERE A = x AND C = z (seeks A, scans for C)
```

### SARGable Predicates (Search ARGument able)

A predicate is SARGable if the query optimizer can use an index seek. Non-SARGable predicates force scans.

```sql
-- ✅ SARGable — can seek on index
WHERE OrderDate >= '2025-01-01'
WHERE CustomerId = 42
WHERE LastName LIKE 'Smith%'       -- prefix match

-- ❌ Non-SARGable — forces scan
WHERE YEAR(OrderDate) = 2025       -- function on column
WHERE Price * Quantity > 1000      -- expression on column
WHERE LastName LIKE '%Smith'       -- leading wildcard
WHERE ISNULL(Status, 'X') = 'X'   -- function on column
WHERE CustomerId + 1 = 43         -- arithmetic on column
```

**Fix non-SARGable predicates:**

```sql
-- Instead of YEAR(OrderDate) = 2025:
WHERE OrderDate >= '2025-01-01' AND OrderDate < '2026-01-01'

-- Instead of ISNULL(Status, 'X') = 'X':
WHERE (Status = 'X' OR Status IS NULL)

-- Instead of CAST(CreatedDate AS DATE) = '2025-06-01':
WHERE CreatedDate >= '2025-06-01' AND CreatedDate < '2025-06-02'
```

### Index Maintenance

```sql
-- Check fragmentation
SELECT
    OBJECT_NAME(ips.object_id) AS TableName,
    i.name AS IndexName,
    ips.avg_fragmentation_in_percent,
    ips.page_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE ips.avg_fragmentation_in_percent > 10
    AND ips.page_count > 1000
ORDER BY ips.avg_fragmentation_in_percent DESC;

-- Rebuild (> 30% fragmentation) — locks table
ALTER INDEX IX_Orders_CustomerId ON Orders REBUILD;

-- Reorganize (10-30% fragmentation) — online operation
ALTER INDEX IX_Orders_CustomerId ON Orders REORGANIZE;

-- Update statistics after rebuild
UPDATE STATISTICS Orders;
```

### Missing Index DMVs

```sql
SELECT
    OBJECT_NAME(mid.object_id) AS TableName,
    mid.equality_columns,
    mid.inequality_columns,
    mid.included_columns,
    migs.avg_user_impact,
    migs.user_seeks,
    migs.user_scans
FROM sys.dm_db_missing_index_details mid
JOIN sys.dm_db_missing_index_groups mig ON mid.index_handle = mig.index_handle
JOIN sys.dm_db_missing_index_group_stats migs ON mig.index_group_handle = migs.group_handle
WHERE mid.database_id = DB_ID()
ORDER BY migs.avg_user_impact * migs.user_seeks DESC;
```

**Warning:** Don't blindly create every missing index. They overlap, duplicate, and can hurt write performance. Analyze the suggestions, consolidate similar ones.


---

## APPLY vs JOIN

### The Core Difference

| Feature | JOIN | APPLY |
|---------|------|-------|
| Evaluation | Set-based — both sides evaluated independently | Row-by-row — right side can reference left side |
| Correlation | Cannot reference outer table in joined table expression | CAN reference outer table columns |
| Table-valued functions | Cannot pass outer column as parameter | Can pass outer row values to TVF |
| Top-N per group | Complex (window functions or self-join) | Natural and readable |
| Performance | Usually better for large set-to-set operations | Better for correlated lookups, TVFs, top-N per group |

### CROSS APPLY vs OUTER APPLY

```sql
-- CROSS APPLY: like INNER JOIN — excludes outer rows with no match
-- OUTER APPLY: like LEFT JOIN — keeps outer rows, NULLs for no match
```

### Pattern 1: Top-N Per Group

Get the 3 most recent orders per customer:

```sql
-- ❌ JOIN approach — awkward, requires window function + subquery
SELECT c.CustomerName, o.OrderDate, o.TotalAmount
FROM Customers c
JOIN (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY CustomerId ORDER BY OrderDate DESC) AS rn
    FROM Orders
) o ON c.Id = o.CustomerId AND o.rn <= 3;

-- ✅ CROSS APPLY — natural, readable, often faster
SELECT c.CustomerName, o.OrderDate, o.TotalAmount
FROM Customers c
CROSS APPLY (
    SELECT TOP 3 OrderDate, TotalAmount
    FROM Orders
    WHERE CustomerId = c.Id
    ORDER BY OrderDate DESC
) o;
```

**Why APPLY wins here:** The optimizer can use an index seek on `Orders(CustomerId, OrderDate DESC)` for each customer, stopping after 3 rows. The window function approach must process ALL orders first, then filter.

### Pattern 2: Table-Valued Functions

```sql
-- Table-valued function that splits a CSV string
CREATE FUNCTION dbo.SplitString(@Input NVARCHAR(MAX), @Delimiter CHAR(1))
RETURNS TABLE AS
RETURN (
    SELECT value FROM STRING_SPLIT(@Input, @Delimiter)
);

-- CROSS APPLY to call TVF with values from each row
SELECT p.ProductName, tag.value AS Tag
FROM Products p
CROSS APPLY dbo.SplitString(p.Tags, ',') tag;

-- JOINs CANNOT do this — you can't pass a column value to a table expression
```

### Pattern 3: Unpivoting / Expanding Rows

```sql
-- Expand a row with multiple phone columns into rows
SELECT c.CustomerName, phones.PhoneType, phones.PhoneNumber
FROM Customers c
CROSS APPLY (
    VALUES
        ('Home', c.HomePhone),
        ('Work', c.WorkPhone),
        ('Mobile', c.MobilePhone)
) phones(PhoneType, PhoneNumber)
WHERE phones.PhoneNumber IS NOT NULL;
```

### Pattern 4: Correlated Subquery Replacement

```sql
-- ❌ Correlated subquery in SELECT — executes per row, can't return multiple columns
SELECT
    o.OrderId,
    (SELECT TOP 1 Name FROM Products WHERE Id = o.ProductId) AS ProductName,
    (SELECT TOP 1 Category FROM Products WHERE Id = o.ProductId) AS ProductCategory
FROM Orders o;

-- ✅ CROSS APPLY — one lookup returns multiple columns
SELECT o.OrderId, p.Name AS ProductName, p.Category AS ProductCategory
FROM Orders o
CROSS APPLY (
    SELECT TOP 1 Name, Category
    FROM Products
    WHERE Id = o.ProductId
) p;
```

### Pattern 5: OUTER APPLY for Optional Related Data

```sql
-- Get each customer with their most recent order (if any)
SELECT
    c.CustomerName,
    lastOrder.OrderDate,
    lastOrder.TotalAmount
FROM Customers c
OUTER APPLY (
    SELECT TOP 1 OrderDate, TotalAmount
    FROM Orders
    WHERE CustomerId = c.Id
    ORDER BY OrderDate DESC
) lastOrder;
-- Customers with no orders still appear (NULLs for order columns)
```

### When JOIN Beats APPLY

```sql
-- Simple equi-join between large tables — JOIN is more efficient
-- The optimizer can choose hash join, merge join, or nested loops

-- ✅ JOIN for set-to-set operations
SELECT o.OrderId, c.CustomerName
FROM Orders o
JOIN Customers c ON o.CustomerId = c.Id;

-- ❌ APPLY here adds unnecessary per-row overhead
SELECT o.OrderId, c.CustomerName
FROM Orders o
CROSS APPLY (
    SELECT CustomerName FROM Customers WHERE Id = o.CustomerId
) c;
```

### Performance Comparison Summary

| Scenario | Winner | Why |
|----------|--------|-----|
| Large table to large table equi-join | JOIN | Hash/merge join parallelism |
| Top-N per group with good index | APPLY | Index seek + TOP stops early |
| Calling a TVF per row | APPLY | Only option — JOIN can't correlate |
| Unpivot/expand columns to rows | APPLY | Natural with VALUES |
| Optional correlated lookup | OUTER APPLY | Cleaner than LEFT JOIN + subquery |
| Many-to-many relationships | JOIN | Set operations more efficient |
| Small outer set, indexed inner lookup | APPLY | Nested loop with seek is optimal |
| Large outer set, no good inner index | JOIN | Hash join doesn't need index |


---

## Query Hints

### Table Hints

```sql
-- NOLOCK: dirty reads, no shared locks (read uncommitted)
-- Use for: reporting queries where stale data is acceptable
-- ❌ NEVER for financial, transactional, or data-integrity-sensitive reads
SELECT * FROM Orders WITH (NOLOCK) WHERE Status = 'Pending';

-- READPAST: skip locked rows (only with row-level locks)
-- Use for: queue-processing patterns
SELECT TOP 1 * FROM JobQueue WITH (READPAST, UPDLOCK, ROWLOCK)
WHERE Status = 'Pending' ORDER BY CreatedDate;

-- FORCESEEK: force index seek (override optimizer)
SELECT * FROM Orders WITH (FORCESEEK) WHERE CustomerId = @id;

-- FORCESCAN: force scan (when optimizer wrongly picks seek on bad stats)
SELECT * FROM Orders WITH (FORCESCAN) WHERE Status IN ('A','B','C','D');

-- TABLOCK: table-level lock (faster bulk inserts)
INSERT INTO Staging WITH (TABLOCK) SELECT * FROM Source;

-- UPDLOCK: take update locks during read (prevent race conditions)
-- Use for: SELECT-then-UPDATE patterns (pessimistic concurrency)
BEGIN TRAN;
SELECT @balance = Balance FROM Accounts WITH (UPDLOCK) WHERE Id = @id;
UPDATE Accounts SET Balance = @balance - @amount WHERE Id = @id;
COMMIT;
```

### Query-Level Hints (OPTION clause)

```sql
-- RECOMPILE: fresh plan every execution
-- Use for: highly variable parameters, one-off queries
SELECT * FROM Orders WHERE OrderDate > @startDate
OPTION (RECOMPILE);

-- OPTIMIZE FOR: compile plan for a specific value
-- Use for: parameter sniffing problems with known typical value
SELECT * FROM Orders WHERE CustomerId = @id
OPTION (OPTIMIZE FOR (@id = 1001));

-- OPTIMIZE FOR UNKNOWN: use average statistics
SELECT * FROM Orders WHERE CustomerId = @id
OPTION (OPTIMIZE FOR UNKNOWN);

-- MAXDOP: limit parallelism for this query
SELECT * FROM LargeTable WHERE Status = 'Active'
OPTION (MAXDOP 4);

-- HASH JOIN / MERGE JOIN / LOOP JOIN: force join strategy
SELECT o.*, c.Name
FROM Orders o JOIN Customers c ON o.CustomerId = c.Id
OPTION (HASH JOIN);

-- USE PLAN: supply an XML execution plan
-- Last resort — extremely fragile, breaks on schema changes
```

### When to Use Hints (Decision Framework)

| Situation | Hint | Risk Level |
|-----------|------|-----------|
| Parameter sniffing | RECOMPILE or OPTIMIZE FOR | Low |
| Reporting on OLTP | NOLOCK | Medium (dirty reads) |
| Queue processing | READPAST + UPDLOCK | Low |
| Bad cardinality estimate | HASH/MERGE/LOOP JOIN | Medium |
| Bulk loading | TABLOCK | Low (during maintenance) |
| Optimizer regression | USE PLAN | High (fragile) |

**Golden Rule:** Hints are band-aids. If you need hints everywhere, fix the root cause (statistics, indexes, schema design).


---

## Window Functions

### Syntax

```sql
function_name() OVER (
    [PARTITION BY column_list]    -- reset calculation per group
    [ORDER BY column_list]       -- defines ordering within partition
    [ROWS/RANGE frame_spec]      -- defines window frame
)
```

### Ranking Functions

```sql
-- ROW_NUMBER: unique sequential number (no ties)
-- RANK: same value = same rank, with gaps (1, 2, 2, 4)
-- DENSE_RANK: same value = same rank, no gaps (1, 2, 2, 3)
-- NTILE(n): distribute rows into n roughly equal groups

SELECT
    OrderId,
    CustomerId,
    TotalAmount,
    ROW_NUMBER() OVER (PARTITION BY CustomerId ORDER BY TotalAmount DESC) AS RowNum,
    RANK()       OVER (PARTITION BY CustomerId ORDER BY TotalAmount DESC) AS Rnk,
    DENSE_RANK() OVER (PARTITION BY CustomerId ORDER BY TotalAmount DESC) AS DenseRnk,
    NTILE(4)     OVER (PARTITION BY CustomerId ORDER BY TotalAmount DESC) AS Quartile
FROM Orders;
```

### Aggregate Window Functions

```sql
SELECT
    OrderId,
    CustomerId,
    TotalAmount,
    SUM(TotalAmount) OVER (PARTITION BY CustomerId) AS CustomerTotal,
    AVG(TotalAmount) OVER (PARTITION BY CustomerId) AS CustomerAvg,
    COUNT(*)         OVER (PARTITION BY CustomerId) AS CustomerOrderCount,
    -- Running total
    SUM(TotalAmount) OVER (
        PARTITION BY CustomerId
        ORDER BY OrderDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS RunningTotal,
    -- Moving average (last 3 orders)
    AVG(TotalAmount) OVER (
        PARTITION BY CustomerId
        ORDER BY OrderDate
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS MovingAvg3
FROM Orders;
```

### Offset Functions

```sql
SELECT
    OrderId,
    OrderDate,
    TotalAmount,
    -- Previous row's value
    LAG(TotalAmount, 1, 0)  OVER (PARTITION BY CustomerId ORDER BY OrderDate) AS PrevAmount,
    -- Next row's value
    LEAD(TotalAmount, 1, 0) OVER (PARTITION BY CustomerId ORDER BY OrderDate) AS NextAmount,
    -- First value in partition
    FIRST_VALUE(TotalAmount) OVER (
        PARTITION BY CustomerId ORDER BY OrderDate
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS FirstOrderAmount,
    -- Last value in partition
    LAST_VALUE(TotalAmount) OVER (
        PARTITION BY CustomerId ORDER BY OrderDate
        ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
    ) AS LastOrderAmount
FROM Orders;
```

### Frame Specifications

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW    -- default for ORDER BY
ROWS BETWEEN CURRENT ROW AND UNBOUNDED FOLLOWING
ROWS BETWEEN 2 PRECEDING AND 2 FOLLOWING            -- sliding window
ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING  -- entire partition

-- ROWS vs RANGE:
-- ROWS: physical rows (deterministic)
-- RANGE: logical values (groups ties together — often not what you want)
```

**⚠️ Default frame trap:** When you specify ORDER BY without an explicit frame, the default is `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` — which groups ties. Use `ROWS` explicitly for deterministic running totals.

### Common Patterns

```sql
-- Delete duplicates (keep first occurrence)
;WITH Dupes AS (
    SELECT *, ROW_NUMBER() OVER (
        PARTITION BY Email ORDER BY CreatedDate
    ) AS rn
    FROM Users
)
DELETE FROM Dupes WHERE rn > 1;

-- Gap detection
SELECT
    OrderDate,
    LEAD(OrderDate) OVER (ORDER BY OrderDate) AS NextOrderDate,
    DATEDIFF(DAY, OrderDate, LEAD(OrderDate) OVER (ORDER BY OrderDate)) AS DayGap
FROM Orders
WHERE CustomerId = @id;

-- Percent of total
SELECT
    Category,
    SalesAmount,
    SalesAmount * 100.0 / SUM(SalesAmount) OVER () AS PctOfTotal
FROM CategorySales;
```


---

## CTEs and Temp Tables

### CTE (Common Table Expression)

```sql
;WITH OrderTotals AS (
    SELECT CustomerId, SUM(TotalAmount) AS Total
    FROM Orders
    GROUP BY CustomerId
)
SELECT c.Name, ot.Total
FROM Customers c
JOIN OrderTotals ot ON c.Id = ot.CustomerId
WHERE ot.Total > 1000;
```

**CTE Facts:**
- Not materialized — inlined into the query (like a view)
- Re-executed every time it's referenced in the same query
- Scope: single statement only
- Recursive CTEs support hierarchical queries

### Recursive CTE

```sql
-- Org chart: find all reports under a manager
;WITH OrgChart AS (
    -- Anchor: the starting manager
    SELECT EmployeeId, ManagerId, Name, 0 AS Level
    FROM Employees
    WHERE EmployeeId = @managerId

    UNION ALL

    -- Recursive: find direct reports of each person found so far
    SELECT e.EmployeeId, e.ManagerId, e.Name, oc.Level + 1
    FROM Employees e
    JOIN OrgChart oc ON e.ManagerId = oc.EmployeeId
)
SELECT * FROM OrgChart
OPTION (MAXRECURSION 100);  -- safety limit, default is 100
```

### Temp Tables

```sql
-- Local temp table: visible to current session only
CREATE TABLE #OrderSummary (
    CustomerId INT,
    OrderCount INT,
    TotalAmount DECIMAL(18,2),
    INDEX IX_Customer (CustomerId)  -- inline index
);

INSERT INTO #OrderSummary
SELECT CustomerId, COUNT(*), SUM(TotalAmount)
FROM Orders
GROUP BY CustomerId;

-- Global temp table: visible to all sessions (rare use)
CREATE TABLE ##SharedData (...);
```

### Table Variables

```sql
DECLARE @Results TABLE (
    Id INT,
    Name NVARCHAR(100),
    INDEX IX_Id (Id)  -- SQL 2014+
);

INSERT INTO @Results
SELECT Id, Name FROM Products WHERE Category = 'Active';
```

### Decision Matrix: CTE vs Temp Table vs Table Variable

| Factor | CTE | Temp Table | Table Variable |
|--------|-----|-----------|----------------|
| Materialized | ❌ No (inlined) | ✅ Yes (tempdb) | ✅ Yes (tempdb) |
| Statistics | Uses base table stats | Has own statistics | ❌ No stats (estimates 1 row!) |
| Indexes | No | Yes (full) | Limited (SQL 2014+) |
| Re-usable in query | Each reference re-executes | Yes — read multiple times | Yes |
| Transaction rollback | N/A | Rolled back | NOT rolled back |
| Good for | Readability, recursion, one-time reference | Large intermediate results, multiple references | Small results (< 1000 rows), inside stored procs |
| **⚠️ Trap** | Multiple references = multiple executions | Lock contention in tempdb under load | Optimizer always estimates 1 row → bad plans |

**Rule of thumb:**
- < 100 rows, referenced once → CTE
- < 1000 rows, need in a proc → Table variable
- Anything larger or referenced multiple times → Temp table

---

## Execution Plans

### How to Read Them

```sql
-- Estimated plan (doesn't execute)
SET SHOWPLAN_XML ON;
GO
SELECT * FROM Orders WHERE CustomerId = 42;
GO
SET SHOWPLAN_XML OFF;

-- Actual plan (executes and shows real row counts)
SET STATISTICS XML ON;
SELECT * FROM Orders WHERE CustomerId = 42;
SET STATISTICS XML OFF;

-- Quick stats
SET STATISTICS IO ON;
SET STATISTICS TIME ON;
```

### Key Operators to Recognize

| Operator | Meaning | Good/Bad |
|----------|---------|----------|
| Index Seek | Direct lookup via index B-tree | ✅ Good |
| Index Scan | Read entire index | ⚠️ Check if seek is possible |
| Table Scan | Read entire heap (no clustered index) | ❌ Usually bad |
| Key Lookup | Go back to clustered index for missing columns | ⚠️ Add INCLUDE columns |
| Hash Match | Hash join or hash aggregate | ✅ Good for large unsorted sets |
| Merge Join | Merge two sorted streams | ✅ Good when both sides sorted |
| Nested Loops | For each outer row, seek inner | ✅ Good for small outer + indexed inner |
| Sort | Explicit sort operation | ⚠️ Expensive — can it be avoided with index? |
| Spool (Eager/Lazy) | Materialize intermediate results | ⚠️ Often a sign of suboptimal plan |
| Parallelism | Multi-threaded execution | ✅ Good for large scans |

### Warning Signs in Execution Plans

| Warning | Meaning | Fix |
|---------|---------|-----|
| Fat arrows | High row counts flowing between operators | Filter earlier, better predicates |
| Estimated vs Actual rows wildly different | Stale statistics or bad cardinality estimate | UPDATE STATISTICS, RECOMPILE |
| Key Lookup with high row count | Index not covering | Add INCLUDE columns |
| Sort with spill to tempdb | Not enough memory granted | Add index in sort order, or trace flag 7470 |
| Implicit conversion | Type mismatch forces scan | Fix data types in schema or parameters |
| Table Spool | Repeated scan of same data | Materialize in temp table instead |

### Implicit Conversions (Silent Performance Killer)

```sql
-- Column is VARCHAR, parameter is NVARCHAR — IMPLICIT CONVERSION
-- SQL Server converts EVERY ROW of the column, forcing a scan
DECLARE @name NVARCHAR(100) = N'Smith';
SELECT * FROM Customers WHERE LastName = @name;  -- LastName is VARCHAR!

-- Fix: match types
DECLARE @name VARCHAR(100) = 'Smith';
SELECT * FROM Customers WHERE LastName = @name;
```

**Data type precedence:** SQL Server converts the LOWER precedence type. `NVARCHAR` > `VARCHAR`, so the column gets converted (per-row), not the parameter.


---

## Locking and Concurrency

### Isolation Levels

| Level | Dirty Reads | Non-Repeatable Reads | Phantoms | Lock Behavior |
|-------|:-----------:|:--------------------:|:--------:|---------------|
| READ UNCOMMITTED | ✅ Yes | ✅ Yes | ✅ Yes | No shared locks taken |
| READ COMMITTED (default) | ❌ No | ✅ Yes | ✅ Yes | Shared locks released after read |
| REPEATABLE READ | ❌ No | ❌ No | ✅ Yes | Shared locks held until commit |
| SERIALIZABLE | ❌ No | ❌ No | ❌ No | Range locks — most restrictive |
| SNAPSHOT | ❌ No | ❌ No | ❌ No | Row versioning (tempdb) — no blocking |
| READ COMMITTED SNAPSHOT | ❌ No | ✅ Yes | ✅ Yes | Row versioning — readers don't block writers |

### SNAPSHOT vs READ COMMITTED SNAPSHOT (RCSI)

```sql
-- Enable RCSI (recommended for most OLTP apps)
ALTER DATABASE MyDb SET READ_COMMITTED_SNAPSHOT ON;
-- Now READ COMMITTED uses row versions instead of locks
-- Readers never block writers, writers never block readers
-- ⚠️ Increases tempdb usage (version store)

-- Enable SNAPSHOT isolation (opt-in per transaction)
ALTER DATABASE MyDb SET ALLOW_SNAPSHOT_ISOLATION ON;
-- Must explicitly set in each transaction:
SET TRANSACTION ISOLATION LEVEL SNAPSHOT;
```

### Deadlock Prevention

```sql
-- 1. Always access tables in the same order across all procedures
-- 2. Keep transactions short
-- 3. Use appropriate isolation level (RCSI eliminates read/write deadlocks)

-- Pattern: SELECT-then-UPDATE with UPDLOCK prevents conversion deadlocks
BEGIN TRAN;
SELECT @qty = QuantityOnHand
FROM Inventory WITH (UPDLOCK, ROWLOCK)
WHERE ProductId = @productId;

IF @qty >= @requestedQty
    UPDATE Inventory SET QuantityOnHand = @qty - @requestedQty
    WHERE ProductId = @productId;
COMMIT;
```

### Finding Blocking

```sql
-- Current blocking chains
SELECT
    blocking.session_id AS BlockingSessionId,
    blocked.session_id AS BlockedSessionId,
    blocked.wait_type,
    blocked.wait_time / 1000 AS WaitSeconds,
    OBJECT_NAME(p.object_id) AS BlockedTable,
    t.text AS BlockingQuery
FROM sys.dm_exec_requests blocked
JOIN sys.dm_exec_sessions blocking ON blocked.blocking_session_id = blocking.session_id
OUTER APPLY sys.dm_exec_sql_text(blocking.most_recent_sql_handle) t
LEFT JOIN sys.partitions p ON blocked.resource_description LIKE '%' + CAST(p.hobt_id AS VARCHAR) + '%'
WHERE blocked.blocking_session_id > 0;
```


---

## Anti-Patterns

### 1. SELECT * in Production Code

```sql
-- ❌ Anti-pattern
SELECT * FROM Orders WHERE CustomerId = @id;

-- Problems:
-- • Can't use covering indexes (always needs key lookup)
-- • Returns columns you don't need (network, memory waste)
-- • Schema changes silently break consuming code
-- • Prevents query optimization

-- ✅ Fix: explicit column list
SELECT OrderId, OrderDate, TotalAmount, Status
FROM Orders WHERE CustomerId = @id;
```

### 2. Scalar Functions in WHERE/SELECT

```sql
-- ❌ Anti-pattern: scalar UDF called per-row (kills parallelism)
SELECT OrderId, dbo.GetCustomerName(CustomerId) AS CustomerName
FROM Orders
WHERE dbo.IsValidOrder(OrderId) = 1;

-- Problems:
-- • Called once per row (RBAR — Row By Agonizing Row)
-- • Prevents parallelism
-- • Optimizer can't see inside the function
-- • Can't use indexes on function results

-- ✅ Fix: inline TVF or join
SELECT o.OrderId, c.Name AS CustomerName
FROM Orders o
JOIN Customers c ON o.CustomerId = c.Id
WHERE o.Status NOT IN ('Cancelled', 'Invalid');

-- Or use inline TVF (which is expanded by optimizer)
CREATE FUNCTION dbo.GetValidOrders()
RETURNS TABLE AS
RETURN (SELECT * FROM Orders WHERE Status NOT IN ('Cancelled', 'Invalid'));
```

### 3. NOLOCK Everywhere

```sql
-- ❌ Anti-pattern: blindly adding NOLOCK to every query
SELECT * FROM Accounts WITH (NOLOCK) WHERE Id = @id;

-- Real risks of dirty reads:
-- • Read partially updated rows (torn pages)
-- • Read rows that will be rolled back
-- • Skip rows or read them twice (page splits during scan)
-- • For financial data: report incorrect balances

-- ✅ Fix: Use RCSI (database-level, no query changes needed)
ALTER DATABASE MyDb SET READ_COMMITTED_SNAPSHOT ON;
-- Readers never block writers WITHOUT dirty read risks
```

### 4. Cursor Loops (RBAR)

```sql
-- ❌ Anti-pattern: processing rows one at a time
DECLARE @id INT, @amount DECIMAL(18,2);
DECLARE cur CURSOR FOR SELECT Id, Amount FROM Orders WHERE Status = 'Pending';
OPEN cur;
FETCH NEXT FROM cur INTO @id, @amount;
WHILE @@FETCH_STATUS = 0
BEGIN
    UPDATE Orders SET ProcessedAmount = @amount * 1.1 WHERE Id = @id;
    FETCH NEXT FROM cur INTO @id, @amount;
END;
CLOSE cur; DEALLOCATE cur;

-- ✅ Fix: set-based operation (100-1000x faster)
UPDATE Orders
SET ProcessedAmount = Amount * 1.1
WHERE Status = 'Pending';
```

**When cursors ARE acceptable:**
- Sending emails/notifications per row (external side effects)
- Running DDL per table (ALTER, index rebuild loops)
- Complex business logic that truly can't be expressed set-based

### 5. Not Using Parameterized Queries

```sql
-- ❌ Anti-pattern: string concatenation (SQL injection + plan cache bloat)
EXEC('SELECT * FROM Users WHERE Name = ''' + @input + '''');

-- Problems:
-- • SQL injection vulnerability
-- • Every unique string = new execution plan (cache bloat)
-- • Can't reuse plans

-- ✅ Fix: sp_executesql with parameters
EXEC sp_executesql
    N'SELECT * FROM Users WHERE Name = @name',
    N'@name NVARCHAR(100)',
    @name = @input;
```

### 6. Implicit Conversions

```sql
-- ❌ Anti-pattern: mismatched types between column and parameter
-- Column: OrderCode VARCHAR(20)
-- Parameter: @code NVARCHAR(20)
SELECT * FROM Orders WHERE OrderCode = @code;
-- SQL Server converts EVERY ROW of OrderCode to NVARCHAR → full scan

-- ✅ Fix: match the parameter type to the column
DECLARE @code VARCHAR(20) = 'ORD-001';
SELECT * FROM Orders WHERE OrderCode = @code;
```

### 7. Functions on Indexed Columns (Non-SARGable)

```sql
-- ❌ Anti-pattern: wrapping indexed columns in functions
WHERE CONVERT(DATE, CreatedDateTime) = '2025-06-01'
WHERE ISNULL(MiddleName, '') = ''
WHERE LEFT(AccountNumber, 3) = 'ACC'
WHERE DATEDIFF(DAY, OrderDate, GETDATE()) < 30

-- ✅ Fix: rewrite to keep column naked
WHERE CreatedDateTime >= '2025-06-01' AND CreatedDateTime < '2025-06-02'
WHERE (MiddleName IS NULL OR MiddleName = '')
WHERE AccountNumber LIKE 'ACC%'
WHERE OrderDate > DATEADD(DAY, -30, GETDATE())
```

### 8. Missing Transaction Handling

```sql
-- ❌ Anti-pattern: no error handling in multi-statement operations
BEGIN TRAN;
INSERT INTO OrderHeaders (...) VALUES (...);
INSERT INTO OrderLines (...) VALUES (...);  -- if this fails, header is orphaned!
COMMIT;

-- ✅ Fix: TRY/CATCH with proper rollback
BEGIN TRY
    BEGIN TRAN;
    INSERT INTO OrderHeaders (...) VALUES (...);
    INSERT INTO OrderLines (...) VALUES (...);
    COMMIT;
END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0 ROLLBACK;
    THROW;  -- re-raise the error
END CATCH;
```

### 9. Over-Indexing

```sql
-- ❌ Anti-pattern: index on every column "just in case"
-- Each index:
--   • Slows down INSERT/UPDATE/DELETE (must maintain all indexes)
--   • Consumes disk space
--   • Can confuse the optimizer (too many choices)

-- Signs of over-indexing:
--   • More indexes than columns
--   • Overlapping indexes (A,B) and (A,B,C) — the second covers both
--   • Indexes with 0 seeks and 0 scans in sys.dm_db_index_usage_stats
```

```sql
-- Find unused indexes
SELECT
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName,
    ius.user_seeks, ius.user_scans, ius.user_lookups, ius.user_updates
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats ius
    ON i.object_id = ius.object_id AND i.index_id = ius.index_id
WHERE OBJECTPROPERTY(i.object_id, 'IsUserTable') = 1
    AND i.index_id > 1  -- skip clustered
    AND (ius.user_seeks + ius.user_scans + ius.user_lookups) = 0
    AND ius.user_updates > 0  -- being maintained but never read
ORDER BY ius.user_updates DESC;
```

### 10. N+1 Query Pattern (from Application Code)

```sql
-- ❌ Anti-pattern: application loops and queries per row
-- App code: for each customer, SELECT orders WHERE customerId = customer.id

-- ✅ Fix: single query with JOIN or batch IN()
SELECT c.Id, c.Name, o.OrderId, o.TotalAmount
FROM Customers c
JOIN Orders o ON c.Id = o.CustomerId
WHERE c.Region = @region;

-- Or batch:
SELECT * FROM Orders WHERE CustomerId IN (SELECT Id FROM Customers WHERE Region = @region);
```

### 11. Large IN() Lists

```sql
-- ❌ Anti-pattern: IN() with thousands of values (from app code)
SELECT * FROM Products WHERE Id IN (1, 2, 3, ... 10000);
-- • Huge query text = parse overhead
-- • Unique plan per unique list = plan cache bloat
-- • Can exceed max query length

-- ✅ Fix: temp table or table-valued parameter
CREATE TYPE dbo.IdList AS TABLE (Id INT);

-- In proc:
CREATE PROCEDURE GetProducts @Ids dbo.IdList READONLY
AS
SELECT p.* FROM Products p
JOIN @Ids i ON p.Id = i.Id;
```

### 12. Trigger Abuse

```sql
-- ❌ Anti-pattern: complex business logic in triggers
-- • Hidden side effects (developers don't see them)
-- • Can't be parameterized or tested easily
-- • Fire on every insert/update/delete (performance)
-- • Recursive trigger chains = debugging nightmare
-- • INSERTED/DELETED tables don't have indexes

-- ✅ Acceptable trigger uses:
-- • Audit logging (simple INSERT into audit table)
-- • Enforcing complex cross-table constraints (last resort)
-- • Maintaining denormalized columns (if no better option)
```

### 13. SELECT INTO Without Thinking

```sql
-- ❌ Anti-pattern: SELECT INTO creates a heap (no indexes, no constraints)
SELECT * INTO #BigTemp FROM HugeTable WHERE Status = 'Active';
-- Then queries against #BigTemp do full table scans

-- ✅ Fix: CREATE TABLE with indexes, then INSERT
CREATE TABLE #BigTemp (
    Id INT PRIMARY KEY,
    Status VARCHAR(20),
    Amount DECIMAL(18,2),
    INDEX IX_Status (Status)
);
INSERT INTO #BigTemp SELECT Id, Status, Amount FROM HugeTable WHERE Status = 'Active';
```

### 14. Catch-All Queries (Kitchen Sink)

```sql
-- ❌ Anti-pattern: one stored proc for all possible filter combinations
CREATE PROCEDURE SearchOrders
    @CustomerId INT = NULL,
    @Status VARCHAR(20) = NULL,
    @StartDate DATE = NULL,
    @EndDate DATE = NULL
AS
SELECT * FROM Orders
WHERE (@CustomerId IS NULL OR CustomerId = @CustomerId)
    AND (@Status IS NULL OR Status = @Status)
    AND (@StartDate IS NULL OR OrderDate >= @StartDate)
    AND (@EndDate IS NULL OR OrderDate <= @EndDate);

-- Problem: ONE execution plan for ALL parameter combinations
-- Plan compiled for NULL params → scan. Reused for specific params → still scans.

-- ✅ Fix: OPTION (RECOMPILE) for catch-all queries
SELECT * FROM Orders
WHERE (@CustomerId IS NULL OR CustomerId = @CustomerId)
    AND (@Status IS NULL OR Status = @Status)
OPTION (RECOMPILE);
-- Fresh plan each time — optimizer eliminates NULL branches

-- ✅ Alternative fix: dynamic SQL with sp_executesql
-- Build WHERE clause dynamically, only include non-NULL filters
-- Each unique combination gets its own cached plan
```

### 15. Not Handling NULLs Properly

```sql
-- ❌ Anti-pattern: comparing with NULL using =
WHERE Status = NULL          -- ALWAYS false (NULL = NULL is unknown)
WHERE Status <> 'Active'     -- doesn't include NULLs!

-- ✅ Fix:
WHERE Status IS NULL
WHERE Status <> 'Active' OR Status IS NULL
WHERE ISNULL(Status, 'Unknown') <> 'Active'  -- but this is non-SARGable!

-- Best: design columns as NOT NULL with meaningful defaults
```


---

## Performance Troubleshooting

### Top Resource-Consuming Queries

```sql
-- Top queries by total CPU time
SELECT TOP 20
    qs.total_worker_time / qs.execution_count AS AvgCPU_us,
    qs.execution_count,
    qs.total_worker_time AS TotalCPU_us,
    qs.total_logical_reads / qs.execution_count AS AvgReads,
    SUBSTRING(st.text, (qs.statement_start_offset / 2) + 1,
        (CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(st.text)
            ELSE qs.statement_end_offset
        END - qs.statement_start_offset) / 2 + 1) AS QueryText
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
ORDER BY qs.total_worker_time DESC;
```

### Currently Running Expensive Queries

```sql
SELECT
    r.session_id,
    r.status,
    r.wait_type,
    r.wait_time,
    r.cpu_time,
    r.logical_reads,
    r.total_elapsed_time / 1000 AS ElapsedSec,
    SUBSTRING(t.text, (r.statement_start_offset / 2) + 1,
        (CASE r.statement_end_offset
            WHEN -1 THEN DATALENGTH(t.text)
            ELSE r.statement_end_offset
        END - r.statement_start_offset) / 2 + 1) AS CurrentStatement,
    p.query_plan
FROM sys.dm_exec_requests r
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
OUTER APPLY sys.dm_exec_query_plan(r.plan_handle) p
WHERE r.session_id > 50  -- skip system sessions
    AND r.session_id <> @@SPID
ORDER BY r.total_elapsed_time DESC;
```

### Wait Stats (What Is SQL Server Waiting On?)

```sql
SELECT TOP 20
    wait_type,
    wait_time_ms / 1000.0 AS WaitTimeSec,
    signal_wait_time_ms / 1000.0 AS SignalWaitSec,
    waiting_tasks_count,
    wait_time_ms * 100.0 / SUM(wait_time_ms) OVER () AS PctOfTotal
FROM sys.dm_os_wait_stats
WHERE wait_type NOT IN (
    'CLR_SEMAPHORE', 'LAZYWRITER_SLEEP', 'RESOURCE_QUEUE',
    'SLEEP_TASK', 'SLEEP_SYSTEMTASK', 'SQLTRACE_BUFFER_FLUSH',
    'WAITFOR', 'LOGMGR_QUEUE', 'CHECKPOINT_QUEUE',
    'REQUEST_FOR_DEADLOCK_SEARCH', 'XE_TIMER_EVENT',
    'BROKER_TO_FLUSH', 'BROKER_TASK_STOP', 'CLR_MANUAL_EVENT',
    'DISPATCHER_QUEUE_SEMAPHORE', 'FT_IFTS_SCHEDULER_IDLE_WAIT',
    'XE_DISPATCHER_WAIT', 'DIRTY_PAGE_POLL', 'HADR_FILESTREAM_IOMGR_IOCOMPLETION'
)
AND waiting_tasks_count > 0
ORDER BY wait_time_ms DESC;
```

### Common Wait Types Decoded

| Wait Type | Meaning | Investigation |
|-----------|---------|---------------|
| `CXPACKET` / `CXCONSUMER` | Parallelism waits | Normal in moderation. High = uneven parallel distribution |
| `PAGEIOLATCH_*` | Waiting for page from disk | Disk I/O bottleneck or insufficient buffer pool |
| `LCK_M_*` | Lock waits (blocking) | Blocking chains, long transactions |
| `SOS_SCHEDULER_YIELD` | CPU pressure | CPU bottleneck, too many active queries |
| `WRITELOG` | Transaction log writes | Slow log disk, frequent small transactions |
| `ASYNC_NETWORK_IO` | Waiting for client to consume results | App not reading results fast enough |
| `PAGELATCH_*` | In-memory page contention | tempdb contention, last-page insert hotspot |

### Parameter Sniffing

```sql
-- Problem: stored proc compiled for one parameter value, plan terrible for others
-- Symptoms: proc is fast for customer A, slow for customer B

-- Diagnosis: compare estimated vs actual rows in execution plan
-- If estimated = 1, actual = 100,000 → parameter sniffing

-- Fixes (in order of preference):

-- 1. OPTIMIZE FOR UNKNOWN (uses average statistics)
CREATE PROCEDURE GetOrders @CustomerId INT
AS
SELECT * FROM Orders WHERE CustomerId = @CustomerId
OPTION (OPTIMIZE FOR UNKNOWN);

-- 2. RECOMPILE (fresh plan each time — CPU cost)
OPTION (RECOMPILE);

-- 3. OPTIMIZE FOR specific value (when you know the typical case)
OPTION (OPTIMIZE FOR (@CustomerId = 1001));

-- 4. Plan guides (DBA-managed, no proc change needed)

-- 5. Query store forced plan (SQL 2016+)
EXEC sp_query_store_force_plan @query_id = 42, @plan_id = 7;
```

### Query Store (SQL 2016+)

```sql
-- Enable query store
ALTER DATABASE MyDb SET QUERY_STORE = ON (
    OPERATION_MODE = READ_WRITE,
    CLEANUP_POLICY = (STALE_QUERY_THRESHOLD_DAYS = 30),
    DATA_FLUSH_INTERVAL_SECONDS = 900,
    MAX_STORAGE_SIZE_MB = 1024
);

-- Find regressed queries (plan changed, got slower)
SELECT
    qsq.query_id,
    qsp.plan_id,
    qsrs.avg_duration / 1000 AS AvgDurationMs,
    qsrs.avg_logical_io_reads,
    qsrs.count_executions,
    CAST(qsp.query_plan AS XML) AS QueryPlan
FROM sys.query_store_query qsq
JOIN sys.query_store_plan qsp ON qsq.query_id = qsp.query_id
JOIN sys.query_store_runtime_stats qsrs ON qsp.plan_id = qsrs.plan_id
WHERE qsrs.avg_duration > 1000000  -- > 1 second
ORDER BY qsrs.avg_duration DESC;
```

### tempdb Contention

```sql
-- Check tempdb file configuration (should have multiple data files)
SELECT
    name, physical_name, size * 8 / 1024 AS SizeMB
FROM sys.master_files
WHERE database_id = 2;

-- Best practice: number of tempdb data files = number of CPU cores (up to 8)
-- All files should be the same size
-- Pre-size files to avoid autogrowth

-- Trace flag 1118: uniform extent allocation (reduces SGAM contention)
-- SQL 2016+: this is the default behavior
```

---

## Quick Reference: Common Patterns

### Upsert (MERGE)

```sql
MERGE INTO Products AS target
USING (VALUES (@Id, @Name, @Price)) AS source(Id, Name, Price)
ON target.Id = source.Id
WHEN MATCHED THEN
    UPDATE SET Name = source.Name, Price = source.Price
WHEN NOT MATCHED THEN
    INSERT (Id, Name, Price) VALUES (source.Id, source.Name, source.Price);

-- ⚠️ MERGE has known bugs with concurrent access. Safer pattern:
BEGIN TRAN;
UPDATE Products SET Name = @Name, Price = @Price WHERE Id = @Id;
IF @@ROWCOUNT = 0
    INSERT INTO Products (Id, Name, Price) VALUES (@Id, @Name, @Price);
COMMIT;
```

### Pagination

```sql
-- OFFSET/FETCH (SQL 2012+) — cleaner syntax
SELECT OrderId, OrderDate, TotalAmount
FROM Orders
WHERE CustomerId = @customerId
ORDER BY OrderDate DESC
OFFSET @pageSize * (@pageNumber - 1) ROWS
FETCH NEXT @pageSize ROWS ONLY;

-- Keyset pagination (faster for deep pages)
SELECT TOP (@pageSize) OrderId, OrderDate, TotalAmount
FROM Orders
WHERE CustomerId = @customerId
    AND (OrderDate < @lastOrderDate
        OR (OrderDate = @lastOrderDate AND OrderId < @lastOrderId))
ORDER BY OrderDate DESC, OrderId DESC;
```

### Batch Deletes (Avoid Lock Escalation)

```sql
-- ❌ Anti-pattern: delete millions in one statement (lock escalation → table lock)
DELETE FROM AuditLog WHERE CreatedDate < DATEADD(YEAR, -2, GETDATE());

-- ✅ Fix: batch delete in chunks
DECLARE @batchSize INT = 10000;
WHILE 1 = 1
BEGIN
    DELETE TOP (@batchSize) FROM AuditLog
    WHERE CreatedDate < DATEADD(YEAR, -2, GETDATE());

    IF @@ROWCOUNT < @batchSize BREAK;

    -- Optional: small delay to reduce log pressure
    WAITFOR DELAY '00:00:01';
END;
```

### String Aggregation

```sql
-- SQL 2017+: STRING_AGG
SELECT
    CustomerId,
    STRING_AGG(ProductName, ', ') WITHIN GROUP (ORDER BY ProductName) AS Products
FROM OrderDetails
GROUP BY CustomerId;

-- Pre-2017: FOR XML PATH (legacy but common)
SELECT
    c.CustomerId,
    STUFF((
        SELECT ', ' + od.ProductName
        FROM OrderDetails od
        WHERE od.CustomerId = c.CustomerId
        ORDER BY od.ProductName
        FOR XML PATH('')
    ), 1, 2, '') AS Products
FROM Customers c;
```

### JSON Operations (SQL 2016+)

```sql
-- Parse JSON
SELECT
    JSON_VALUE(Data, '$.name') AS Name,
    JSON_VALUE(Data, '$.address.city') AS City,
    JSON_QUERY(Data, '$.tags') AS TagsArray
FROM Documents
WHERE ISJSON(Data) = 1;

-- Generate JSON
SELECT Id, Name, Email
FROM Users
WHERE IsActive = 1
FOR JSON PATH, ROOT('users');

-- OPENJSON for shredding arrays
SELECT item.*
FROM Orders o
CROSS APPLY OPENJSON(o.LineItemsJson)
WITH (
    ProductId INT '$.productId',
    Quantity INT '$.quantity',
    Price DECIMAL(18,2) '$.price'
) item;
```

---

## Performance Checklist (Before Production)

- [ ] No `SELECT *` in application queries
- [ ] All WHERE clause columns are SARGable
- [ ] Covering indexes for high-frequency queries (no key lookups)
- [ ] Parameterized queries from application code (no string concatenation)
- [ ] Parameter sniffing addressed for stored procs with variable data distribution
- [ ] Transaction scope is minimal (no user interaction inside transactions)
- [ ] Batch large DML operations (avoid lock escalation)
- [ ] RCSI enabled (read-write contention elimination)
- [ ] tempdb has multiple data files sized equally
- [ ] Statistics up to date (maintenance plan)
- [ ] Index fragmentation maintained (rebuild > 30%, reorganize 10-30%)
- [ ] No implicit conversions in execution plans
- [ ] Query Store enabled for plan regression detection
- [ ] Alerts on blocking chains > 30 seconds
- [ ] No cursors for set-based-solvable operations

---

## References

- `steering/preferences/stack/mssql/query-performance.md` — Concise decision matrices, DMV diagnostic queries, index type hierarchy (drives the `mssql-query-performance` skill)
- `steering/preferences/stack/csharp/efcore-query-patterns.md` — EF Core patterns (EF generates SQL this doc helps optimize)
- `steering/preferences/stack/csharp/dapper-antipatterns.md` — Dapper anti-patterns (Dapper executes raw SQL covered here)
