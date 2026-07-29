# useLayoutEffect Steering

## When to Use

- Measuring DOM elements before the browser paints (element dimensions, positions)
- Positioning tooltips, popovers, or dropdowns relative to a trigger element
- Preventing visual flicker when a `useEffect` would cause a visible "jump" (element appears, then moves)
- Synchronously updating DOM or state based on layout measurements

**Trigger:** You see a visible flicker or layout jump with `useEffect` — switch to `useLayoutEffect`. If there's no visual glitch, stay with `useEffect`.

**Default to `useEffect`.** Only reach for `useLayoutEffect` when you can demonstrate the flicker problem.

---

## Best Practices

- Keep the callback fast — it blocks the browser from painting
- Only read layout (getBoundingClientRect, offsetHeight) and set state — don't do network requests or heavy computation
- Pair with `useRef` to access the DOM node being measured
- In Next.js / SSR: `useLayoutEffect` fires a warning on the server. Suppress by using it only in `'use client'` components, or conditionally fall back to `useEffect` via a wrapper hook
- Prefer CSS solutions (anchor positioning, `position: fixed` with transforms) over JS measurement when possible

---

## Example Use

### Tooltip Positioning

```tsx
// hooks/use-element-rect.ts
'use client'

import { useLayoutEffect, useRef, useState } from 'react'

interface Rect {
  top: number
  left: number
  width: number
  height: number
}

export function useElementRect<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [rect, setRect] = useState<Rect>({ top: 0, left: 0, width: 0, height: 0 })

  useLayoutEffect(() => {
    if (!ref.current) return
    const { top, left, width, height } = ref.current.getBoundingClientRect()
    setRect({ top, left, width, height })
  })

  return { ref, rect }
}
```

```tsx
// components/tooltip.tsx
'use client'

import { useLayoutEffect, useRef, useState } from 'react'

interface TooltipProps {
  triggerRef: React.RefObject<HTMLElement | null>
  children: React.ReactNode
  visible: boolean
}

export function Tooltip({ triggerRef, children, visible }: TooltipProps) {
  const tooltipRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  useLayoutEffect(() => {
    if (!visible || !triggerRef.current || !tooltipRef.current) return

    const triggerRect = triggerRef.current.getBoundingClientRect()
    const tooltipRect = tooltipRef.current.getBoundingClientRect()

    setPosition({
      top: triggerRect.top - tooltipRect.height - 8,
      left: triggerRect.left + (triggerRect.width - tooltipRect.width) / 2,
    })
  }, [visible])

  if (!visible) return null

  return (
    <div
      ref={tooltipRef}
      role="tooltip"
      className="fixed z-50 rounded bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md"
      style={{ top: position.top, left: position.left }}
    >
      {children}
    </div>
  )
}
```

### Preventing Flash of Incorrect Size

```tsx
'use client'

import { useLayoutEffect, useRef, useState } from 'react'

export function AutoResizeTextarea({ value, onChange }: {
  value: string
  onChange: (v: string) => void
}) {
  const ref = useRef<HTMLTextAreaElement>(null)

  useLayoutEffect(() => {
    if (!ref.current) return
    ref.current.style.height = '0px'
    ref.current.style.height = `${ref.current.scrollHeight}px`
  }, [value])

  return (
    <textarea
      ref={ref}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full resize-none overflow-hidden"
    />
  )
}
```

---

## Pitfalls

- **Blocks painting** — a slow `useLayoutEffect` freezes the UI. Keep under 5ms.
- **SSR warning** — Next.js logs a warning when `useLayoutEffect` runs on the server. Only use in `'use client'` components.
- **Infinite loops** — setting state that changes the measurement causes another layout effect → measure → set state. Guard with comparison:

```tsx
useLayoutEffect(() => {
  const newHeight = ref.current?.scrollHeight ?? 0
  if (newHeight !== height) setHeight(newHeight)
}, [deps])
```

- **Missing deps** — same rules as `useEffect`. Lint with exhaustive-deps.

---

## Error Handling

- Null-check refs before reading layout: `if (!ref.current) return`
- `getBoundingClientRect()` returns zeros for hidden/detached elements — handle gracefully
- If measurement fails, fall back to a default position rather than rendering nothing

---

## Works With

| Hook | Relationship |
|------|-------------|
| `useRef` | Access the DOM node to measure |
| `useState` | Store computed position/dimensions |
| `useCallback` | Stable resize handlers passed to ResizeObserver |
| `useEffect` | Use for non-visual side effects that don't need paint-blocking |

---

## Anti-Patterns

- ❌ Using `useLayoutEffect` for data fetching, subscriptions, or anything not layout-related
- ❌ Using it "just to be safe" when `useEffect` works fine — adds unnecessary paint blocking
- ❌ Heavy computation inside the callback (parsing, filtering large arrays)
- ❌ Using in Server Components or without `'use client'` directive
- ❌ Setting state unconditionally causing infinite re-render loops
- ❌ Measuring elements that aren't yet rendered (conditional rendering without guards)
