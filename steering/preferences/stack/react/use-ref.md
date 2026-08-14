---
inclusion: manual
---

# useRef Steering

## When to Use

- Holding a reference to a DOM element (focus management, measuring dimensions, scrolling)
- Storing a mutable value that persists across renders but does **not** trigger re-renders when changed (timers, previous values, instance references)
- Holding third-party library instances (map objects, chart instances, WebSocket connections)
- Tracking whether a component is mounted (for async cleanup patterns)
- Reading the latest value of a prop/state inside a callback without adding it to dependency arrays

## Best Practices

- **Never read or write `ref.current` during render** — refs are mutable escape hatches outside React's render model. Reading during render creates non-deterministic behavior
- **Exception: lazy initialization pattern** — `if (ref.current === null) { ref.current = createInstance() }` is safe because it only writes once and the result is the same on every render
- Forward refs to custom components using the `ref` prop (React 19+) or `forwardRef` (React 18)
- Use `useRef<T | null>(null)` for DOM refs — the initial value is `null` until the element mounts
- Use `useRef<T>(initialValue)` for mutable data refs — non-null from the start
- Prefer `useRef` over module-level variables when the value is per-component-instance

## Example Use

### DOM manipulation (focus management)

```tsx
function SearchInput({ onSearch }: { onSearch: (term: string) => void }) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Focus on mount — accessibility for primary search fields
    inputRef.current?.focus();
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      inputRef.current?.blur();
    }
  };

  return (
    <input
      ref={inputRef}
      type="search"
      onChange={(e) => onSearch(e.target.value)}
      onKeyDown={handleKeyDown}
      aria-label="Search"
    />
  );
}
```

### Storing latest value for stable callbacks

```tsx
function useLatestCallback<T extends (...args: unknown[]) => unknown>(fn: T): T {
  const ref = useRef(fn);

  // Update ref on every render (not during render output — in a layout effect)
  useLayoutEffect(() => {
    ref.current = fn;
  });

  // Return a stable function that always calls the latest version
  return useCallback(
    ((...args) => ref.current(...args)) as T,
    [],
  );
}

// Usage — stable callback without dependency churn
function NotificationBanner({ notifications }: Props) {
  const handleDismiss = useLatestCallback((id: string) => {
    // Always reads fresh `notifications` without listing it as a dep
    const remaining = notifications.filter((n) => n.id !== id);
    updateNotifications(remaining);
  });

  return <MemoizedList items={notifications} onDismiss={handleDismiss} />;
}
```

### Interval with cleanup

```tsx
function useInterval(callback: () => void, delayMs: number | null) {
  const savedCallback = useRef(callback);

  useLayoutEffect(() => {
    savedCallback.current = callback;
  });

  useEffect(() => {
    if (delayMs === null) return;

    const id = setInterval(() => savedCallback.current(), delayMs);
    return () => clearInterval(id);
  }, [delayMs]);
}
```

## Pitfalls (react.dev Caveats)

- **Don't read/write `ref.current` during render** — React can't track mutations to refs. Reading during render means different results on re-renders (non-deterministic output). Write in effects or event handlers only
- **Strict Mode calls component twice** — if you set `ref.current` during render, it happens twice in development. This is intentional to surface impure render logic
- **Custom components don't accept `ref` by default** (React 18) — must use `forwardRef`. In React 19, `ref` is a regular prop
- **Mutating `ref.current` does NOT cause re-render** — if you need the UI to update when the value changes, use `useState` instead
- **Initial value is used only on first render** — changing the argument to `useRef` on subsequent renders has no effect
- **Null ref on first render** — DOM refs are `null` until after the component mounts. Don't assume `ref.current` is available in the component body

## Error Handling

- `useRef` itself never throws
- DOM refs can be `null` — always null-check before accessing: `ref.current?.focus()`
- When using refs to store async operation state (AbortController, timeouts), ensure cleanup nullifies the ref to prevent stale operations:

```tsx
useEffect(() => {
  const controller = new AbortController();
  controllerRef.current = controller;

  fetchData({ signal: controller.signal });

  return () => {
    controller.abort();
    controllerRef.current = null;
  };
}, []);
```

## Works With

| Hook | Relationship |
|------|-------------|
| `useEffect` | Effects read/write refs for DOM manipulation and storing instances |
| `useLayoutEffect` | Measure DOM via ref before paint, update ref with latest callback |
| `useCallback` | Ref holds latest value, callback reads from ref — avoids dep array bloat |
| `useImperativeHandle` | Exposes custom methods on a forwarded ref |
| `useState` | If you need re-renders on change, use `useState`. If you don't, use `useRef` |

## Anti-Patterns

- ❌ Reading `ref.current` during render to determine output — non-deterministic, breaks concurrent features
- ❌ Using `useRef` to store state that affects the rendered UI — component won't re-render when it changes
- ❌ Overwriting `ref.current` in render for DOM refs — React manages the assignment via the `ref` prop
- ❌ Using a ref as a "did mount" flag to skip effects — Strict Mode double-invoke breaks this pattern
- ❌ Storing derived/computed values in a ref — use `useMemo` for derived data
- ❌ Creating a new ref for each callback just to avoid dependencies — use `useReducer` with stable dispatch instead
- ❌ Forgetting to clean up ref-held resources (timers, subscriptions, instances) in `useEffect` cleanup
