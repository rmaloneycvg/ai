# React Technology Stack — AI Agent Steering

> Standard dependency choices, patterns, and conventions for all React projects. Follow prescriptively when generating code.

## Why These Choices

| Decision | Why this over alternatives |
|----------|--------------------------|
| **shadcn/ui + Tailwind** | Unstyled primitives = full control. No CSS-in-JS runtime cost. Copy-paste ownership vs. opaque npm dependency. |
| **Zustand** | Minimal API surface (3 functions), no providers/context boilerplate, works outside React. Redux is overkill for most apps. |
| **TanStack Query** | Solves cache invalidation, background refetching, optimistic updates, request deduplication. Fetch/axios alone require reinventing all of these. |
| **React Hook Form + Zod** | RHF minimizes re-renders (uncontrolled under the hood). Zod provides runtime + TypeScript types from one schema. Formik re-renders on every keystroke. |
| **AG Grid** | Enterprise-grade features (virtual scrolling, server-side row model, column pinning) without building from scratch. Every other table library hits a wall at 10k rows. |
| **Recharts / uPlot** | Recharts for standard dashboards (easy API). uPlot when rendering 100k+ data points (10x faster, no React reconciliation). |
| **Vitest** | Same config as Vite. Jest-compatible API. Faster via ESM-native transforms. |
| **Playwright** | Cross-browser, auto-waits, accessibility locators. Cypress is single-tab only and slower. |
| **Storybook** | Living documentation, visual regression, component isolation. Every component must be viewable in isolation. |

## Key Relationships

- **Zustand** holds client-side state; **TanStack Query** holds server-side state. Never duplicate server state into Zustand.
- **React Hook Form** manages form state independently. **Zod** schemas are the single source of truth for validation — shared with API types.
- **shadcn/ui** provides accessible primitives. All custom components compose on top of these.
- **AG Grid** for ANY tabular data. Do not build custom table components.
- **Recharts** for dashboard/business charts. **uPlot** only when datasets exceed 10k points or need 60fps pan/zoom.

---

## Stack Rules

### TypeScript (Strict Mode)

- Every file is `.ts` or `.tsx`. No `.js` in source.
- `"strict": true, "noUncheckedIndexedAccess": true, "exactOptionalPropertyTypes": true`
- Define API response types from Zod schemas: `z.infer<typeof schema>`
- Use discriminated unions for state machines and component variants
- Prefer `interface` for extendable shapes; `type` for unions and computed types
- Use `satisfies` for type-safe constants
- Never `any` — use `unknown` + narrowing
- No `as` assertions — narrow instead
- No enums — use `as const` objects or union literals
- `@ts-expect-error` (with comment) over `@ts-ignore`

### shadcn/ui + Tailwind CSS

- Install on-demand: `npx shadcn-ui@latest add [component]`
- Components: `src/components/ui/` (shadcn primitives), `src/components/` (app components)
- Use `cn()` utility for conditional class merging
- Don't modify `components/ui/` directly — wrap them
- CSS variables for theming in `globals.css`
- Tailwind design tokens only — no arbitrary values unless necessary
- No separate component library (MUI, Ant Design, Chakra)
- No `@apply` abuse — inline classes preferred
- No one-off CSS files — use CSS variables in `globals.css` if Tailwind can't express it

### Zustand (State Management)

**When:** Client-only state NOT from server. UI state, preferences, wizard steps, selected items.

- One store per domain: `useAuthStore`, `useUIStore`, `useCartStore` in `src/stores/`
- Always use selectors: `const count = useStore(s => s.count)` — never destructure entire store
- `immer` middleware for complex nested updates
- `persist` middleware for localStorage when needed
- Don't put API data in Zustand — that's TanStack Query's job
- Don't create a store for single-component state — use `useState`

### TanStack Query

**When:** ALL server-state — fetching, mutations, cache invalidation, optimistic updates.

