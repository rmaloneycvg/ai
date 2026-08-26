---
name: ReactUseImperativeHandle
description: Steering for useImperativeHandle — exposing limited imperative APIs from child components via ref
inclusion: manual
fileMatchPattern: [
  "**/src/**/*.tsx",
  "**/src/**/*.jsx",
  "**/src/**/*.ts",
  "**/src/**/*.js"
]
---

# useImperativeHandle Steering

## When to Use

- Exposing a limited API from a child component to a parent via ref
- Wrapping a DOM element but only exposing specific methods (focus, scroll, reset)
- Building reusable compound components (dialogs, drawers, video players) where the parent needs imperative control
- When the parent should NOT have direct access to the underlying DOM node

**Trigger:** A parent needs to call methods on a child, but exposing the full DOM node would break encapsulation or allow unintended mutations.

---

## Best Practices

- Expose the minimum surface area — only methods the parent actually needs
- Use the `ref` prop directly (React 19+); `forwardRef` is no longer required but still works
- Type the handle explicitly with an interface — never `any`
- Name the exposed interface `ComponentNameHandle` (e.g., `DialogHandle`)
- Keep imperative methods focused: `open()`, `close()`, `focus()`, `scrollToTop()`
- Prefer declarative props over imperative handles when possible

---

## Example Use

### Exposing a Dialog Handle

```tsx
// components/dialog.tsx
'use client'

import { useImperativeHandle, useRef, useState, type Ref } from 'react'

export interface DialogHandle {
  open: () => void
  close: () => void
}

interface DialogProps {
  ref?: Ref<DialogHandle>
  title: string
  children: React.ReactNode
}

export function Dialog({ ref, title, children }: DialogProps) {
  const [isOpen, setIsOpen] = useState(false)
  const innerRef = useRef<HTMLDialogElement>(null)

  useImperativeHandle(ref, () => ({
    open: () => {
      setIsOpen(true)
      innerRef.current?.showModal()
    },
    close: () => {
      setIsOpen(false)
      innerRef.current?.close()
    },
  }))

  return (
    <dialog ref={innerRef} aria-labelledby="dialog-title">
      <h2 id="dialog-title">{title}</h2>
      {children}
    </dialog>
  )
}
```

```tsx
// Parent usage
'use client'

import { useRef } from 'react'
import { Dialog, type DialogHandle } from '@/components/dialog'

export function SettingsPage() {
  const dialogRef = useRef<DialogHandle>(null)

  return (
    <>
      <Button onClick={() => dialogRef.current?.open()}>Edit Settings</Button>
      <Dialog ref={dialogRef} title="Settings">
        <SettingsForm onSave={() => dialogRef.current?.close()} />
      </Dialog>
    </>
  )
}
```

### Input with Reset

```tsx
export interface InputHandle {
  focus: () => void
  reset: () => void
}

export function SearchInput({ ref, onSearch }: { ref?: Ref<InputHandle>; onSearch: (q: string) => void }) {
  const inputRef = useRef<HTMLInputElement>(null)

  useImperativeHandle(ref, () => ({
    focus: () => inputRef.current?.focus(),
    reset: () => {
      if (inputRef.current) inputRef.current.value = ''
      onSearch('')
    },
  }))

  return <input ref={inputRef} onChange={(e) => onSearch(e.target.value)} />
}
```

---

## Pitfalls

- The handle object is recreated on every render unless you pass a dependency array as the third argument
- If you omit deps, the handle recreates every render (fine for most cases, wasteful for expensive objects)
- The ref is `null` during initial render — parents must null-check: `ref.current?.method()`
- Does not work in Server Components — only `'use client'` components

---

## Error Handling

- Always null-check before calling: `dialogRef.current?.open()`
- If the exposed method can fail, return a result or throw — don't silently swallow errors
- Type the handle strictly so TypeScript catches invalid method calls at compile time

---

## Works With

| Hook | Relationship |
|------|-------------|
| `useRef` | Parent holds the ref (`useRef<HandleType>(null)`) |
| `useState` | Internal state controlled by imperative methods |
| `useCallback` | Stable method references if deps are needed |

---

## Anti-Patterns

- ❌ Exposing the entire DOM node — defeats the purpose; use a plain `ref` instead
- ❌ Using imperative handle when a prop/callback would work (prefer `onClose` over `ref.close()`)
- ❌ Calling imperative methods during render (side effect in render body)
- ❌ Deeply nested imperative chains (parent calls child which calls grandchild via refs)
- ❌ Recreating handle on every render for expensive objects — pass `[deps]` as third arg
