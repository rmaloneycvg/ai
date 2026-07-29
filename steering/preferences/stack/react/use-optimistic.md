# useOptimistic Steering

## When to Use

- Showing immediate UI feedback while an async action (form submission, server mutation) is in-flight
- Any mutation where the expected success state is predictable (adding to a list, toggling a boolean, updating text)
- Inside form actions or `startTransition` callbacks — the optimistic state reverts automatically when the async function completes

**Do NOT use when:**
- The result of the mutation is unpredictable (server generates IDs, computed fields you can't guess)
- You need the optimistic state to persist beyond the async action (use `useState` instead)
- You're outside a transition or form action context (optimistic state won't revert properly)

---

## Best Practices

- Keep `updateFn` pure — it receives current state + the optimistic value you pass to `addOptimistic`, and returns new state
- Pair with Server Actions in Next.js for seamless form submissions
- Always design the optimistic state to match the eventual server response shape
- Use discriminated unions to distinguish optimistic items from confirmed ones (e.g., `{ sending: true }`)

---

## Example Use

### Optimistic Message List (Server Action)

```tsx
'use client'

import { useOptimistic } from 'react'
import { sendMessage } from '@/lib/actions/messages'

interface Message {
  id: string
  text: string
  sending?: boolean
}

export function MessageThread({ messages }: { messages: Message[] }) {
  const [optimisticMessages, addOptimisticMessage] = useOptimistic(
    messages,
    (state: Message[], newMessage: string) => [
      ...state,
      { id: `temp-${Date.now()}`, text: newMessage, sending: true },
    ]
  )

  async function formAction(formData: FormData) {
    const text = formData.get('message') as string
    addOptimisticMessage(text)
    await sendMessage(text)
  }

  return (
    <div>
      <ul>
        {optimisticMessages.map((msg) => (
          <li key={msg.id} className={msg.sending ? 'opacity-60' : ''}>
            {msg.text}
          </li>
        ))}
      </ul>
      <form action={formAction}>
        <input name="message" required />
        <button type="submit">Send</button>
      </form>
    </div>
  )
}
```

### Optimistic Toggle (with useTransition)

```tsx
'use client'

import { useOptimistic, useTransition } from 'react'
import { toggleFavorite } from '@/lib/actions/favorites'

export function FavoriteButton({ isFavorited, itemId }: { isFavorited: boolean; itemId: string }) {
  const [optimisticFavorited, setOptimisticFavorited] = useOptimistic(
    isFavorited,
    (_current: boolean, next: boolean) => next
  )
  const [isPending, startTransition] = useTransition()

  function handleClick() {
    startTransition(async () => {
      setOptimisticFavorited(!optimisticFavorited)
      await toggleFavorite(itemId)
    })
  }

  return (
    <button onClick={handleClick} disabled={isPending}>
      {optimisticFavorited ? '★' : '☆'}
    </button>
  )
}
```

---

## Pitfalls

- Optimistic state only reverts when the async action's promise resolves or rejects — if you call `addOptimistic` outside a transition/action, the state won't revert
- If the server response differs from your optimistic prediction, React replaces with the real state (no merge — ensure your parent re-renders with fresh server data)
- Multiple rapid optimistic updates stack correctly only if your `updateFn` is pure and composes against current state

---

## Error Handling

- On rejection, the optimistic state reverts to the last confirmed state automatically
- Show error UI via the form action's error return or a try/catch in the transition callback
- Pair with toast notifications to inform the user when a revert happens

```tsx
async function formAction(formData: FormData) {
  const text = formData.get('message') as string
  addOptimisticMessage(text)
  const result = await sendMessage(text)
  if (result?.error) {
    toast.error('Failed to send message')
    // Optimistic state reverts automatically since the action completed
  }
}
```

---

## Works With

| Hook/Feature | Relationship |
|-------------|-------------|
| `useTransition` | Wrap async mutations in `startTransition` to trigger optimistic + pending state |
| Server Actions | Primary pairing in Next.js — form `action` prop triggers optimistic flow |
| `useActionState` | Combine for form state + optimistic updates |
| TanStack Query | Use TQ for client-side cache invalidation after the server action completes |

---

## Anti-Patterns

- ❌ Using `useOptimistic` outside a transition or form action (state won't revert)
- ❌ Mutating state inside `updateFn` instead of returning a new object
- ❌ Using optimistic state for unpredictable server-generated values (UUIDs, timestamps)
- ❌ Replacing `useState` with `useOptimistic` for local-only state (no async = no benefit)
- ❌ Forgetting to visually distinguish optimistic items (users need to know what's pending)