- Query keys as hierarchical arrays: `['users', userId, 'posts']`
- Central key factory in `src/lib/query-keys.ts`
- Custom hooks per query in `src/hooks/queries/`
- Optimistic updates for all mutations affecting visible UI (cancel → snapshot → set → rollback on error → invalidate on settle)
- Defaults: `staleTime: 5 * 60 * 1000`, `gcTime: 10 * 60 * 1000`
- Pair with Zod for runtime response validation in `queryFn`
- Use `prefetchQuery()` in route loaders for instant navigation
- Never use `useEffect` + `useState` for data fetching
- Never set `staleTime: 0` globally
- Always invalidate related queries after mutations

### React Hook Form + Zod

**When:** Every form — login, settings, CRUD, filters, wizards.

- Define Zod schema first → infer TypeScript type → `zodResolver`
- Always provide `defaultValues`
- Use shadcn/ui `<Form>` + `<FormField>` pattern (not `register` directly)
- `useFieldArray` for dynamic lists
- Share schemas between frontend validation and API request/response typing
- Mutation on submit connects to TanStack Query `useMutation`
- Don't validate on every keystroke for expensive ops — use `mode: 'onBlur'` or `mode: 'onSubmit'`
- Don't create separate TypeScript interfaces that duplicate Zod schemas

### AG Grid

**When:** ANY data in rows and columns. Even simple lists with 3+ columns.

- `ag-grid-react` with Community or Enterprise as needed
- Typed `ColDef<T>[]` column definitions
- Custom cell renderers in `src/components/grid/cell-renderers/` — always extracted, never inline
- `domLayout='autoHeight'` for grids under 100 rows
- Always set `getRowId` for stable row identity
- Feed from TanStack Query: `rowData={query.data ?? []}`
- Loading: AG Grid's overlay tied to `query.isLoading`
- Style: Alpine theme with CSS variable overrides matching design tokens
- Don't build custom `<table>` elements — AG Grid handles all table needs

### Charts — Recharts + uPlot

**Recharts** (default, < 10k points): `<ResponsiveContainer>` wrapper required, composable elements, CSS variables for colors, custom tooltips/legends as React components, in `src/components/charts/`.

**uPlot** (performance, > 10k points): React wrapper managing lifecycle via refs, `useEffect` for init/destroy, `setData()` for updates (never re-create instances).

- Don't use uPlot for simple bar/pie charts
- Don't forget `<ResponsiveContainer>` with Recharts
- Import only used chart types (tree-shaking)

### Testing — Vitest + Playwright + Storybook

**Vitest** — unit/integration, co-located (`Component.test.tsx`):
- `@testing-library/react` for components, `msw` for API mocking
- Test behavior, not implementation
- `renderHook` for custom hooks
- Coverage: utilities 100%, hooks 90%+, components 80%+, stores 90%+

**Playwright** — E2E in `e2e/`, critical user flows:
- Page Object Model pattern
- Accessible roles/labels, not CSS selectors
- Fixtures for auth state

**Storybook** — every component, no exceptions:
- CSF3 format, `tags: ['autodocs']`
- All variants, states (loading, error, empty, disabled), sizes
- `@storybook/addon-a11y` for accessibility
- Interaction tests for visual regression + behavior

---

## Standard Project Structure

```
src/
├── app/                    # Route pages (file-based routing)
├── components/
│   ├── ui/                 # shadcn/ui primitives (don't modify directly)
│   ├── charts/             # Recharts/uPlot wrappers
│   ├── grid/cell-renderers/
│   └── forms/              # Reusable form components
├── hooks/
│   ├── queries/            # TanStack Query hooks
│   └── mutations/          # TanStack Query mutations
├── stores/                 # Zustand stores (*.store.ts)
├── lib/
│   ├── utils.ts            # cn() and shared utilities
│   ├── api.ts              # API client wrapper
│   ├── query-keys.ts       # Query key factories
│   └── query-client.ts     # QueryClient config
├── schemas/                # Zod schemas (*.schema.ts)
├── types/                  # TypeScript types (inferred from Zod where possible)
├── styles/globals.css      # Tailwind directives + CSS variables
└── test/
    ├── setup.ts            # Vitest global setup
    ├── mocks/              # MSW handlers
    └── utils.tsx           # Custom render, providers wrapper

e2e/
├── fixtures/
├── pages/                  # Page Object Models
└── specs/
```

