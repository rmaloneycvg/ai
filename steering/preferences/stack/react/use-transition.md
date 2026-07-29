# useTransition Steering

## When to Use

- Marking state updates as non-urgent so the UI stays responsive during expensive re-renders
- Tab switching, filtering large lists, navigating between views — anything where blocking the UI feels janky
- Wrapping async mutations (Server Actions) to get `isPending` without manual loading state
- Keeping previous UI visible while new content renders (pairs with Suspense)

**Do NOT use when:**
- The update is urgent (typing into an input, toggling a checkbox) — transitions defer these, causing input lag
- You need synchronous state for controlled inputs — use `useState` directly
- The update is trivial (single boolean toggle with no expensive render downstream)

---

## Best Practices

- Use `isPending` to show subtle loading indicators (spinners, opacity reduction) — not full-page skeletons
- Wrap navigation and filter changes in transitions so previous content stays visible until new content is ready
- Combine with Suspense boundaries — transitions keep the existing UI while suspended children load
- Keep the callback synchronous (or pass an async function in React 19+) — don't nest `await` chains inside the callback in React 18

---

## Example Use

### Non-Blocking Tab Switch

```tsx
'use client'

import { useState, useTransition } from 'react'
import { TabContent } from './tab-content'

const TABS = ['overview', 'analytics', 'settings'] as const
type Tab = (typeof TABS)[number]

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [isPending, startTransition] = useTransition()

  function handleTabChange(tab: Tab) {
    startTransition(() => {
      setActiveTab(tab)
    })
  }

  return (
    <div>
      <nav role="tablist">
        {TABS.map((tab) => (
          <button
            key={tab}
            role="tab"
            aria-selected={activeTab === tab}
            onClick={() => handleTabChange(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>
      <div className={isPending ? 'opacity-60 transition-opacity' : ''}>
        <TabContent tab={activeTab} />
      </div>
    </div>
  )
}
```

### Server Action with isPending

```tsx
'use client'

import { useTransition } from 'react'
import { deleteProject } from '@/lib/actions/projects'
import { Button } from '@/components/ui/button'

export function DeleteButton({ projectId }: { projectId: string }) {
  const [isPending, startTransition] = useTransition()

  function handleDelete() {
    startTransition(async () => {
      await deleteProject(projectId)
    })
  }

  return (
    <Button
      variant="destructive"
      onClick={handleDelete}
      disabled={isPending}
    >
      {isPending ? 'Deleting...' : 'Delete'}
    </Button>
  )
}
```

---

## Pitfalls

- Transitions are interruptible — if a newer transition starts, the previous one is abandoned. Don't rely on every transition completing.
- `isPending` stays `true` until all state updates inside `startTransition` finish rendering (including Suspense boundaries that get triggered)
- Wrapping controlled input `onChange` in a transition causes perceived input lag — the value update is deferred
- In React 18, `startTransition` callback must be synchronous. In React 19+, async callbacks are supported.

---

## Error Handling

- Errors thrown inside `startTransition` propagate to the nearest error boundary
- For async transitions (React 19+), unhandled rejections also propagate to error boundaries
- Use try/catch inside the async callback if you need to handle errors locally (e.g., showing a toast)

```tsx
function handleSubmit() {
  startTransition(async () => {
    try {
      await submitForm(data)
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Submission failed')
    }
  })
}
```

---

## Works With

| Hook/Feature | Relationship |
|-------------|-------------|
| `Suspense` | Transitions keep existing UI visible while suspended children load |
| `useOptimistic` | Wrap optimistic updates in `startTransition` for automatic revert on completion |
| `useDeferredValue` | Alternative for deferring derived values without wrapping in a callback |
| Server Actions | Async transitions provide `isPending` for server mutation feedback |
| `useActionState` | Handles form submission state; `useTransition` is lighter for non-form async |

---

## Anti-Patterns

- ❌ Wrapping urgent input changes (`onChange` for text fields) in `startTransition`
- ❌ Using `isPending` as primary loading state for data fetching (use TanStack Query or Suspense)
- ❌ Nesting transitions inside transitions (outer transition already defers)
- ❌ Using transitions for trivial state changes that render instantly
- ❌ Assuming every transition completes — newer transitions interrupt older ones
- ❌ Replacing `useState` loading booleans everywhere with transitions (only use when you need non-blocking renders)
