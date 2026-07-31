---
name: general-debug
description: Diagnose and fix issues — reading service logs, tracing React rendering problems, debugging network/API errors, profiling performance, or inspecting state management. NOT for writing tests (use test skill) or deploying fixes (use deploy skill).
---

# Debug

## Environment Scope

**write+validate** — Reads logs, source files, and config. May add temporary debug instrumentation (console.log, breakpoints) that is removed before completion. Runs diagnostic commands (`tilt logs`, `curl`, `git diff`). Does NOT modify production systems or deploy.

## Workflow

1. **Reproduce** — Confirm the issue is reproducible. Ask user for specific steps, environment, and error messages if not provided.
2. **Isolate** — Determine which layer the issue is in: frontend rendering, network/API, state management, backend service, database, or infrastructure.
3. **Gather Evidence** — Read relevant logs, source code, and config for the isolated layer. Bounded: read only files in the suspected area.
4. **Form Hypothesis** — Present a diagnosis with supporting evidence to the user.
5. **Await Approval** — Propose a fix. Do NOT modify code until user confirms the approach.
6. **Fix** — Apply the minimal targeted fix.
7. **Verify** — Reproduce the original steps — issue should be resolved. Run related tests. If still failing, enter failure loop.
8. **Clean Up** — Remove any debug instrumentation. Add a regression test if one doesn't exist.

### Failure Recovery (max 3 retries)

7a. Issue still reproduces → re-examine evidence, form new hypothesis
7b. Apply alternative fix
7c. Re-verify
7d. After 3 failures → present all attempted approaches to user, ask for new direction

### Rollback

If fix makes things worse:
1. Revert the fix (`git checkout -- <modified files>`)
2. Confirm original behavior is restored (even if still broken, at least not worse)
3. Report what was tried and why it didn't work

## Reading Logs from Tilt Services

- View all service logs: `tilt logs`
- Filter by service: `tilt logs --resource <service-name>`
- Follow live: `tilt logs -f --resource <service-name>`
- Check Tilt UI at http://localhost:10350 for build/deploy status
- Look for crash loops in the resource sidebar

## Debugging React Rendering Issues

- Identify unnecessary re-renders with React DevTools Profiler (highlight updates)
- Check for:
  - Unstable references in props (new objects/arrays created each render)
  - Missing or incorrect dependency arrays in `useEffect`/`useMemo`
  - State updates in render path (infinite loop)
  - Context providers re-rendering all consumers

```tsx
// Quick debug hook
function useWhyDidYouRender(name: string, props: Record<string, unknown>) {
  const prev = useRef(props);
  useEffect(() => {
    const changes = Object.entries(props).filter(
      ([key, val]) => prev.current[key] !== val
    );
    if (changes.length) console.log(`[${name}] changed:`, changes);
    prev.current = props;
  });
}
```

## Network / API Debugging

- Browser DevTools Network tab: filter by XHR/Fetch
- Check request/response payloads, status codes, timing
- For CORS issues: verify `Access-Control-*` headers on the response
- For auth failures: check token expiry, cookie domain, credentials mode
- Use `curl` to isolate frontend vs backend issues:

```bash
curl -v http://localhost:3000/api/endpoint \
  -H "Authorization: Bearer $TOKEN"
```

## State Management Debugging

- Zustand: use `devtools` middleware for Redux DevTools integration
- React Query DevTools: check cache status, refetch triggers, stale time
- Common issues:
  - Stale closures capturing old state
  - Selectors returning new references on every call
  - Mutations not invalidating dependent queries

## Performance Profiling

- **Frontend**: Lighthouse, React Profiler, `performance.mark()`/`performance.measure()`
- **Bundle size**: `npx vite-bundle-visualizer` or `source-map-explorer`
- **Backend**: structured logging with timing, `clinic.js` for Node services
- **Distributed tracing**: Jaeger UI at the Tilt-mapped port for request flow across services (see `steering/orchestration/local-dev.md` for port mappings)
- **Database**: enable slow query logging, check `EXPLAIN ANALYZE`

## Guardrails

- NEVER deploy a fix to production without testing locally first
- NEVER leave debug instrumentation (console.log, debugger statements) in committed code
- NEVER modify production databases during debugging — use read-only queries
- NEVER skip adding a regression test after fixing a bug
- NEVER assume the first hypothesis is correct — verify with evidence before fixing
- NEVER read entire log files into context — filter by service, time range, or error pattern

## References

- `steering/orchestration/local-dev.md` — Tilt service topology, port mappings, and how to restart services
- `steering/preferences/stack/react/dependency-graph.md` — Understanding data flow and component relationships for tracing bugs