### Naming Conventions

- Components: PascalCase (`UserProfile.tsx`)
- Hooks: camelCase with `use` prefix (`useUser.ts`)
- Stores: `*.store.ts` (`auth.store.ts`)
- Schemas: `*.schema.ts` (`user.schema.ts`)
- Tests: co-located `.test.tsx`
- Stories: co-located `.stories.tsx`

---

## Performance Rules

- `React.memo()` only when profiling confirms unnecessary re-renders
- Zustand selectors over context for frequently-updated global state
- `useDeferredValue` for expensive filter/search computations
- `React.lazy()` + `Suspense` for route-level code splitting
- `useCallback`/`useMemo` when passing to memoized children or as deps
- TanStack Query `staleTime` prevents redundant requests — tune per query
- `placeholderData` for instant perceived performance
- Paginate AG Grid server-side for > 1,000 rows
- `keepPreviousData` for paginated views to prevent layout shift
- Dynamic imports for heavy libs (AG Grid enterprise, uPlot)
- Monitor bundle with `vite-bundle-visualizer`

---

## Accessibility (Non-Negotiable)

- WCAG 2.1 AA minimum
- Every interactive element keyboard accessible
- Every form input has a visible label
- Color never the sole state indicator
- Focus management on route changes and modal open/close
- All images: meaningful `alt` or `alt=""` for decorative
- Minimum touch target: 44x44px mobile
- Semantic HTML: `<main>`, `<nav>`, `<section>`, `<article>`
- AG Grid: `headerName` on all columns
- Charts: text alternative (data table or `aria-label`)
- `aria-live="polite"` for dynamic content (toasts, loading)
- Test: `@storybook/addon-a11y` (every story), `jest-axe` in Vitest, keyboard flows in Playwright

---

## Decision Rules (Quick Reference)

| Question | Answer |
|----------|--------|
| Where does server data live? | TanStack Query cache — never in Zustand |
| Where does UI state live? | Zustand (cross-component) or useState (single component) |
| How do I validate a form? | Zod schema → zodResolver → React Hook Form |
| How do I display tabular data? | AG Grid — always |
| How do I style components? | Tailwind classes via `cn()` utility |
| How do I add a UI primitive? | `npx shadcn-ui@latest add [component]` |
| How do I chart business data? | Recharts |
| How do I chart large/realtime data? | uPlot |
| How do I test a component? | Vitest + Testing Library (behavior, not impl) |
| How do I test a user flow? | Playwright with Page Object Model |
| How do I document a component? | Storybook story (mandatory for all components) |
| How do I manage query keys? | Factory in `lib/query-keys.ts` |
| How do I handle loading states? | TanStack Query `isLoading`/`isPending` + Suspense |
| How do I handle errors? | Error boundaries + TanStack Query `isError` + toasts |

---

## Anti-Patterns (Never Do These)

1. `useEffect` for data fetching — use TanStack Query
2. Custom `<table>` — use AG Grid
3. CSS modules or styled-components — use Tailwind
4. Second component library — shadcn/ui is the standard
5. Server state in Zustand — TanStack Query owns it
6. Skip Storybook story — every component gets one
7. `any` type — use `unknown` and narrow
8. Uncontrolled inputs without RHF — forms always use React Hook Form
9. Custom validation logic — Zod handles all validation
10. Skip accessibility — every PR must pass axe-core checks
