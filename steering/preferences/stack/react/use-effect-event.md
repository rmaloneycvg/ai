# useEffectEvent Steering

> **Status: Experimental (React Canary).** This API is not stable. Do not use in production code until it ships in a stable React release. Include this hook in new projects only if already on React Canary.

## When to Use

- An Effect needs to read the latest value of a prop or state variable but should NOT re-run when that value changes
- Breaking the "stale closure" problem without adding every value to the dependency array
- Wrapping event-handler-style logic (logging, analytics, notifications) that an Effect triggers but shouldn't be reactive to

**Trigger:** You have a `useEffect` where adding a value to deps causes undesirable re-execution, but removing it causes stale reads. `useEffectEvent` solves this tension.

---

## Best Practices

- Only call the returned function from inside an Effect — never from event handlers, render, or other hooks
- Do not add the Effect Event to the dependency array of the parent Effect
- Keep Effect Events focused — one logical "event" per function
- Name with `on` prefix to signal event semantics: `onTick`, `onVisit`, `onConnectionChange`
- Treat as the conceptual boundary between "reactive" (re-run on change) and "non-reactive" (read latest, don't trigger)

---

## Example Use

### Logging Page Visits Without Re-Running on Theme Change

```tsx
'use client'

import { useEffect, useEffectEvent } from 'react'

interface PageTrackerProps {
  url: string
  theme: string // Changes frequently, but shouldn't re-trigger the visit log
}

export function PageTracker({ url, theme }: PageTrackerProps) {
  const onVisit = useEffectEvent((visitedUrl: string) => {
    // Reads `theme` from props at call time — always latest
    logAnalytics({ url: visitedUrl, theme })
  })

  useEffect(() => {
    onVisit(url)
    // Only re-runs when `url` changes — NOT when `theme` changes
  }, [url])

  return null
}
```

### Chat Connection with Notification Preferences

```tsx
'use client'

import { useEffect, useEffectEvent, useState } from 'react'

export function useChatConnection(roomId: string, notificationsEnabled: boolean) {
  const [messages, setMessages] = useState<Message[]>([])

  const onMessage = useEffectEvent((message: Message) => {
    // Reads `notificationsEnabled` at call time — always current
    setMessages((prev) => [...prev, message])
    if (notificationsEnabled) {
      showNotification(message.preview)
    }
  })

  useEffect(() => {
    const connection = createConnection(roomId)
    connection.on('message', onMessage)
    connection.connect()

    return () => connection.disconnect()
    // Re-connects only when roomId changes
    // Does NOT re-connect when notificationsEnabled toggles
  }, [roomId])

  return messages
}
```

---

## Pitfalls

- **Experimental API** — may change signature or be renamed before stable release
- **Cannot be called outside Effects** — calling from an event handler or render body is invalid
- **Not a dependency** — never include in the `useEffect` deps array (lint rule will enforce this once stable)
- **Not a replacement for `useCallback`** — `useCallback` is for stable function identity passed as props; `useEffectEvent` is for non-reactive reads inside Effects
- **SSR** — behaves the same as `useEffect` (does not run on server)

---

## Error Handling

- If the Effect Event throws, the error propagates to the calling Effect — handle with try/catch inside the Effect Event or at the Effect level
- Don't rely on the Effect Event being called at a specific time relative to render — it's called when the Effect runs

```tsx
const onVisit = useEffectEvent((url: string) => {
  try {
    logAnalytics({ url, theme })
  } catch (err) {
    console.error('Analytics failed:', err)
    // Don't let analytics break the app
  }
})
```

---

## Works With

| Hook | Relationship |
|------|-------------|
| `useEffect` | The only valid caller of an Effect Event function |
| `useState` | Read latest state inside the Effect Event without adding to Effect deps |
| `useRef` | Alternative approach (stale closure via ref) that `useEffectEvent` replaces more cleanly |
| `useCallback` | Different purpose — `useCallback` stabilizes identity for props; `useEffectEvent` reads latest values non-reactively |

---

## Anti-Patterns

- ❌ Calling the Effect Event from an onClick handler or during render
- ❌ Adding the Effect Event to the dependency array of `useEffect`
- ❌ Using in production apps on stable React (API will break on upgrade)
- ❌ Replacing all `useCallback` with `useEffectEvent` — they solve different problems
- ❌ Wrapping reactive logic that SHOULD trigger re-execution of the Effect
- ❌ Using `useEffectEvent` when a simple ref (`useRef` + assignment in render) would suffice in stable React

---

## Migration Note (Pre-Stable Workaround)

Until `useEffectEvent` ships in stable React, use the ref pattern:

```tsx
const notificationsRef = useRef(notificationsEnabled)
notificationsRef.current = notificationsEnabled

useEffect(() => {
  const connection = createConnection(roomId)
  connection.on('message', (msg) => {
    if (notificationsRef.current) showNotification(msg.preview)
  })
  connection.connect()
  return () => connection.disconnect()
}, [roomId])
```

This achieves the same "read latest without re-running" behavior but is less ergonomic. Replace with `useEffectEvent` once stable.
