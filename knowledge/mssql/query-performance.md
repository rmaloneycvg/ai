---
inclusion: manual
---

# MSSQL Query Performance Patterns

## Why This Exists

SQL performance decisions require both static code analysis AND runtime data from the database. Without a structured approach, developers either over-index (hurting write performance) or under-index (hurting read performance). This document defines the decision hierarchies, detection rules, and diagnostic workflows that the mssql-query-performance skill follows prescriptively.

---

## Index Naming Convention

All indexes must follow: `IX_[TYPE]_[TableName]_[TableName]...`

Where TableName entries are the tables whose columns participate in the index (joined tables used in the query the index supports).

| Index Type | Abbreviation | Example |
|-----------|-------------|---------|
| Non-Clustered | NC | `IX_NC_Orders_Customers` |
| Clustered | CL | `IX_CL_Orders` |
| Unique Non-Clustered | UQ | `IX_UQ_Users` |
| Unique Clustered | UCL | `IX_UCL_Orders` |
| Columnstore | CS | `IX_CS_Sales` |
| Filtered | FLT | `IX_FLT_Orders` |
| Covering (has INCLUDEs) | COV | `IX_COV_Orders_Customers` |

Rules:
- Table names in PascalCase matching the actual table name
- Multiple table names when the index supports a JOIN between those tables
- If the index only involves one table, single table name
- Never abbreviate table names in the index name

---

## 1. Anti-Pattern Detection Rules

### WHERE Clause Anti-Patterns

| Anti-Pattern | Detection Signal | Severity | Fix |
|-------------|-----------------|----------|-----|
| Non-SARGable: function on column | `WHERE YEAR(col)`, `WHERE ISNULL(col, x)`, `WHERE CAST(col AS...)`, `WHERE LEFT(col, n)` | Critical | Rewrite to range predicate or OR pattern |
| Non-SARGable: arithmetic on column | `WHERE col + 1 = x`, `WHERE col * 2 > y` | Critical | Move arithmetic to the other side |
| Implicit conversion | Parameter type doesn't match column type (NVARCHAR param vs VARCHAR column) | Critical | Match parameter type to column type |
| Leading wildcard | `WHERE col LIKE '%value'` | High | Full-text index or reverse the string pattern |
| OR that prevents seek | `WHERE colA = x OR colB = y` | High | Rewrite as UNION ALL of two seeks |
| NOT IN with NULLable column | `WHERE col NOT IN (SELECT nullable_col...)` | High | Use NOT EXISTS instead |
| Redundant IS NOT NULL | `WHERE col = @val AND col IS NOT NULL` | Low | Remove redundant check (equality implies NOT NULL) |

### GROUP BY Anti-Patterns

| Anti-Pattern | Detection Signal | Severity | Fix |
|-------------|-----------------|----------|-----|
| GROUP BY on non-indexed columns (large table) | GROUP BY cols don't match any index leading columns | High | Add covering index or columnstore |
| GROUP BY with function/expression | `GROUP BY YEAR(OrderDate)`, `GROUP BY col1 + col2` | High | Add computed column + index, or pre-materialize |
| Unnecessary DISTINCT when GROUP BY suffices | SELECT DISTINCT + aggregate in same logical need | Medium | Replace with GROUP BY |
| GROUP BY ALL columns to get one aggregate | Grouping by many columns when a window function is cleaner | Medium | Rewrite with window function |
| SELECT columns not in GROUP BY or aggregate | Missing aggregate wrapper (SQL Server will error, but indicates design confusion) | Low | Fix query logic |

### HAVING Anti-Patterns

| Anti-Pattern | Detection Signal | Severity | Fix |
|-------------|-----------------|----------|-----|
| Filtering on non-aggregate in HAVING | `HAVING Status = 'Active'` (should be WHERE) | High | Move to WHERE — executes before aggregation, fewer rows to process |
| HAVING COUNT(*) > 0 | Equivalent to EXISTS | Medium | Rewrite with EXISTS for clarity and possible plan improvement |
| HAVING on column available pre-aggregation | Filter could reduce rows BEFORE grouping | High | Move filter to WHERE |

### APPLY Misuse / Missing APPLY

**When APPLY is REQUIRED (JOIN cannot do this):**
- Calling a table-valued function with outer row values as parameters
- Top-N per group pattern (TOP + ORDER BY correlated to outer)
- Unpivoting columns to rows with VALUES
- Correlated subquery returning multiple columns

