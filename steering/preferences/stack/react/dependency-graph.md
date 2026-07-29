# React Technology Stack — AI Agent Steering

> This document defines the standard dependency choices, patterns, and conventions for all React projects. Follow these prescriptively when generating code.

## Why These Choices

Each dependency was chosen to eliminate decision paralysis and prevent incompatible library combinations:

| Decision | Why this over alternatives |
|----------|--------------------------|
| **shadcn/ui + Tailwind** | Unstyled primitives = full control. No CSS-in-JS runtime cost. Copy-paste ownership vs. opaque npm dependency. |
| **Zustand** | Minimal API surface (3 functions), no providers/context boilerplate, works outside React (tests, utils). Redux is overkill for most apps. |
| **TanStack Query** | Solves cache invalidation, background refetching, optimistic updates, and request deduplication. Fetch/axios alone require reinventing all of these. |
| **React Hook Form + Zod** | RHF minimizes re-renders (uncontrolled under the hood). Zod provides runtime + TypeScript types from one schema. Formik re-renders on every keystroke. |
| **AG Grid** | Enterprise-grade features (virtual scrolling, server-side row model, column pinning) without building them from scratch. Every other table library hits a wall at 10k rows. |
| **Recharts / uPlot** | Recharts for standard dashboards (easy API, React-native). uPlot when rendering 100k+ data points (10x faster, no React reconciliation overhead). |
| **Vitest** | Same config as Vite (one less tool). Jest-compatible API. Faster execution via ESM-native transforms. |
| **Playwright** | Cross-browser, auto-waits, accessibility locators built-in. Cypress is single-tab only and slower. |
| **Storybook** | Living documentation, visual regression testing, component isolation for development. Every component must be viewable in isolation. |

## Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐   ┌──────────────┐   ┌────────────────────────┐  │
│  │ Zustand  │   │ TanStack     │   │ React Hook Form + Zod  │  │
│  │ (state)  │◄──│ Query (data) │   │ (form state + valid.)  │  │
│  └────┬─────┘   └──────┬───────┘   └───────────┬────────────┘  │
│       │                 │                       │               │
│       ▼                 ▼                       ▼               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              shadcn/ui + Tailwind CSS                     │   │
│  │              (UI primitives + styling)                    │   │
│  └──────────┬───────────┬───────────────────┬───────────────┘   │
│             │           │                   │                   │
│             ▼           ▼                   ▼                   │
│  ┌──────────────┐ ┌──────────┐    ┌─────────────────┐          │
│  │   AG Grid    │ │ Recharts │    │     uPlot       │          │
│  │  (tables)    │ │ (charts) │    │ (perf charts)   │          │
│  └──────────────┘ └──────────┘    └─────────────────┘          │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                        Foundation                                │
│  TypeScript (strict) · React 18+ · Vite                         │
├─────────────────────────────────────────────────────────────────┤
│                     Testing & Docs                               │
│  Vitest (unit/integration) · Playwright (E2E) · Storybook       │
└─────────────────────────────────────────────────────────────────┘
```

### Key Relationships

- **Zustand** holds client-side state; **TanStack Query** holds server-side state. Never duplicate server state into Zustand.
- **React Hook Form** manages form state independently. Use **Zod** schemas as the single source of truth for validation — share them with API types.
- **shadcn/ui** provides accessible primitives. All custom components compose on top of these.
- **AG Grid** is used for ANY tabular data display. Do not build custom table components.
- **Recharts** for dashboard/business charts. **uPlot** only when datasets exceed 10k points or need 60fps pan/zoom.

---

## Core Stack Details

### 1. TypeScript (Strict Mode)

**When to use:** Always. Every file is `.ts` or `.tsx`. No `.js` files in source.

**Key patterns:**
- Enable all strict flags in `tsconfig.json`: `"strict": true, "noUncheckedIndexedAccess": true, "exactOptionalPropertyTypes": true`
- Define API response types from Zod schemas using `z.infer<typeof schema>`
- Use discriminated unions for state machines and component variants
- Prefer `interface` for object shapes that may be extended; `type` for unions and computed types
- Use `satisfies` operator for type-safe constant definitions
- Never use `any`. Use `unknown` + type narrowing when type is uncertain

**Common pitfalls:**
- Avoid type assertions (`as`) — they hide bugs. Narrow instead.
- Don't use enums — use `as const` objects or union literal types
- Don't ignore TypeScript errors with `@ts-ignore`. Use `@ts-expect-error` only with a comment explaining why

---

### 2. shadcn/ui + Tailwind CSS

**When to use:** All UI rendering. shadcn/ui is the component library. Tailwind is the only styling approach.

**Key patterns:**
- Install shadcn/ui components on-demand via CLI: `npx shadcn-ui@latest add button`
- Components live in `src/components/ui/` (shadcn primitives) and `src/components/` (app components)
- Use `cn()` utility (from `lib/utils.ts`) for conditional class merging
- Follow shadcn/ui's composition pattern — don't modify files in `components/ui/` directly; wrap them
- Use CSS variables for theming (defined in `globals.css`)
- Use Tailwind's design tokens exclusively — no arbitrary values unless absolutely necessary

**Integration notes:**
- shadcn/ui is built on Radix UI primitives — leverage their accessibility props
- AG Grid styling: override AG Grid theme CSS variables to match Tailwind design tokens
- Form components from shadcn/ui integrate directly with React Hook Form via `<FormField>`

**Common pitfalls:**
- Don't install a separate component library (MUI, Ant Design, Chakra). shadcn/ui is the answer.
- Don't use `@apply` excessively — inline Tailwind classes are preferred
- Don't create one-off CSS files. If Tailwind can't express it, use CSS variables in `globals.css`

---

### 3. Zustand (State Management)

**When to use:** Client-only state that is NOT server data. Examples: UI state (sidebar open/closed), user preferences, wizard step tracking, selected items for batch actions.

**Key patterns:**
- One store per domain concern: `useAuthStore`, `useUIStore`, `useCartStore`
- Store files live in `src/stores/`
- Use slices pattern for large stores
- Always use selectors to prevent unnecessary re-renders:
  ```tsx
  // ✅ Good — component only re-renders when count changes
  const count = useStore((state) => state.count);
  
  // ❌ Bad — re-renders on ANY store change
  const { count } = useStore();
  ```
- Use `immer` middleware for complex nested state updates
- Persist stores to localStorage with `persist` middleware when needed

**Integration notes:**
- TanStack Query owns server state. Zustand owns client state. If data comes from an API, it belongs in TanStack Query.
- Use Zustand for cross-component UI coordination that doesn't warrant prop drilling or context
- Zustand stores can read TanStack Query cache via `queryClient.getQueryData()` in actions when needed

**Common pitfalls:**
- Don't put API response data in Zustand — that's TanStack Query's job
- Don't create a store for state used by a single component — use `useState`
- Don't subscribe to entire store objects; always use granular selectors

---

### 4. TanStack Query (React Query)

**When to use:** ALL server-state: API calls, data fetching, mutations, cache invalidation, optimistic updates.

**Key patterns:**
- Query keys are arrays with hierarchical structure: `['users', userId, 'posts']`
- Define query keys in a central `src/lib/query-keys.ts` file as factory functions:
  ```tsx
  export const userKeys = {
    all: ['users'] as const,
    lists: () => [...userKeys.all, 'list'] as const,
    list: (filters: UserFilters) => [...userKeys.lists(), filters] as const,
    details: () => [...userKeys.all, 'detail'] as const,
    detail: (id: string) => [...userKeys.details(), id] as const,
  };
  ```
- Custom hooks per query in `src/hooks/queries/`:
  ```tsx
  export function useUser(id: string) {
    return useQuery({
      queryKey: userKeys.detail(id),
      queryFn: () => api.users.get(id),
    });
  }
  ```
- Implement optimistic updates for all mutations that affect visible UI:
  ```tsx
  useMutation({
    mutationFn: updateUser,
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: userKeys.detail(id) });
      const previous = queryClient.getQueryData(userKeys.detail(id));
      queryClient.setQueryData(userKeys.detail(id), newData);
      return { previous };
    },
    onError: (_err, _vars, context) => {
      queryClient.setQueryData(userKeys.detail(id), context?.previous);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: userKeys.detail(id) });
    },
  });
  ```
- Set sensible defaults in QueryClient: `staleTime: 5 * 60 * 1000`, `gcTime: 10 * 60 * 1000`

**Integration notes:**
- Pair with Zod for runtime response validation: `queryFn: () => api.get(url).then(res => schema.parse(res.data))`
- Use `queryClient.prefetchQuery()` in route loaders for instant navigation
- Combine with Zustand only when client-side derived state is needed across components

**Common pitfalls:**
- Don't use `useEffect` + `useState` for data fetching. TanStack Query handles loading, error, caching, retries.
- Don't set `staleTime: 0` globally — it causes excessive refetching
- Don't forget to invalidate related queries after mutations
- Don't use `refetchOnWindowFocus` in development without `staleTime` — it causes confusing refetches

---

### 5. React Hook Form + Zod

**When to use:** Every form in the application — login, settings, CRUD, filters, multi-step wizards.

**Key patterns:**
- Define Zod schema first, infer TypeScript type from it:
  ```tsx
  const createUserSchema = z.object({
    name: z.string().min(1, 'Name is required'),
    email: z.string().email('Invalid email'),
    role: z.enum(['admin', 'user', 'viewer']),
  });
  type CreateUserInput = z.infer<typeof createUserSchema>;
  ```
- Use `zodResolver` to connect schema to form:
  ```tsx
  const form = useForm<CreateUserInput>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { name: '', email: '', role: 'user' },
  });
  ```
- Use shadcn/ui `<Form>` components for consistent rendering:
  ```tsx
  <FormField control={form.control} name="email" render={({ field }) => (
    <FormItem>
      <FormLabel>Email</FormLabel>
      <FormControl><Input {...field} /></FormControl>
      <FormMessage />
    </FormItem>
  )} />
  ```
- Share Zod schemas between frontend validation and API request/response typing
- Use `useFieldArray` for dynamic form lists

**Integration notes:**
- shadcn/ui `<Form>` is built on React Hook Form — use it directly
- Mutation on submit connects to TanStack Query `useMutation`
- Zod schemas serve triple duty: form validation, API response validation, TypeScript types

**Common pitfalls:**
- Always provide `defaultValues` — omitting them causes uncontrolled-to-controlled warnings
- Don't use `register` with shadcn/ui components — use `Controller` or `FormField` pattern
- Don't validate on every keystroke for expensive validations — use `mode: 'onBlur'` or `mode: 'onSubmit'`
- Don't create separate TypeScript interfaces that duplicate Zod schemas

---

### 6. AG Grid

**When to use:** ANY data displayed in rows and columns. Even simple lists with 3+ columns use AG Grid. Do not build custom `<table>` elements.

**Key patterns:**
- Use AG Grid React (`ag-grid-react`) with AG Grid Community or Enterprise as needed
- Define column definitions with TypeScript:
  ```tsx
  const columnDefs: ColDef<User>[] = [
    { field: 'name', sortable: true, filter: true },
    { field: 'email', flex: 1 },
    { field: 'role', cellRenderer: RoleBadgeRenderer },
    { field: 'actions', cellRenderer: ActionsCellRenderer, sortable: false },
  ];
  ```
- Custom cell renderers are React components in `src/components/grid/cell-renderers/`
- Always set `domLayout='autoHeight'` for grids under 100 rows; use default for larger datasets
- Enable row virtualization for large datasets (default behavior)
- Use AG Grid's built-in features: sorting, filtering, pagination, row selection, column resizing

**Integration notes:**
- Feed data from TanStack Query: `rowData={query.data ?? []}`
- Loading state: use AG Grid's `loading` overlay tied to `query.isLoading`
- Selection state can flow to Zustand for cross-component batch actions
- Style with Tailwind: apply AG Grid's Alpine theme, override CSS variables to match your design tokens

**Common pitfalls:**
- Don't build custom table components — AG Grid handles all table needs
- Don't forget to set `getRowId` for stable row identity during updates
- Don't use AG Grid for simple key-value displays — use a description list instead
- Don't inline complex cell renderers — extract to named components for testability

---

### 7. Charts — Recharts + uPlot

#### Recharts (Default)

**When to use:** Standard business charts — bar, line, area, pie, radar, scatter. Any chart with fewer than 10,000 data points.

**Key patterns:**
- Wrap in responsive container: `<ResponsiveContainer width="100%" height={300}>`
- Use composable chart elements:
  ```tsx
  <LineChart data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="date" />
    <YAxis />
    <Tooltip content={<CustomTooltip />} />
    <Line type="monotone" dataKey="revenue" stroke="var(--chart-1)" />
  </LineChart>
  ```
- Use CSS variables for chart colors to support theming
- Custom tooltips and legends as React components for full control
- Chart components live in `src/components/charts/`

**Integration notes:**
- Data comes from TanStack Query hooks
- Use Zod to validate chart data shapes from API responses
- Wrap charts in error boundaries to prevent dashboard crashes

#### uPlot (Performance)

**When to use:** Large time-series data (10k+ points), real-time streaming charts, or when you need 60fps interactions (pan, zoom, scrub).

**Key patterns:**
- Create a React wrapper component that manages uPlot lifecycle:
  ```tsx
  function TimeSeriesChart({ data, options }: Props) {
    const chartRef = useRef<HTMLDivElement>(null);
    const uplotRef = useRef<uPlot>();
    
    useEffect(() => {
      if (!chartRef.current) return;
      uplotRef.current = new uPlot(options, data, chartRef.current);
      return () => uplotRef.current?.destroy();
    }, [options]);
    
    useEffect(() => {
      uplotRef.current?.setData(data);
    }, [data]);
    
    return <div ref={chartRef} />;
  }
  ```
- Use typed-array formats for data when possible for maximum performance
- Configure axes, scales, and series in options object

**Common pitfalls (both):**
- Don't use uPlot for simple bar/pie charts — the DX is worse for no benefit
- Don't forget `<ResponsiveContainer>` with Recharts — charts won't render without dimensions
- Don't re-create uPlot instances on data change — use `setData()` for updates
- Don't import all of Recharts — use tree-shaking: `import { LineChart, Line } from 'recharts'`

---

### 8. Testing — Vitest + Playwright + Storybook

#### Vitest (Unit & Integration)

**When to use:** All unit tests and component integration tests. Test files co-located with source: `Component.test.tsx` next to `Component.tsx`.

**Key patterns:**
- Use `@testing-library/react` for component tests
- Use `msw` (Mock Service Worker) for API mocking in integration tests
- Test behavior, not implementation:
  ```tsx
  it('submits the form with valid data', async () => {
    const onSubmit = vi.fn();
    render(<UserForm onSubmit={onSubmit} />);
    
    await userEvent.type(screen.getByLabelText('Name'), 'Jane Doe');
    await userEvent.type(screen.getByLabelText('Email'), 'jane@example.com');
    await userEvent.click(screen.getByRole('button', { name: /submit/i }));
    
    expect(onSubmit).toHaveBeenCalledWith({ name: 'Jane Doe', email: 'jane@example.com' });
  });
  ```
- Test custom hooks with `renderHook` from `@testing-library/react`
- Test Zustand stores by importing and calling actions directly
- Test TanStack Query hooks with `QueryClientProvider` wrapper

**Coverage targets:**
- Utility functions: 100%
- Custom hooks: 90%+
- Components: 80%+ (focus on user interactions and edge cases)
- Stores: 90%+

#### Playwright (E2E)

**When to use:** Critical user flows — auth, checkout, CRUD operations, multi-page wizards. Tests live in `e2e/` directory.

**Key patterns:**
- Use Page Object Model for reusable page interactions:
  ```tsx
  class LoginPage {
    constructor(private page: Page) {}
    async login(email: string, password: string) {
      await this.page.getByLabel('Email').fill(email);
      await this.page.getByLabel('Password').fill(password);
      await this.page.getByRole('button', { name: 'Sign in' }).click();
    }
  }
  ```
- Test against accessible roles and labels, not CSS selectors
- Use `test.describe` for logical grouping
- Run against a local dev server or preview build
- Use Playwright fixtures for auth state setup

#### Storybook (Component Documentation)

**When to use:** Every UI component gets a story. No exceptions.

**Key patterns:**
- Stories live next to components: `Button.stories.tsx`
- Use Component Story Format (CSF3):
  ```tsx
  import type { Meta, StoryObj } from '@storybook/react';
  
  const meta: Meta<typeof Button> = {
    component: Button,
    tags: ['autodocs'],
  };
  export default meta;
  
  type Story = StoryObj<typeof Button>;
  
  export const Default: Story = { args: { children: 'Click me' } };
  export const Disabled: Story = { args: { children: 'Disabled', disabled: true } };
  export const Loading: Story = { args: { children: 'Loading', loading: true } };
  ```
- Document all variants, states (loading, error, empty, disabled), and sizes
- Use `@storybook/addon-a11y` for automatic accessibility checking
- Use interaction tests in stories for visual regression + behavior

**Common pitfalls (testing):**
- Don't mock what you don't own excessively — prefer MSW over mocking fetch directly
- Don't write E2E tests for things unit tests can cover
- Don't skip stories for "simple" components — they always grow complexity
- Don't test implementation details (internal state, private methods)

---

## Standard Project Structure

```
src/
├── app/                    # Route pages (if using file-based routing)
│   ├── layout.tsx
│   └── (routes)/
├── components/
│   ├── ui/                 # shadcn/ui primitives (do not modify directly)
│   ├── charts/             # Recharts/uPlot wrapper components
│   ├── grid/
│   │   └── cell-renderers/ # AG Grid custom cell renderers
│   ├── forms/              # Reusable form components
│   └── [feature]/          # Feature-specific components
├── hooks/
│   ├── queries/            # TanStack Query custom hooks (useUser, usePosts, etc.)
│   ├── mutations/          # TanStack Query mutation hooks
│   └── [domain].ts         # Other custom hooks
├── stores/                 # Zustand stores
│   ├── ui.store.ts
│   └── auth.store.ts
├── lib/
│   ├── utils.ts            # cn() and shared utilities
│   ├── api.ts              # API client (axios/fetch wrapper)
│   ├── query-keys.ts       # TanStack Query key factories
│   └── query-client.ts     # QueryClient configuration
├── schemas/                # Zod schemas (shared between forms and API)
│   ├── user.schema.ts
│   └── common.schema.ts
├── types/                  # TypeScript types (inferred from Zod where possible)
├── styles/
│   └── globals.css         # Tailwind directives + CSS variables
└── test/
    ├── setup.ts            # Vitest global setup
    ├── mocks/              # MSW handlers
    └── utils.tsx           # Test utilities (custom render, providers wrapper)

