---
name: ReactUseCallback
description: Steering for useCallback — stabilizing function references for memoized children and custom hooks
inclusion: manual
fileMatchPattern: [
  "**/src/**/*.tsx",
  "**/src/**/*.jsx",
  "**/src/**/*.ts",
  "**/src/**/*.js"
]
---

# useCallback Steering

## When to Use

- Passing a callback to a memoized child component (`React.memo`) — prevents unnecessary re-renders
- Returning functions from custom hooks — consumers depend on stable references
- Callback is listed as a dependency of `useEffect`, `useMemo`, or another `useCallback`
- Event handler passed to a list of items rendered with `React.memo`

**Note:** React Compiler (React 19+) automatically memoizes functions in many cases. Manual `useCallback` is increasingly unnecessary in compiled codebases — use it only when profiling confirms a performance issue or when custom hook contracts require stability.

## Best Practices

- Wrap all function return values from custom hooks in `useCallback` — hook consumers cannot control re-render frequency
- Prefer moving the function inside `useEffect` over wrapping it in `useCallback` when the function is only used by that effect
- Keep the dependency array minimal — every dep is a cache-bust opportunity
- If a callback closes over state that changes frequently, consider `useReducer` + dispatch (dispatch is always stable)

## Example Use

### Stable callback for memoized child

```tsx
interface ItemListProps {
  items: Item[];
  onSelect: (id: string) => void;
}

const ItemList = React.memo(function ItemList({ items, onSelect }: ItemListProps) {
  return (
    <ul>
      {items.map((item) => (
        <li key={item.id}>
          <button onClick={() => onSelect(item.id)}>{item.name}</button>
        </li>
      ))}
    </ul>
  );
});

function Dashboard({ items }: { items: Item[] }) {
  const [selected, setSelected] = useState<string | null>(null);

  const handleSelect = useCallback((id: string) => {
    setSelected(id);
  }, []);

  return <ItemList items={items} onSelect={handleSelect} />;
}
```

### Custom hook returning a stable function

```tsx
export function useToggle(initial = false) {
  const [value, setValue] = useState(initial);

  const toggle = useCallback(() => setValue((v) => !v), []);
  const setTrue = useCallback(() => setValue(true), []);
  const setFalse = useCallback(() => setValue(false), []);

  return { value, toggle, setTrue, setFalse } as const;
}
```

## Pitfalls (react.dev Caveats)

- **Forgot dependency array** → returns a new function every render, defeating the purpose entirely
- **Cannot call in loops** — extract the loop body into a child component that calls `useCallback` internally
- **Strict Mode calls component twice** — callback recreation is expected; don't rely on side effects during creation
- **Cache is not guaranteed** — React may discard memoized values (e.g., on offscreen component suspension). Never rely on `useCallback` for correctness, only performance
- **Object/array deps** — inline `{}` or `[]` in the dependency array breaks memoization every render. Stabilize deps first or move them outside the component

## Error Handling

- `useCallback` itself never throws — errors happen when the returned function executes
- Wrap async callbacks in try/catch inside the callback body, not outside `useCallback`
- If a callback triggers a mutation, error handling belongs in the `useMutation.onError` callback (TanStack Query), not in `useCallback`

## Works With

| Hook | Relationship |
|------|-------------|
| `React.memo` | Primary consumer — stable callback prevents child re-render |
| `useEffect` | Stable callback as a dependency avoids effect re-runs |
| `useMemo` | Often paired — memoized data + memoized handler passed together |
| `useReducer` | `dispatch` is already stable — prefer over `useCallback` wrapping setState |
| `useRef` | Use ref inside callback to read latest value without adding deps |

## Anti-Patterns

- ❌ Wrapping every function in `useCallback` without a memoized consumer — adds complexity with zero benefit
- ❌ Using `useCallback` to "prevent re-creation" when no child is memoized — React doesn't care about function identity unless something compares it
- ❌ Putting the entire component state in the dependency array — negates memoization
- ❌ `useCallback` with an empty deps array that reads stale state — use a ref or `useReducer` instead
- ❌ Wrapping inline event handlers on native DOM elements (`<button onClick={...}>`) — DOM elements are not memoized, so `useCallback` does nothing
