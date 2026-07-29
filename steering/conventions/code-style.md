# Code Style Conventions

## Why This Exists

Inconsistent naming, file organization, and import ordering create cognitive load during code review and make grep/search unreliable. These conventions ensure any developer (or AI agent) can predict where code lives and how it's named without checking each file individually.

## TypeScript Naming

### Why These Patterns

- **PascalCase for types/components:** Matches React's component detection (lowercase = HTML element, PascalCase = component). Also distinguishes types from values at a glance.
- **camelCase for variables/functions:** JavaScript convention. Fighting it creates friction with every library and tool.
- **SCREAMING_SNAKE for constants:** Visually distinct from mutable variables. Immediately signals "this never changes."
- **kebab-case for files:** Avoids case-sensitivity issues across OS (macOS is case-insensitive, Linux is not). URLs and imports are cleaner.

| Target | Convention | Example |
|--------|-----------|---------|
| Components | PascalCase | `UserProfile.tsx` → `export function UserProfile()` |
| Hooks | camelCase with `use` prefix | `useAuth.ts` → `export function useAuth()` |
| Utilities | camelCase | `formatDate.ts` → `export function formatDate()` |
| Constants | SCREAMING_SNAKE_CASE | `export const MAX_RETRY_COUNT = 3` |
| Types/Interfaces | PascalCase | `export interface UserProfile {}` |
| Enums | PascalCase (enum + members) | `export enum UserRole { Admin, Editor }` |
| File names | kebab-case | `user-profile.tsx`, `use-auth.ts`, `format-date.ts` |
| Directory names | kebab-case | `user-management/`, `api-client/` |
| CSS classes | kebab-case (Tailwind) | Already enforced by Tailwind |
| Environment variables | SCREAMING_SNAKE_CASE | `DATABASE_URL`, `API_BASE_URL` |

### Naming Rules

```typescript
// ✅ Good — name describes what it IS or DOES
const isAuthenticated = checkToken(token);
function calculateTotalPrice(items: CartItem[]): number {}
interface CreateWidgetRequest {}

// ❌ Bad — vague, abbreviated, or misleading
const flag = checkToken(token);
function calc(i: any[]): number {}
interface ICreateWidgetRequest {} // No I- prefix for interfaces
```

