---
name: ReactUseDebugValue
description: Steering for useDebugValue — adding human-readable labels to custom hooks for React DevTools inspection
inclusion: manual
fileMatchPattern: [
  "**/src/**/*.tsx",
  "**/src/**/*.jsx",
  "**/src/**/*.ts",
  "**/src/**/*.js",
  "**/hooks/**/*.ts",
  "**/hooks/**/*.tsx"
]
---

# useDebugValue Steering

## When to Use

- Adding a human-readable label to a custom hook visible in React DevTools
- Debugging complex custom hooks where the internal state isn't obvious from the hook name alone
- Shared/library hooks consumed by multiple developers who benefit from at-a-glance state inspection

**Do NOT use when:**
- Inside a component (only works in custom hooks)
- The hook's return value already makes the state obvious (e.g., a simple counter hook)
- The formatting is expensive and you haven't provided a formatter function (avoid unnecessary work)

---

## Best Practices

- Only add `useDebugValue` to hooks shared across the team or published as a library — don't clutter every trivial hook
- Use the optional formatter function (second argument) to defer expensive formatting until DevTools actually inspects the hook
- Keep labels concise — DevTools has limited space
- Format as a status string or key metric, not a full data dump

---

## Example Use

### Auth Status Hook

```tsx
import { useDebugValue } from 'react'
import { useQuery } from '@tanstack/react-query'

interface Session {
  userId: string
  role: string
  expiresAt: number
}

export function useSession() {
  const query = useQuery<Session | null>({
    queryKey: ['session'],
    queryFn: fetchSession,
    staleTime: 5 * 60 * 1000,
  })

  useDebugValue(query.data, (session) =>
    session ? `${session.role} (${session.userId})` : 'Not authenticated'
  )

  return query
}
```

In React DevTools, this hook displays:
```
Session: "admin (user_abc123)"
```

### Online Status Hook with Formatter

```tsx
import { useDebugValue, useSyncExternalStore } from 'react'

export function useOnlineStatus() {
  const isOnline = useSyncExternalStore(
    subscribe,
    () => navigator.onLine,
    () => true // SSR fallback
  )

  useDebugValue(isOnline ? 'Online' : 'Offline')

  return isOnline
}

function subscribe(callback: () => void) {
  window.addEventListener('online', callback)
  window.addEventListener('offline', callback)
  return () => {
    window.removeEventListener('online', callback)
    window.removeEventListener('offline', callback)
  }
}
```

---

## Pitfalls

- `useDebugValue` has **zero runtime effect** — it does not log, throw, or change behavior. It only appears in DevTools.
- Calling it inside a component (not a custom hook) silently does nothing
- Without the formatter function, the value is computed on every render even when DevTools isn't open — use the formatter for expensive derivations
- DevTools must be open and inspecting the component for the label to appear

---

## Error Handling

- No error handling needed — `useDebugValue` cannot throw or fail
- If the formatter function throws, it may crash DevTools inspection (keep formatters simple and defensive)

```tsx
// Defensive formatter
useDebugValue(state, (s) => {
  try {
    return `${s.items.length} items, ${s.status}`
  } catch {
    return 'Unknown state'
  }
})
```

---

## Works With

| Hook/Feature | Relationship |
|-------------|-------------|
| Custom hooks | **Only context** — `useDebugValue` is meaningless outside custom hooks |
| React DevTools | The sole consumer of the debug label |
| `useReducer` | Add debug value to show current reducer state summary |
| TanStack Query hooks | Wrap in a custom hook with debug label showing query status |
| Zustand stores | Custom hook wrappers can surface store state in DevTools |

---

## Anti-Patterns

- ❌ Using inside a component instead of a custom hook
- ❌ Adding to every hook regardless of complexity (noise in DevTools)
- ❌ Expensive computation without the formatter function (runs every render)
- ❌ Using as a logging mechanism (it's not — use `console.log` or a logger)
- ❌ Displaying sensitive data (tokens, passwords) in debug labels
- ❌ Relying on `useDebugValue` for production monitoring (DevTools only)
