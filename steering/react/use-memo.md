---
name: ReactUseMemo
description: Steering for useMemo — memoizing expensive computations and stabilizing object references for memoized children
inclusion: manual
fileMatchPattern: [
  "**/src/**/*.tsx",
  "**/src/**/*.jsx",
  "**/src/**/*.ts",
  "**/src/**/*.js"
]
---

# useMemo Steering

## When to Use

- Expensive computation that shouldn't re-run on every render (filtering/sorting large arrays, complex transforms)
- Stabilizing an object/array reference passed to a memoized child component
- Derived value used as a dependency in `useEffect` or `useCallback` — prevents unnecessary effect re-runs
- Computing a value from props/state that costs > 1ms (profile first with `console.time`)

**Note:** React Compiler (React 19+) automatically memoizes expressions. In compiled codebases, manual `useMemo` is rarely needed. Only add it when profiling confirms a measurable performance problem.

## Best Practices

- Profile before memoizing — `useMemo` has overhead (dependency comparison on every render). Only worth it if the computation is genuinely expensive
- Keep dependency arrays tight — every dep is a potential cache invalidation
- If you're memoizing a simple object literal to stabilize identity, consider hoisting it outside the component or using `useRef` for truly static values
- Never depend on `useMemo` for correctness — React may discard cached values at any time. Code must work without it (just slower)

## Example Use

### Expensive filtering

```tsx
function UserTable({ users, searchTerm }: { users: User[]; searchTerm: string }) {
  const filteredUsers = useMemo(() => {
    return users.filter((user) =>
      user.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [users, searchTerm]);

  return <AgGridReact rowData={filteredUsers} columnDefs={columns} />;
}
```

### Stabilizing a derived object for a memoized child

```tsx
function ChartContainer({ revenue, expenses }: Props) {
  const chartData = useMemo(
    () => revenue.map((r, i) => ({ month: r.month, revenue: r.value, expenses: expenses[i]?.value ?? 0 })),
    [revenue, expenses],
  );

  return <RevenueChart data={chartData} />;
}

const RevenueChart = React.memo(function RevenueChart({ data }: { data: ChartPoint[] }) {
  return (
    <ResponsiveContainer>
      <LineChart data={data}>
        <Line dataKey="revenue" />
        <Line dataKey="expenses" />
      </LineChart>
    </ResponsiveContainer>
  );
});
```

## Pitfalls (react.dev Caveats)

- **Undefined return** — using `() => { ... }` with curly braces requires an explicit `return`. Arrow without braces (`() => expression`) returns implicitly. Missing `return` inside `{}` yields `undefined`
- **Cannot call in loops** — extract the loop body into a separate component that calls `useMemo` internally
- **Strict Mode calls calculation twice** — in development only. Ensures the calculation is pure. If you see doubled logs, this is expected
- **Cache can be thrown away** — React discards memoized values when a component suspends offscreen or during memory pressure. Never use `useMemo` as a semantic guarantee
- **Dependency comparison is shallow** — objects/arrays in deps must be referentially stable or the memo breaks every render. Stabilize them first (hoist, `useMemo` them separately, or use primitives)
- **New object in deps every render** — `useMemo(() => compute(obj), [obj])` where `obj` is created inline above breaks memoization. Move `obj` creation into its own `useMemo` or extract primitives

## Error Handling

- `useMemo` itself doesn't catch errors — if the calculation throws, the error propagates to the nearest error boundary
- Don't perform side effects inside `useMemo` — it's called during render. Errors from side effects here corrupt the render tree
- For async computations, use TanStack Query — `useMemo` is synchronous only

## Works With

| Hook | Relationship |
|------|-------------|
| `React.memo` | `useMemo` stabilizes props so `React.memo`'s shallow comparison succeeds |
| `useCallback` | Often paired — memoize data with `useMemo`, memoize handlers with `useCallback` |
| `useEffect` | Memoized value as a dep prevents unnecessary effect re-runs |
| `useDeferredValue` | Defer expensive filter input, then `useMemo` the filtered result |
| `useRef` | For truly static values that never change, `useRef` is cheaper than `useMemo(() => x, [])` |

## Anti-Patterns

- ❌ Memoizing trivial operations (simple math, string concatenation) — overhead exceeds savings
- ❌ Using `useMemo` for side effects (API calls, subscriptions, DOM manipulation)
- ❌ Memoizing a value with no memoized consumer — if nothing compares the reference, stabilization is pointless
- ❌ Empty dependency array for a value that depends on props/state — produces stale data
- ❌ Wrapping every derived value in `useMemo` "just in case" — adds noise, hurts readability, and React Compiler handles this automatically
- ❌ Using `useMemo` to create initial state — use `useState(() => expensiveInit())` lazy initializer instead