- No `I` prefix for interfaces (TypeScript convention, not C#)
- No `T` prefix for type parameters (use descriptive names: `TItem`, `TResponse`)
- Boolean variables: `is`, `has`, `can`, `should` prefix
- Event handlers: `on` prefix for props, `handle` prefix for implementations

```typescript
// Props use "on" — implementation uses "handle"
interface ButtonProps {
  onSubmit: () => void;  // What the parent passes
}

function Form() {
  const handleSubmit = () => { /* ... */ };  // What this component does
  return <Button onSubmit={handleSubmit} />;
}
```

## File Organization

### Why This Structure

- **Feature-based grouping** (not type-based): When you work on "users", you open one folder — not hunt across `components/`, `hooks/`, `services/`, `types/`. Reduces context switching.
- **Barrel exports**: Consumers import from the folder, not specific files. Internal refactoring doesn't break imports.
- **Colocated tests**: Test is always next to the code. No mirrored `__tests__/` directory that falls out of sync.

```
src/
├── components/              # Shared UI components
│   └── button/
│       ├── index.ts
│       ├── button.tsx
│       ├── button.stories.tsx
│       └── button.test.tsx
├── features/                # Feature modules (domain logic + UI)
│   └── users/
│       ├── index.ts         # Public API of this feature
│       ├── components/      # Feature-specific components
│       ├── hooks/           # Feature-specific hooks
│       ├── api.ts           # API calls for this feature
│       ├── store.ts         # Zustand slice for this feature
│       ├── types.ts         # Types scoped to this feature
│       └── utils.ts         # Helpers scoped to this feature
├── hooks/                   # Shared hooks (used across features)
├── lib/                     # Third-party wrappers, utilities
├── stores/                  # Global Zustand stores
├── types/                   # Shared type definitions
└── app/                     # Next.js App Router pages (or routes/)
```

### Rules

- Shared code lives in `components/`, `hooks/`, `lib/`, `types/`
- Feature-specific code lives in `features/<name>/`
- A file belongs in `features/` if it's only imported within that feature
- Promote to shared only when a second feature needs it
- Maximum directory depth: 4 levels from `src/`

## Import Ordering

### Why Enforce Order

Consistent import ordering makes diffs cleaner (no import reordering noise), makes it easy to scan what a file depends on, and prevents circular dependency confusion by making the dependency hierarchy visible.

```typescript
// 1. Node/framework built-ins
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';

// 2. External dependencies (node_modules)
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';

// 3. Internal shared modules (absolute imports via @/ alias)
import { Button } from '@/components/button';
import { useAuth } from '@/hooks/use-auth';
import { cn } from '@/lib/utils';

// 4. Relative imports (same feature/module)
import { UserCard } from './components/user-card';
import { useUserStore } from './store';
import type { User } from './types';

// 5. Styles (if any)
import './styles.css';
```

### Rules

- Blank line between each group
- Alphabetical within each group
- `type` imports at the bottom of their group or use `import type` inline
- Enforce with ESLint (`eslint-plugin-import` + `sort-imports`) — not manually

### ESLint Config

```json
{
  "rules": {
    "import/order": ["error", {
      "groups": ["builtin", "external", "internal", "parent", "sibling", "index"],
      "pathGroups": [{ "pattern": "@/**", "group": "internal" }],
      "newlines-between": "always",
      "alphabetize": { "order": "asc" }
    }]
  }
}
```

## Component Patterns

### Why These Patterns

- **Function components only:** Classes add ceremony, don't compose with hooks, and are being deprecated from React docs. No reason to use them.
- **Props interface always exported:** Enables composition — parent components can extend or pick from child props.
- **Destructured props:** Makes the component's API visible in the signature without scrolling to usage.

```typescript
// ✅ Standard component pattern
export interface UserCardProps {
  user: User;
  onSelect?: (user: User) => void;
  className?: string;
}

export function UserCard({ user, onSelect, className }: UserCardProps) {
  return (
    <div className={cn('rounded-lg border p-4', className)}>
      <h3>{user.name}</h3>
      {onSelect && (
        <Button onClick={() => onSelect(user)}>Select</Button>
      )}
    </div>
  );
}
```

### Rules

- No default exports (except Next.js pages/layouts where required)
- Why: named exports enable reliable refactoring (rename propagates) and prevent import aliasing confusion
- `className` prop always optional, always last visual prop
- Render logic over 20 lines → extract to a sub-component or custom hook
- Side effects only in hooks, never in render body

## Anti-Patterns

```typescript
// ❌ Default export (unreliable refactoring)
export default function UserCard() {}

// ❌ Prop spreading without type safety
function Card(props: any) { return <div {...props} /> }

// ❌ Index files with logic (should only re-export)
// index.ts should be: export { UserCard } from './user-card';
// NOT: export function UserCard() { ... }

// ❌ Barrel files that re-export everything (tree-shaking killer)
export * from './user-card';
export * from './user-list';
// Instead: export specific named exports

// ❌ Relative imports reaching up more than 2 levels
import { Button } from '../../../components/button'; // Use @/components/button

// ❌ Mixing concerns in one file (component + API call + store)
// Split into: component.tsx, api.ts, store.ts
```

## Commit Message Format

### Why Conventional Commits

Enables automated changelogs, semantic versioning, and makes git history searchable by type of change.

```
<type>(<scope>): <short description>

<body — optional, explains WHY>

<footer — optional, references issues>
```

| Type | When |
|------|------|
| `feat` | New feature |
| `fix` | Bug fix |
| `refactor` | Code change that neither fixes nor adds |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `chore` | Build, CI, tooling changes |
| `perf` | Performance improvement |

```
feat(users): add role-based filtering to user list

Admins need to filter users by role to manage permissions efficiently.
Previously required a database query each time.

Closes #142
```