e2e/
├── fixtures/               # Playwright fixtures
├── pages/                  # Page Object Models
└── specs/                  # Test spec files
```

### Naming Conventions

- Components: PascalCase (`UserProfile.tsx`)
- Hooks: camelCase with `use` prefix (`useUser.ts`)
- Stores: camelCase with `.store.ts` suffix (`auth.store.ts`)
- Schemas: camelCase with `.schema.ts` suffix (`user.schema.ts`)
- Tests: same name with `.test.tsx` suffix, co-located
- Stories: same name with `.stories.tsx` suffix, co-located

---

## Performance Considerations

### Rendering

- Use `React.memo()` only when profiling confirms unnecessary re-renders
- Prefer Zustand selectors over context for frequently-updated global state
- Use `useDeferredValue` for expensive filter/search computations
- Lazy-load route-level components with `React.lazy()` + `Suspense`
- Use `useCallback` and `useMemo` when passing callbacks/objects to memoized children or as deps

### Data

- TanStack Query `staleTime` prevents redundant network requests — tune per query
- Use `placeholderData` for instant perceived performance during navigation
- Paginate AG Grid server-side for datasets over 1,000 rows
- Use `keepPreviousData` in TanStack Query for paginated views to prevent layout shift

### Bundle Size

- Import shadcn/ui components individually (they're local files, so tree-shaking is automatic)
- Use dynamic imports for heavy libraries: AG Grid enterprise modules, uPlot
- Recharts supports tree-shaking — import only used chart types
- Monitor bundle with `vite-bundle-visualizer`

### Images & Assets

- Use `loading="lazy"` on below-fold images
- Prefer SVG for icons (via lucide-react, which shadcn/ui uses)
- Use responsive image sizes with `srcSet` for raster images

---

## Accessibility Requirements

### Non-Negotiable Standards

- WCAG 2.1 AA compliance minimum
- Every interactive element must be keyboard accessible
- Every form input must have a visible label (use shadcn/ui `<FormLabel>`)
- Color is never the sole indicator of state — use icons, text, or patterns alongside
- Focus management on route changes and modal open/close
- All images have meaningful `alt` text (or `alt=""` for decorative)
- Minimum touch target: 44x44px for mobile

### Implementation Patterns

- Use semantic HTML: `<main>`, `<nav>`, `<section>`, `<article>`, `<aside>`
- Use shadcn/ui components — they're built on Radix which handles ARIA
- AG Grid has built-in accessibility — ensure `headerName` is set on all columns
- Charts must have a text alternative (data table or `aria-label` with summary)
- Test with `@storybook/addon-a11y` in every story
- Test with keyboard navigation in Playwright E2E tests
- Use `aria-live="polite"` for dynamic content updates (toast notifications, loading states)

### Testing Accessibility

- Storybook: `addon-a11y` runs axe-core on every story automatically
- Vitest: Use `jest-axe` (compatible with Vitest) for component-level a11y assertions:
  ```tsx
  import { axe } from 'jest-axe';
  it('has no accessibility violations', async () => {
    const { container } = render(<UserForm />);
    expect(await axe(container)).toHaveNoViolations();
  });
  ```
- Playwright: Include keyboard-only navigation flows in E2E tests
- CI: Run Storybook accessibility tests in CI pipeline

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
| How do I manage API keys? | Query key factory in `lib/query-keys.ts` |
| How do I handle loading states? | TanStack Query `isLoading`/`isPending` + Suspense boundaries |
| How do I handle errors? | Error boundaries + TanStack Query `isError` + toast notifications |

---

## Anti-Patterns (Never Do These)

1. **Never use `useEffect` for data fetching** — use TanStack Query
2. **Never build a custom table** — use AG Grid
3. **Never use CSS modules or styled-components** — use Tailwind
4. **Never install a second component library** — shadcn/ui is the standard
5. **Never store server state in Zustand** — TanStack Query owns it
6. **Never skip writing a Storybook story** — every component gets one
7. **Never use `any` type** — use `unknown` and narrow
8. **Never use uncontrolled inputs without React Hook Form** — forms always use RHF
9. **Never roll custom validation** — Zod handles all validation logic
10. **Never skip accessibility** — every PR must pass axe-core checks
