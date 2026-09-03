# Description

Steps to instrument and quantify sql server schema drift a vm infrastructure with multiple tenants with different database schemas :

## Delivery Plan

### Baseline vs. Static Drift Measurement

1. Find the static gold standard schema.  

**Automated DACPAC Extraction:** Use `SqlPackage.exe` in a PowerShell script to extract a `.dacpac` of your Gold schema. Then, loop through all 100+ tenant databases and run a `DeployReport` or `DriftReport` against them.
* **The Drift Matrix:** Push the output of those reports into a central tracking database. You are looking to categorize the drift into three buckets:
* *Additive:* Custom tables or columns added for specific tenants (Annoying, but usually safe to migrate).
* *Subtractive:* Missing indexes or deprecated tables (Performance risk).
* *Mutative:* Modified stored procedures where the financial calculation logic actually differs from the Gold standard (High risk - this breaks lift-and-shift and requires code refactoring).



### 2. Instrumenting Active Drift (Real-Time)

Since you are in a regulated finance environment, you must know if support teams or DBAs are actively making hotfixes that increase drift *right now*.

* **Server-Scoped DDL Triggers:** Implement a Server-Level DDL trigger (`ON ALL SERVER FOR DDL_DATABASE_LEVEL_EVENTS`). Have this trigger capture `EVENTDATA()` (which contains the exact `ALTER` or `CREATE` script, the user, and the time) and write it to a centralized, secured Audit database.
* **Extended Events (XEvents):** If DDL triggers introduce too much overhead or risk, configure a SQL Server Extended Event session tracking `object_altered`, `object_created`, and `object_deleted`.

### 3. Tying Drift to Performance Metrics

Once you know *what* is different, you must instrument how that difference affects compute.

* **Hash the Stored Procedures:** Write a script that loops through `sys.sql_modules`, hashes the definition of your heavy financial calculation procs, and logs the hash alongside the Tenant ID.
* **Correlate with Query Store:** When you pull your Query Store metrics (CPU time, logical reads) for those calculations, group the results by the Procedure Hash. This definitively proves whether a customized tenant proc is consuming more VMware CPU than the standard proc.

If you don't map this out, you will size your target cloud database based on the "average" tenant, and the custom tenants will crash the node.
