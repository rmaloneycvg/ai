---
name: ReactUseContext
description: Steering for useContext — when to prefer it over Zustand, scoping patterns, and performance considerations
inclusion: manual
fileMatchPattern: [
  "**/src/**/*.tsx",
  "**/src/**/*.jsx",
  "**/src/**/*.ts",
  "**/src/**/*.js"
]
---

# useContext Steering

> **Zustand is the default for global state.** useContext is the fallback for narrow, infrequently-updated shared data where adding a store is overkill.

## When to Use

- Passing data through deep component trees without prop drilling
- Theming (light/dark mode, design tokens)
- Locale / i18n provider
- Auth state in small apps with few consumers
- Dependency injection (providing a service instance to a subtree)

## When to Use Zustand Instead

| Condition | Use Zustand |
|-----------|-------------|
| State updates frequently (timers, cursors, form state) | ✅ Context re-renders all consumers |
| Need selectors to avoid unnecessary re-renders | ✅ Context has no selector mechanism |
| State accessed outside React (utils, middleware) | ✅ Context only works inside components |
| Complex state transitions (reducers, immer) | ✅ Zustand + immer middleware |
| Multiple unrelated consumers need different slices | ✅ Selectors prevent over-rendering |

## Best Practices

- Split context into `StateContext` and `DispatchContext` to prevent dispatch-only consumers from re-rendering on state changes
- Memoize the context value object to prevent referential inequality re-renders
- Provide a custom hook that throws if used outside the provider
- Keep context values small and stable — primitives or memoized objects

## Example Use

### Theme Context (Provider + Consumer Pattern)

```tsx
// contexts/theme-context.tsx
import { createContext, useContext, useState, useMemo, useCallback, type ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextValue {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light');

  const toggleTheme = useCallback(() => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  }, []);

  // Memoize to prevent re-renders when parent re-renders
  const value = useMemo(() => ({ theme, toggleTheme }), [theme, toggleTheme]);

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}
```

```tsx
// Usage in a component
import { useTheme } from '@/contexts/theme-context';

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <Button onClick={toggleTheme}>
      Current: {theme}
    </Button>
  );
}
```

## Pitfalls

### Every consumer re-renders on any value change

Context has no selector mechanism. If `value` has 5 properties and one changes, all consumers re-render — even those reading only the unchanged properties.

```tsx
// ❌ All consumers re-render when either user OR permissions changes
const value = { user, permissions };
```

**Fix:** Split into separate contexts or use Zustand.

### Inline object values cause re-renders every render

```tsx
// ❌ New object reference every render — all consumers re-render
<MyContext.Provider value={{ count, increment }}>

// ✅ Memoized — stable reference when deps unchanged
const value = useMemo(() => ({ count, increment }), [count, increment]);
<MyContext.Provider value={value}>
```

### Missing provider causes silent `undefined`

```tsx
// ❌ Returns undefined, component silently breaks
const value = useContext(MyContext);

// ✅ Custom hook with guard
export function useMyContext() {
  const ctx = useContext(MyContext);
  if (!ctx) throw new Error('useMyContext must be used within MyProvider');
  return ctx;
}
```

## Error Handling

- Always use a custom hook that throws when context is null (missing provider)
- Wrap provider logic in error boundaries if the provider itself fetches data
- For async data in context, expose loading/error states alongside the value

## Works With

| Dependency | Integration |
|-----------|-------------|
| **Zustand** | Context for tree-scoped state (per-dialog instance), Zustand for global |
| **React Hook Form** | Context can provide form-level config; RHF manages actual form state |
| **shadcn/ui** | Theme context feeds CSS variables consumed by shadcn components |

## Anti-Patterns

- ❌ Using context for frequently-updated state (use Zustand)
- ❌ Single monolithic context with all app state
- ❌ Inline object/array values without `useMemo`
- ❌ Using context instead of props for parent→child (one level deep)
- ❌ Putting server state in context (use TanStack Query)
- ❌ Deep provider nesting (5+ providers) — consolidate or use Zustand
