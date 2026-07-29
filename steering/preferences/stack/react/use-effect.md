# useEffect Steering

## When to Use

- Synchronizing with an **external system** — WebSocket connections, DOM event listeners, third-party widget lifecycles, browser APIs (IntersectionObserver, ResizeObserver)
- Subscribing to a store not designed for React (non-React event emitters) — though prefer `useSyncExternalStore` when possible
- Running cleanup logic when a component unmounts (disconnect, unsubscribe, cancel timers)
- Sending analytics events after render (fire-and-forget, not affecting UI)

**Never use for:** Data fetching (use TanStack Query), computing derived state (use `useMemo`), responding to user events (use event handlers), transforming data for rendering (do it during render).

## Best Practices

- Every effect should return a cleanup function (even if it's a no-op) — makes intent explicit
- One effect per concern — don't combine unrelated subscriptions in a single `useEffect`
- Move functions used only by the effect inside the effect — avoids `useCallback` and keeps deps obvious
- If the effect doesn't need to re-run, use `[]` — but verify it genuinely has no external dependencies
- If you see visual flicker (element appears then repositions), switch to `useLayoutEffect`
- Prefer declarative alternatives: `useSyncExternalStore` for store subscriptions, TanStack Query for server state, event handlers for user interactions

## Example Use

### WebSocket subscription

```tsx
function useChatMessages(roomId: string) {
  const [messages, setMessages] = useState<Message[]>([]);

  useEffect(() => {
    const ws = new WebSocket(`wss://chat.example.com/rooms/${roomId}`);

    ws.addEventListener('message', (event) => {
      const msg: Message = JSON.parse(event.data);
      setMessages((prev) => [...prev, msg]);
    });

    ws.addEventListener('error', (event) => {
      console.error('WebSocket error:', event);
    });

    return () => {
      ws.close();
    };
  }, [roomId]);

  return messages;
}
```

### Third-party library lifecycle

```tsx
function MapView({ center, zoom }: { center: LatLng; zoom: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      center: [center.lng, center.lat],
      zoom,
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []); // Initialize once — updates handled separately

  useEffect(() => {
    mapRef.current?.setCenter([center.lng, center.lat]);
    mapRef.current?.setZoom(zoom);
  }, [center.lng, center.lat, zoom]);

  return <div ref={containerRef} className="h-full w-full" />;
}
```

## Pitfalls (react.dev Caveats)

- **Strict Mode runs setup+cleanup twice** — in development, React mounts → unmounts → mounts to verify cleanup works. If your effect breaks on second mount, the cleanup is incomplete
- **Missing deps = stale closures** — the effect reads state/props from the render it was created in. Omitting deps means it never re-runs with fresh values
- **Too many deps = infinite loops** — an object created during render changes identity every time → effect re-runs → state updates → re-render → new object → loop. Stabilize with `useMemo` or extract primitives
- **Async functions** — `useEffect` cannot return a Promise. Define an async function inside the effect and call it, but handle the case where cleanup runs before the async work completes
- **Race conditions without cleanup** — when deps change rapidly, multiple async operations can complete out of order. Use a `let ignore = false` flag or `AbortController` in cleanup
- **Effects fire after paint** — if you need to measure/mutate DOM before browser paints, use `useLayoutEffect`

## Error Handling

- Errors thrown in `useEffect` propagate to the nearest error boundary
- For async work inside effects, always wrap in try/catch — unhandled rejections won't hit error boundaries
- Use `AbortController` for cancelable fetch/async operations:

```tsx
useEffect(() => {
  const controller = new AbortController();

  async function sync() {
    try {
      const res = await fetch(url, { signal: controller.signal });
      // handle response
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      // handle real error
    }
  }

  sync();
  return () => controller.abort();
}, [url]);
```

## Works With

| Hook | Relationship |
|------|-------------|
| `useRef` | Store mutable values (DOM nodes, instances) that effects read/write without triggering re-runs |
| `useCallback` | Stable function as effect dependency — but prefer moving function inside the effect |
| `useMemo` | Stabilize object/array deps to prevent unnecessary effect re-runs |
| `useState` | Effect sets state on subscription events — but never read state as an implicit dep |
| `useLayoutEffect` | Same API, fires synchronously before paint — use when effect measures/mutates DOM layout |
| `useSyncExternalStore` | Preferred over `useEffect` for subscribing to external stores |

## Anti-Patterns

- ❌ Data fetching in `useEffect` — use TanStack Query (handles caching, deduplication, race conditions, loading/error states)
- ❌ Transforming props/state into other state on every render (`useEffect` + `setState`) — compute during render or use `useMemo`
- ❌ Resetting all state when a prop changes — use a `key` prop on the component instead
- ❌ Event handling disguised as an effect — if something happens in response to a click, put it in the click handler
- ❌ Missing cleanup — leaked subscriptions, timers, or connections cause memory leaks and stale updates
- ❌ `useEffect(() => { ... }, undefined)` — forgetting the deps array entirely means the effect runs after every render
- ❌ Setting state in an effect that triggers the same effect (infinite loop)
- ❌ `// eslint-disable-next-line react-hooks/exhaustive-deps` — fix the deps, don't suppress the lint rule
