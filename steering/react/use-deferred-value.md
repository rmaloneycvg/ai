---
name: ReactUseDeferredValue
description: Steering for useDeferredValue — deferring expensive re-renders for search results, filtered lists, and large tables
inclusion: manual
fileMatchPattern: [
  "**/src/**/*.tsx",
  "**/src/**/*.jsx",
  "**/src/**/*.ts",
  "**/src/**/*.js"
]
---

# useDeferredValue Steering

## When to Use

- Deferring an expensive re-render of a child tree (search results, filtered lists, large tables) while keeping inputs responsive
- Showing stale content while fresh content loads — a React-integrated alternative to manual debouncing
- The deferred value "lags behind" the current value, allowing React to prioritize urgent updates (typing) over non-urgent ones (re-rendering results)

**Do NOT use when:**
- The re-render triggered by the value is cheap — deferring adds complexity for no benefit
- You need a fixed delay (use `setTimeout`/debounce for API calls with rate limits)
- The data comes from a server and you want loading states (use Suspense + transitions instead)

---

## Best Practices

- Wrap the expensive child component in `React.memo()` — without memo, the child re-renders on every parent render regardless of deferral
- Pass the deferred value (not the current value) to the expensive child — React skips re-rendering it until the deferred value catches up
- Use with Suspense: when the deferred value triggers a Suspense boundary, React shows stale content instead of the fallback
- Show visual feedback (opacity, indicator) when `deferredValue !== currentValue` so users know results are updating

---

## Example Use

### Deferred Search Results

```tsx
'use client'

import { useState, useDeferredValue } from 'react'
import { SearchResults } from './search-results'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query)
  const isStale = query !== deferredQuery

  return (
    <div>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
        aria-label="Search"
      />
      <div className={isStale ? 'opacity-60 transition-opacity' : ''}>
        <SearchResults query={deferredQuery} />
      </div>
    </div>
  )
}
```

```tsx
// search-results.tsx — must be memoized for deferral to work
import { memo } from 'react'

interface SearchResultsProps {
  query: string
}

export const SearchResults = memo(function SearchResults({ query }: SearchResultsProps) {
  // Expensive filtering/rendering
  const results = useSearchData(query) // TanStack Query or filtered local data

  return (
    <ul>
      {results.map((item) => (
        <li key={item.id}>{item.name}</li>
      ))}
    </ul>
  )
})
```

### Deferred Value with Suspense

```tsx
'use client'

import { Suspense, useState, useDeferredValue } from 'react'
import { UserList } from './user-list'
import { Skeleton } from '@/components/ui/skeleton'

export function UserFilter() {
  const [filter, setFilter] = useState('')
  const deferredFilter = useDeferredValue(filter)
  const isStale = filter !== deferredFilter

  return (
    <div>
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter users..."
        aria-label="Filter users"
      />
      <Suspense fallback={<Skeleton className="h-64" />}>
        <div className={isStale ? 'opacity-60' : ''}>
          <UserList filter={deferredFilter} />
        </div>
      </Suspense>
    </div>
  )
}
```

---

## Pitfalls

- Without `memo` on the child, deferral has no effect — the child re-renders every time the parent renders regardless
- The deferred value updates asynchronously — there's no guarantee on timing (it's not a fixed debounce interval)
- During the initial render, `useDeferredValue` returns the same value you pass in (no lag on mount)
- Deferred updates are interruptible — if a new value arrives before the deferred render completes, React restarts with the newer value

---

## Error Handling

- Errors in the deferred child propagate to the nearest error boundary like any other render error
- If the deferred child suspends and the Suspense boundary has already shown content, React shows the stale content (no fallback flash)
- No special error handling needed — standard error boundary patterns apply

---

## Works With

| Hook/Feature | Relationship |
|-------------|-------------|
| `React.memo` | **Required** — wrap the expensive child or deferral has no rendering benefit |
| `Suspense` | Deferred values keep stale UI visible instead of showing Suspense fallback |
| `useTransition` | Alternative approach — transitions wrap the state update, deferred values wrap the consumer |
| AG Grid | Defer filter values passed to grid `rowData` filtering for responsive input |
| TanStack Query | Defer the query key value so rapid typing doesn't trigger excessive re-fetches |

---

## Anti-Patterns

- ❌ Using `useDeferredValue` without memoizing the consumer component
- ❌ Replacing proper debouncing for API calls (deferred value doesn't control fetch timing)
- ❌ Deferring values that trigger cheap renders (adds complexity without benefit)
- ❌ Using deferred values for urgent UI updates (checkboxes, toggles)
- ❌ Expecting a consistent delay — React decides when to update based on device performance
- ❌ Passing deferred value to the same component that owns the state (defer at the child boundary)
