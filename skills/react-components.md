---
name: react-components
description: Scaffold new React components with TypeScript, Storybook stories, tests, and proper exports. Use when adding UI components to a React or Next.js project. NOT for refactoring existing components (use refactor skill) or writing tests for existing components (use test skill).
---

# React Component Scaffolding

## Environment Scope

**write+validate** — Writes component files (tsx, stories, tests). Runs `npx tsc --noEmit` to validate TypeScript compiles. Does NOT start dev server or storybook.

## Workflow

1. **Check Existing State** — Does `src/components/<ComponentName>/` already exist? If yes, report "component already exists" and ask if user wants to extend or refactor it instead.
2. **Gather Context** — Read `src/components/` directory listing to understand naming patterns. Read the nearest barrel file to understand export conventions.
3. **Generate Spec** — List files to create: index.tsx, ComponentName.tsx, ComponentName.stories.tsx, ComponentName.test.tsx. State which shadcn/ui primitives will be used. State props interface.
4. **Await Approval** — Present the spec. Do NOT create files until user confirms.
5. **Implement** — Create all component files following the templates below.
6. **Verify** — Run `npx tsc --noEmit` (expected: <10s). If type errors, enter failure loop.
7. **Document** — Add component to relevant barrel export. Note in PR description.

### Failure Recovery (max 3 retries)

6a. Read TypeScript error output → identify type mismatch or missing import
6b. Fix the specific file
6c. Re-run `npx tsc --noEmit`
6d. After 3 failures → show errors to user, ask for guidance

### Rollback

If user cancels mid-implementation:
1. Delete the entire `src/components/<ComponentName>/` directory
2. Revert any barrel file changes
3. Confirm with directory listing

## File Structure

Every component lives in `src/components/<ComponentName>/`:

```
ComponentName/
├── index.tsx                    # Barrel export
├── ComponentName.tsx            # Implementation
├── ComponentName.stories.tsx    # Storybook story
├── ComponentName.test.tsx       # Vitest tests
└── ComponentName.module.css     # Optional — only if Tailwind classes get unwieldy
```

## Templates

### Barrel Export
```tsx
export { ComponentName } from './ComponentName';
export type { ComponentNameProps } from './ComponentName';
```

### Component
```tsx
import { cn } from '@/lib/utils';

export interface ComponentNameProps {
  className?: string;
  children?: React.ReactNode;
}

export function ComponentName({ className, children }: ComponentNameProps) {
  return (
    <div className={cn('', className)}>
      {children}
    </div>
  );
}
```

### Storybook Story (CSF3)
```tsx
import type { Meta, StoryObj } from '@storybook/react';
import { ComponentName } from './ComponentName';

const meta: Meta<typeof ComponentName> = {
  component: ComponentName,
  tags: ['autodocs'],
};
export default meta;

type Story = StoryObj<typeof ComponentName>;

export const Default: Story = {
  args: {},
};

export const WithContent: Story = {
  args: { children: 'Example content' },
};
```

### Vitest Test
```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ComponentName } from './ComponentName';

describe('ComponentName', () => {
  it('renders without crashing', () => {
    render(<ComponentName />);
  });

  it('applies custom className', () => {
    const { container } = render(<ComponentName className="custom" />);
    expect(container.firstChild).toHaveClass('custom');
  });
});
```

## Guardrails

- NEVER create a component without a Storybook story — no exceptions
- NEVER skip the test file — every component ships with at least a render test
- NEVER use a custom solution when a shadcn/ui primitive exists for the same purpose
- NEVER create a component without a TypeScript props interface export
- NEVER create tables without AG Grid or charts without Recharts/uPlot
- NEVER put shared state directly in a component — use Zustand store
- NEVER skip accessibility: components must have proper ARIA attributes and keyboard support

## Checklist

- [ ] Component file with TypeScript props interface
- [ ] Barrel export in index.tsx
- [ ] Storybook story with at least Default + one variant
- [ ] Vitest test covering render and key interactions
- [ ] Accessibility: proper ARIA attributes, keyboard navigation
- [ ] Responsive: works at mobile/tablet/desktop breakpoints

## References

- `steering/conventions/code-style.md` — TypeScript naming, file organization, import ordering, component patterns
- `steering/preferences/stack/react/dependency-graph.md` — Full stack choices, import rules, and patterns
- `steering/preferences/stack/nextjs/server-components.md` — When to use 'use client' vs server component (check BEFORE scaffolding)
- `steering/preferences/stack/nextjs/app-router.md` — File-based routing context for page/layout components
