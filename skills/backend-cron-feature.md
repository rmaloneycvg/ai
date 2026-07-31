---
name: backend-cron-feature
description: Add or modify scheduled/cron jobs and background workers. Covers Celery tasks, Node.js BullMQ scheduling, C# hosted services, retry logic, and monitoring. NOT for REST API endpoints (use backend-rest-api-feature) or deployment (use deploy).
---

# Backend Cron / Scheduled Job Feature

## Environment Scope

**write+validate** — Writes task definitions, schedules, worker configs, and tests. Runs type check to validate compilation. Does NOT start workers or execute tasks — instructs user to run `tilt up` or deploy.

## Workflow

1. **Check Existing State** — Does a task with this name/schedule already exist? Search task/job definitions. If it exists, ask if user wants to modify schedule, logic, or create a new task.
2. **Gather Context** — Identify which stack is in use (Python/Celery, Node/BullMQ, C#/IHostedService, K8s CronJob). Read existing task structure and schedule config.
3. **Generate Spec** — List: task name, schedule (crontab expression), inputs, retry policy, timeout, files to create/modify. Present as EARS requirements.
4. **Await Approval** — Present the spec. Do NOT write code until user confirms.
5. **Implement** — Create task definition, schedule config, worker entry, and test.
6. **Verify** — Run type check or `python -m py_compile <file>`. Expected: <10s. If fails, enter failure loop.
7. **Document** — Add to project README (schedule table). Update Tilt config if new worker needed.

### Failure Recovery (max 3 retries)

6a. Read error → identify import issue, type error, or config syntax problem
6b. Fix the specific file
6c. Re-verify
6d. After 3 failures → show errors to user, ask for guidance

### Rollback

If user cancels mid-implementation:
1. Delete new task/worker files
2. Revert schedule config changes (beat_schedule or queue definitions)
3. Revert Tiltfile additions if any
4. Confirm with `git diff --stat`

## Architecture Options

| Stack | Tool | Use Case |
|-------|------|----------|
| Python | Celery Beat + Worker | Complex task graphs, retries, rate limiting |
| Node.js | BullMQ | Redis-backed queues with scheduling |
| C# | IHostedService + Timer | In-process scheduling for .NET services |
| C# | Hangfire | Dashboard, persistence, complex scheduling |
| Any | Kubernetes CronJob | Isolated execution, no long-running process |

## Celery Task (Python)

```python
from celery import shared_task

@shared_task(bind=True, max_retries=3, default_retry_delay=60, acks_late=True)
def generate_daily_report(self, report_date: str):
    try:
        data = fetch_metrics(report_date)
        report = build_report(data)
        store_report(report)
    except TransientError as exc:
        raise self.retry(exc=exc)
```

### Beat Schedule
```python
from celery.schedules import crontab

beat_schedule = {
    'daily-report': {
        'task': 'tasks.reports.generate_daily_report',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

## Node.js (BullMQ)

```typescript
import { Queue, Worker } from 'bullmq';

const reportQueue = new Queue('reports', { connection: redis });

await reportQueue.add('daily-report', {}, {
  repeat: { pattern: '0 2 * * *' },
});

const worker = new Worker('reports', async (job) => {
  await generateReport(job.data.date);
}, {
  connection: redis,
  concurrency: 1,
  attempts: 3,
  backoff: { type: 'exponential', delay: 5000 },
});
```

## C# Hosted Service

```csharp
public class DailyReportService : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            var nextRun = GetNext2AM(DateTimeOffset.UtcNow);
            await Task.Delay(nextRun - DateTimeOffset.UtcNow, ct);

            using var scope = _scopeFactory.CreateScope();
            var svc = scope.ServiceProvider.GetRequiredService<IReportService>();
            await svc.GenerateDailyReportAsync(ct);
        }
    }
}
```

## Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: daily-report
spec:
  schedule: "0 2 * * *"
  concurrencyPolicy: Forbid
  jobTemplate:
    spec:
      backoffLimit: 3
      activeDeadlineSeconds: 3600
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: report
              image: report-generator:latest
              command: ["python", "-m", "tasks.reports"]
```

## Error Handling & Retry

- **Idempotency** — every job must be safe to re-run
- **Dead letter queue** — failed jobs after max retries go to DLQ
- **Alerting** — alert on 3+ consecutive failures
- **Timeout** — every job has a max execution time
- **Locking** — use distributed lock if job must not overlap

## Tilt Integration

```python
docker_build('celery-worker', './services/worker')
k8s_yaml('deploy/celery-worker.yaml')
k8s_resource('celery-worker', port_forwards='5555:5555', labels=['background'])
```

## Guardrails

- NEVER create a scheduled task without an idempotency check (safe to re-run)
- NEVER skip retry logic — every task must define max_retries and backoff strategy
- NEVER create a task without a timeout (prevents infinite hangs)
- NEVER deploy a cron job without monitoring/alerting for consecutive failures
- NEVER schedule overlapping executions without a distributed lock
- NEVER skip integration test with mocked clock/queue

## Checklist

- [ ] Task/job defined with clear inputs
- [ ] Schedule configured (crontab expression documented)
- [ ] Retry logic with max attempts and backoff
- [ ] Idempotent execution (safe to re-run)
- [ ] Timeout configured
- [ ] Error handling with logging
- [ ] Monitoring/alerting set up
- [ ] Added to Tilt (worker + beat/scheduler)
- [ ] Integration test with mocked clock/queue
- [ ] Documented in project README

## References

- `steering/orchestration/local-dev.md` — Tilt service topology, Celery worker setup, k8s CronJob patterns
- `skills/general-deploy.md` — Deploying cron workers via Terraform
- `skills/general-test.md` — Testing async jobs and scheduled tasks
