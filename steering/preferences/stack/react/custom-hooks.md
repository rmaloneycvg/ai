# Custom Hooks Steering

## When to Extract a Custom Hook

- Same hook combination appears in 2+ components (DRY signal)
- A component has 3+ hooks working together for one concern (cohesion signal)
- Hook logic is testable independently from the component's UI
- You need to share stateful logic without sharing UI

**Do NOT extract when:**
- Used in only one component and unlikely to be reused
- Would require 4+ parameters (too coupled to component context)
- Types don't generalize beyond the specific component
- It's a single `useState` or trivial one-liner

---

## Structure

```tsx
// hooks/use-<name>.ts — one hook per file
export function use<Name>(params) {
  // hooks (useState, useEffect, useRef, etc.)
  // derived values
  // handlers (wrapped in useCallback if returned)
  return { value, handler, status };
}
```

### Naming

- File: `use-<name>.ts` (kebab-case)
- Export: `use<Name>` (camelCase with `use` prefix)
- Name describes the **behavior**, not the implementation: `useDebounce` not `useEffectWithTimeout`
- Place in `src/hooks/` (shared) or feature-local `hooks/` directory
- Co-locate test: `use-<name>.test.ts`

---

## Rules

### Return Named Functions, Not Dispatch

Expose semantically named functions. Consumers shouldn't know the internal state mechanism.

```tsx
// ✅ Named functions — consumer doesn't know it's useReducer inside
export function useToggle(initial = false) {
  const [value, setValue] = useState(initial);
  const toggle = useCallback(() => setValue(v => !v), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);
  return { value, toggle, setTrue, setFalse } as const;
}

// ❌ Exposing dispatch — breaks encapsulation
export function useToggle(initial = false) {
  const [state, dispatch] = useReducer(reducer, { value: initial });
  return { state, dispatch }; // Consumer must know action types
}
```

### Wrap Returned Functions in useCallback

Custom hook consumers can't control re-render frequency. Stabilize all returned functions.

```tsx
export function useCounter(initial = 0) {
  const [count, setCount] = useState(initial);
  const increment = useCallback(() => setCount(c => c + 1), []);
  const decrement = useCallback(() => setCount(c => c - 1), []);
  const reset = useCallback(() => setCount(initial), [initial]);
  return { count, increment, decrement, reset };
}
```

### Keep Return Type Narrow

Return only what consumers need. Don't expose internal refs, intermediate state, or implementation details.

```tsx
// ✅ Narrow return — consumer gets what they need
export function useAsync<T>() {
  // ... internal useReducer, refs, etc.
  return { data, error, status, run, reset };
}

// ❌ Leaky return — exposes internals
export function useAsync<T>() {
  // ...
  return { data, error, status, run, reset, dispatch, stateRef, abortController };
}
```

### Compose Hooks Inside Hooks

Custom hooks can call other custom hooks. Build complex behavior from simple, tested primitives.

```tsx
export function useSearchWithDebounce(initialQuery = '') {
  const [query, setQuery] = useState(initialQuery);
  const debouncedQuery = useDebounce(query, 300);  // custom hook
  const results = useSearchResults(debouncedQuery); // custom hook
  return { query, setQuery, results };
}
```

---

## Testing

- Test hooks with `renderHook` from `@testing-library/react`
- Test behavior, not implementation (don't assert internal state)
- Test state transitions: initial → action → expected result
- Test cleanup: unmount and verify subscriptions cleared
- Coverage target: 90%+

```tsx
import { renderHook, act } from '@testing-library/react';
import { useToggle } from './use-toggle';

describe('useToggle', () => {
  it('starts with initial value', () => {
    const { result } = renderHook(() => useToggle(false));
    expect(result.current.value).toBe(false);
  });

  it('toggles value', () => {
    const { result } = renderHook(() => useToggle(false));
    act(() => result.current.toggle());
    expect(result.current.value).toBe(true);
  });
});
```

---

## Common Patterns

| Pattern | Hook Name | Internal Hooks |
|---------|-----------|----------------|
| Debounced value | `useDebounce(value, ms)` | useState + useEffect |
| Toggle boolean | `useToggle(initial)` | useState + useCallback |
| Previous value | `usePrevious(value)` | useRef + useEffect |
| Media query | `useMediaQuery(query)` | useSyncExternalStore |
| LocalStorage sync | `useLocalStorage(key, default)` | useState + useEffect |
| Window size | `useWindowSize()` | useSyncExternalStore |
| Intersection observer | `useIntersection(ref, opts)` | useState + useEffect + useRef |
| Async action | `useAsync<T>()` | useReducer + useCallback |
| Interval | `useInterval(callback, ms)` | useRef + useEffect |
| Event listener | `useEventListener(event, handler, el)` | useRef + useEffect |

---

## Anti-Patterns

- ❌ Naming without `use` prefix — breaks Rules of Hooks linting
- ❌ Exposing `dispatch` or `setState` directly — breaks encapsulation
- ❌ Giant hook with 20+ lines of JSX-related logic — that's a component, not a hook
- ❌ Hook that returns a React element — hooks return data/handlers, components return elements
- ❌ Unstable returned functions (missing `useCallback`) — causes consumer re-renders
- ❌ Side effects in the hook body outside `useEffect` — violates React rules
- ❌ Reading `ref.current` during the hook's synchronous body for render output
- ❌ Accepting a callback param without stabilizing it via ref (causes effect churn)
