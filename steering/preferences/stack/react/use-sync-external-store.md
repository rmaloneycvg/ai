---
inclusion: manual
---

# useSyncExternalStore Steering

## When to Use

- Subscribing to non-React state: browser APIs (navigator.onLine, matchMedia, localStorage)
- Integrating third-party state libraries that aren't React-aware
- Reading from a shared mutable source that notifies on change (WebSocket message bus, EventEmitter)
- When you need SSR-safe access to browser state (via `getServerSnapshot`)

**Trigger:** You need React to re-render when an external value changes, and that value lives outside React's state system.

**Don't use when:** The state is already managed by React (useState), Zustand (already uses useSyncExternalStore internally), or TanStack Query.

---

## Best Practices

- `getSnapshot` must return an immutable value — same reference if nothing changed (`Object.is` comparison)
- Never create new objects/arrays inside `getSnapshot` — causes infinite re-renders
- `subscribe` must return an unsubscribe function (cleanup)
- Always provide `getServerSnapshot` for SSR/Next.js Server Components to avoid hydration mismatches
- Extract into a custom hook — components should never call `useSyncExternalStore` directly
- Cache/memoize the snapshot value if deriving from a larger store

---

## Example Use

### Online Status Hook

```tsx
// hooks/use-online-status.ts
import { useSyncExternalStore } from 'react'

function subscribe(callback: () => void) {
  window.addEventListener('online', callback)
  window.addEventListener('offline', callback)
  return () => {
    window.removeEventListener('online', callback)
    window.removeEventListener('offline', callback)
  }
}

function getSnapshot() {
  return navigator.onLine
}

function getServerSnapshot() {
  return true // Assume online during SSR
}

export function useOnlineStatus() {
  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
```

```tsx
// Component usage
'use client'

import { useOnlineStatus } from '@/hooks/use-online-status'

export function ConnectionBanner() {
  const isOnline = useOnlineStatus()

  if (isOnline) return null

  return (
    <div role="alert" aria-live="polite" className="bg-destructive text-destructive-foreground p-2 text-center">
      You are offline. Changes will sync when reconnected.
    </div>
  )
}
```

### Media Query Hook

```tsx
// hooks/use-media-query.ts
import { useCallback, useSyncExternalStore } from 'react'

export function useMediaQuery(query: string): boolean {
  const subscribe = useCallback(
    (callback: () => void) => {
      const mql = window.matchMedia(query)
      mql.addEventListener('change', callback)
      return () => mql.removeEventListener('change', callback)
    },
    [query],
  )

  const getSnapshot = () => window.matchMedia(query).matches

  const getServerSnapshot = () => false // Conservative default for SSR

  return useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)
}
```

```tsx
// Usage
const isMobile = useMediaQuery('(max-width: 768px)')
const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)')
```

---

## Pitfalls

- If `getSnapshot` returns a new object/array every call, React re-renders infinitely — always return a cached/stable reference
- `subscribe` must be a stable function (define outside component or wrap in `useCallback`) — otherwise React re-subscribes every render
- Forgetting `getServerSnapshot` causes hydration mismatch errors in Next.js
- Browser APIs accessed in `getSnapshot` throw during SSR if no server snapshot is provided

---

## Error Handling

- Wrap browser API access in try/catch inside `getSnapshot` if the API might be unavailable
- Return a safe default from `getServerSnapshot` — never throw
- If the external store can be in an error state, include that in the snapshot shape:

```tsx
interface StoreSnapshot {
  data: Data | null
  error: Error | null
}
```

---

## Works With

| Hook | Relationship |
|------|-------------|
| `useCallback` | Stabilize `subscribe` when it depends on props |
| `useMemo` | Memoize derived values from snapshot to avoid downstream re-renders |
| `useRef` | Hold mutable references to the external store instance |
| `useEffect` | Setup/teardown of the external store itself (if created dynamically) |

---

## Anti-Patterns

- ❌ Creating a new object in `getSnapshot` — causes infinite render loop
- ❌ Using for React-managed state (useState/Zustand already handles reactivity)
- ❌ Omitting `getServerSnapshot` in SSR apps — hydration errors
- ❌ Subscribing to high-frequency events without throttling (e.g., `scroll`, `mousemove`)
- ❌ Putting the full store in the snapshot when you only need a slice — selector pattern instead
- ❌ Calling `useSyncExternalStore` directly in components — always wrap in a custom hook