**When APPLY is SUPERIOR to JOIN:**
- Small outer set + indexed inner lookup (seek + TOP stops early)
- Optional correlated lookup (OUTER APPLY cleaner than LEFT JOIN + subquery)

**When JOIN is SUPERIOR to APPLY:**
- Large table to large table equi-join (hash/merge join parallelism)
- Many-to-many relationships
- Large outer set with no good inner index (hash join doesn't need index)
- Any non-correlated set operation

**Detection Rules:**

| Signal | Recommendation |
|--------|---------------|
| JOIN with ROW_NUMBER() OVER PARTITION BY + WHERE rn <= N | Replace with CROSS APPLY TOP N |
| Multiple correlated scalar subqueries in SELECT for same table | Replace with single CROSS APPLY |
| CROSS APPLY on large-to-large without TOP or WHERE | Replace with JOIN |
| LEFT JOIN to a subquery with TOP 1 correlated to outer | Replace with OUTER APPLY |


---

## 2. Index Type Decision Hierarchy

Apply top-to-bottom. First matching rule wins.

| Query Pattern | Table Rows | Current Index State | Recommended Type | Rationale |
|--------------|-----------|-------------------|-----------------|-----------|
| Heavy aggregation (SUM, AVG, COUNT) scanning full table or large range | > 1M rows | No columnstore exists | CS (Columnstore) | Batch mode + compression = orders of magnitude faster for analytics |
| Heavy aggregation on smaller table | < 1M rows | No covering index | COV (Covering NC with INCLUDE) | Avoids key lookups, small enough that NC is efficient |
| Equality filter(s) + range filter | Any | No composite index on those cols | NC (composite: equality cols first, range col last) | Seek on equality, range scan on final col |
| Equality filter(s) only | Any | No index on those cols | NC (composite on equality cols) | Index seek |
| Top-N per group (APPLY pattern) | Any | No index on (group_col, sort_col) | NC (group_col, sort_col DESC) + INCLUDE output cols | Enables seek + TOP early termination |
| Frequently filtered sparse subset (< 30% of rows match) | Any | No filtered index | FLT (Filtered NC) | Smaller index, faster maintenance, only relevant rows |
| JOIN FK column with high selectivity | Any | No index on FK | NC on FK column + INCLUDE frequently selected cols | Nested loop seek on inner |
| Unique constraint needed | Any | No unique index | UQ | Enforce data integrity + serves as a seek target |
| Sort/ORDER BY without TOP (full sort) | > 100K rows | No index in sort order | NC in sort order | Eliminates explicit Sort operator |

### When to Recommend Columnstore over Non-Clustered

- Table > 1M rows AND query does full/large-range aggregation
- Query touches > 50% of table rows (scan is inevitable, columnstore makes scans fast)
- Reporting/analytics workload on OLTP table → non-clustered columnstore (doesn't replace clustered)
- Multiple aggregate queries on different column combinations → one columnstore covers all

### When NOT to Recommend Columnstore

- Table < 100K rows (overhead not justified)
- Primarily point-lookup queries (seek patterns need B-tree)
- Very write-heavy table with minimal read aggregation (columnstore maintenance cost)
- Narrow, highly selective queries (B-tree NC is better)


---

## 3. DMV Diagnostic Queries

### 3a. Table Size and Row Count

```sql
SELECT
    SCHEMA_NAME(t.schema_id) AS SchemaName,
    t.name AS TableName,
    SUM(p.rows) AS RowCount,
    SUM(a.total_pages) * 8 / 1024 AS TotalSizeMB,
    SUM(a.used_pages) * 8 / 1024 AS UsedSizeMB
FROM sys.tables t
JOIN sys.indexes i ON t.object_id = i.object_id
JOIN sys.partitions p ON i.object_id = p.object_id AND i.index_id = p.index_id
JOIN sys.allocation_units a ON p.partition_id = a.container_id
WHERE t.name IN ('{TABLE_NAMES}')  -- Replace with actual table names from query
GROUP BY t.schema_id, t.name
ORDER BY RowCount DESC;
```

### 3b. Current Index Usage Stats

```sql
SELECT
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName,
    i.type_desc AS IndexType,
    ius.user_seeks,
    ius.user_scans,
    ius.user_lookups,
    ius.user_updates,
    ius.last_user_seek,
    ius.last_user_scan
FROM sys.indexes i
LEFT JOIN sys.dm_db_index_usage_stats ius
    ON i.object_id = ius.object_id AND i.index_id = ius.index_id AND ius.database_id = DB_ID()
WHERE OBJECT_NAME(i.object_id) IN ('{TABLE_NAMES}')
    AND i.type > 0
ORDER BY OBJECT_NAME(i.object_id), i.index_id;
```

### 3c. Missing Index Suggestions for Target Tables

```sql
SELECT
    OBJECT_NAME(mid.object_id) AS TableName,
    mid.equality_columns,
    mid.inequality_columns,
    mid.included_columns,
    migs.avg_user_impact AS AvgImpactPct,
    migs.user_seeks AS TimesNeeded,
    migs.avg_total_user_cost AS AvgQueryCost,
    ROUND(migs.avg_user_impact * migs.user_seeks * migs.avg_total_user_cost, 2) AS ImprovementScore
FROM sys.dm_db_missing_index_details mid
JOIN sys.dm_db_missing_index_groups mig ON mid.index_handle = mig.index_handle
JOIN sys.dm_db_missing_index_group_stats migs ON mig.index_group_handle = migs.group_handle
WHERE mid.database_id = DB_ID()
    AND OBJECT_NAME(mid.object_id) IN ('{TABLE_NAMES}')
ORDER BY ImprovementScore DESC;
```

### 3d. Index Fragmentation

```sql
SELECT
    OBJECT_NAME(ips.object_id) AS TableName,
    i.name AS IndexName,
    ips.index_type_desc,
    ips.avg_fragmentation_in_percent,
    ips.page_count,
    ips.record_count
FROM sys.dm_db_index_physical_stats(DB_ID(), NULL, NULL, NULL, 'LIMITED') ips
JOIN sys.indexes i ON ips.object_id = i.object_id AND ips.index_id = i.index_id
WHERE OBJECT_NAME(ips.object_id) IN ('{TABLE_NAMES}')
    AND ips.page_count > 100
ORDER BY ips.avg_fragmentation_in_percent DESC;
```

### 3e. Top Queries by Logical Reads for Target Tables

```sql
SELECT TOP 10
    qs.total_logical_reads / qs.execution_count AS AvgLogicalReads,
    qs.execution_count,
    qs.total_worker_time / qs.execution_count AS AvgCPU_us,
    SUBSTRING(st.text, (qs.statement_start_offset / 2) + 1,
        (CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(st.text)
            ELSE qs.statement_end_offset
        END - qs.statement_start_offset) / 2 + 1) AS QueryText
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st
WHERE st.text LIKE '%{TABLE_NAME}%'
ORDER BY qs.total_logical_reads DESC;
```

### 3f. Existing Index Definitions (Columns + Includes)

```sql
SELECT
    OBJECT_NAME(i.object_id) AS TableName,
    i.name AS IndexName,
    i.type_desc,
    i.is_unique,
    i.filter_definition,
    STRING_AGG(CASE WHEN ic.is_included_column = 0 THEN c.name END, ', ')
        WITHIN GROUP (ORDER BY ic.key_ordinal) AS KeyColumns,
    STRING_AGG(CASE WHEN ic.is_included_column = 1 THEN c.name END, ', ')
        WITHIN GROUP (ORDER BY ic.index_column_id) AS IncludedColumns
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
WHERE OBJECT_NAME(i.object_id) IN ('{TABLE_NAMES}')
    AND i.type > 0
GROUP BY i.object_id, i.name, i.type_desc, i.is_unique, i.filter_definition
ORDER BY OBJECT_NAME(i.object_id), i.name;
```


---

## 4. Temp Table vs Table Variable Decision Matrix

| Factor | Temp Table (#) | Table Variable (@) | Recommendation |
|--------|:-:|:-:|---|
| Row count > 1000 | ✅ | ❌ | Temp table — optimizer gets accurate statistics |
| Row count < 100 | ⚠️ | ✅ | Table variable — less overhead, no tempdb contention |
| Row count 100–1000 | ✅ | ⚠️ | Temp table preferred — statistics help optimizer |
| Need index on intermediate results | ✅ | ⚠️ | Temp table — full index support |
| Referenced multiple times in query | ✅ | ✅ | Temp table if > 100 rows (CTE re-executes!) |
| Inside a transaction (need rollback behavior) | ⚠️ | ✅ | Table variable NOT rolled back — intentional? |
| High-concurrency proc (tempdb contention) | ⚠️ | ✅ | Table variable for tiny results to avoid tempdb |
| JOIN target with large table | ✅ | ❌ | Temp table — statistics prevent bad join strategy |
| Schema needs ALTER during proc | ✅ | ❌ | Table variable schema is fixed at declaration |

**Critical Rule:** Table variables ALWAYS estimate 1 row to the optimizer (until SQL 2019 with deferred compilation). If the table variable feeds into a JOIN or is filtered, the optimizer produces terrible plans for anything over ~100 rows. Default to temp tables unless you have a specific reason not to.

**SELECT INTO vs CREATE TABLE + INSERT:**
- SELECT INTO creates a heap (no indexes, no constraints) — fine for quick temp data you'll scan once
- CREATE TABLE + INSERT when you need indexes on the temp table for subsequent joins/lookups

---

## 5. Indexed View Recommendations

### When to Recommend

- Same expensive aggregation JOIN runs frequently (> 10x/hour)
- Aggregation involves GROUP BY on columns from multiple joined tables
- Underlying tables have moderate write rate (not > 1000 inserts/sec)
- Query improvement justifies the write overhead

### Requirements (SQL Server Enforces These)

- View must be created WITH SCHEMABINDING
- All functions must be deterministic
- No OUTER JOIN, UNION, subqueries, DISTINCT, TOP, ORDER BY, HAVING without GROUP BY
- No APPLY, EXCEPT, INTERSECT
- Must use COUNT_BIG(*) if any aggregate is used
- All GROUP BY columns + aggregates must be in the SELECT

### Trade-offs

| Benefit | Cost |
|---------|------|
| Reads from the view are instant (pre-computed) | Every INSERT/UPDATE/DELETE on base tables must update the indexed view |
| Eliminates repeated aggregation joins | Schema changes to base tables may break the view |
| Optimizer can use the indexed view even if query doesn't reference it | Storage for materialized results |

### Template

```sql
CREATE VIEW dbo.vw_{DescriptiveName}
WITH SCHEMABINDING
AS
SELECT
    {group_columns},
    COUNT_BIG(*) AS RowCount,
    SUM({agg_column}) AS Total{AggColumn}
FROM dbo.{Table1}
JOIN dbo.{Table2} ON ...
GROUP BY {group_columns};
GO

CREATE UNIQUE CLUSTERED INDEX IX_UCL_vw_{Name}
ON dbo.vw_{DescriptiveName}({group_columns});
```

---

## 6. Gap Detection Checklist

Run after primary analysis to find remaining optimization opportunities:

- [ ] Key Lookup in execution plan → add INCLUDE columns to existing index
- [ ] Sort operator with spill → add index in sort order
- [ ] CTE referenced multiple times → replace with temp table
- [ ] Catch-all stored proc (optional WHERE params) → add OPTION(RECOMPILE)
- [ ] Parameter sniffing symptoms → check estimated vs actual rows
- [ ] Large IN() list from app code → table-valued parameter
- [ ] Cursor processing set-based-solvable data → rewrite as single statement
- [ ] NOLOCK hints → recommend RCSI instead
- [ ] SELECT * in production queries → explicit column list
- [ ] Missing error handling in multi-statement transactions → TRY/CATCH
- [ ] Large single DELETE/UPDATE → batch in chunks to prevent lock escalation
- [ ] Scalar UDF in WHERE/SELECT → rewrite as inline TVF or JOIN
- [ ] Repeated subquery that could be an indexed view → evaluate indexed view

---

## Anti-Patterns (Quick Reference)

For full patterns and code examples, see `docs/mssql-cheatsheet.md` Anti-Patterns section (15 anti-patterns with before/after code).

Key categories detected by the skill:

1. Non-SARGable WHERE predicates
2. Implicit type conversions
3. Scalar functions per-row
4. Cursor/RBAR patterns
5. Missing parameterization
6. Over-indexing / unused indexes
7. Catch-all query without RECOMPILE
8. NULL handling errors
9. SELECT INTO without subsequent indexing
10. APPLY misuse (using where JOIN is better, or missing where APPLY is needed)

---

## References

- `docs/mssql-cheatsheet.md` — Full SQL Server patterns, execution plan reading, locking, all 15 anti-patterns with code examples
- `steering/preferences/stack/csharp/api-caching.md` — Caching patterns that complement query-level optimizations (cache before you optimize the query)
