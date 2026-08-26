---
name: ReactRouterHooks
description: Steering for React Router v6+ hooks — navigation, typed params with Zod, and data loading with TanStack Query
inclusion: manual
fileMatchPattern: [
  "**/src/**/*.tsx",
  "**/src/**/*.jsx",
  "**/src/**/*.ts",
  "**/src/**/*.js"
]
---

# React Router Hooks Steering

> Hooks for navigation, params, and data loading in React Router v6+. Type-safe params with Zod. Prefetch data in loaders with TanStack Query.

## When to Use

- `useNavigate` — programmatic navigation after async operations (form submit, auth redirect)
- `useParams` — access dynamic route segments (always strings, always validate)
- `useSearchParams` — read/write URL query parameters for filter/sort/pagination state
- `useLocation` — access current pathname, search, hash, state
- `useLoaderData` — consume data prefetched in route loader functions
- `useRouteError` — access thrown errors in `errorElement` boundaries
- `useMatches` — access all matched route data (breadcrumbs, layout decisions)

## Best Practices

- **Always validate params with Zod** — `useParams` returns `string | undefined`, never trust it raw
- **Prefetch in loaders** — use TanStack Query's `queryClient.ensureQueryData()` in route loaders for instant navigation
- **Keep URLs as source of truth** — filters, pagination, sort order belong in `searchParams`, not component state
- **Use `replace: true`** for search param updates that shouldn't create history entries
- **Type loader returns** — use `satisfies` or explicit return types on loaders

## Example Use

### Typed Params with Zod Validation

```tsx
// routes/project-detail.tsx
import { useParams } from 'react-router-dom';
import { z } from 'zod';

const ParamsSchema = z.object({
  projectId: z.string().uuid('Invalid project ID'),
});

export function ProjectDetail() {
  const rawParams = useParams();
  const result = ParamsSchema.safeParse(rawParams);

  if (!result.success) {
    throw new Response('Invalid project ID', { status: 400 });
  }

  const { projectId } = result.data;
  // Use projectId safely — validated UUID
  return <ProjectView projectId={projectId} />;
}
```

### Loader with TanStack Query Prefetch

```tsx
// routes/projects.tsx
import { type LoaderFunctionArgs } from 'react-router-dom';
import { queryClient } from '@/lib/query-client';
import { projectsQueryOptions } from '@/hooks/queries/use-projects';

export async function projectsLoader({ request }: LoaderFunctionArgs) {
  const url = new URL(request.url);
  const page = parseInt(url.searchParams.get('page') ?? '1');

  // Prefetch — returns cached data or fetches fresh
  await queryClient.ensureQueryData(projectsQueryOptions(page));
  return { page };
}

// Component consumes via TanStack Query (already in cache from loader)
export function ProjectsPage() {
  const [searchParams] = useSearchParams();
  const page = parseInt(searchParams.get('page') ?? '1');
  const { data: projects } = useQuery(projectsQueryOptions(page));

  return <ProjectList projects={projects} />;
}
```

### Search Params for Filter State

```tsx
import { useSearchParams } from 'react-router-dom';

export function UserFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const role = searchParams.get('role') ?? 'all';

  function handleRoleChange(newRole: string) {
    setSearchParams((prev) => {
      if (newRole === 'all') {
        prev.delete('role');
      } else {
        prev.set('role', newRole);
      }
      prev.set('page', '1'); // Reset pagination on filter change
      return prev;
    }, { replace: true });
  }

  return (
    <Select value={role} onValueChange={handleRoleChange}>
      {/* options */}
    </Select>
  );
}
```

## Pitfalls

### useParams returns strings — always parse

```tsx
// ❌ Trusting raw params
const { id } = useParams();
const numericId = Number(id); // NaN if "abc" — no error thrown

// ✅ Validate with Zod
const parsed = z.object({ id: z.coerce.number().positive() }).safeParse(useParams());
if (!parsed.success) throw new Response('Not found', { status: 404 });
```

### Stale closures with useNavigate in callbacks

```tsx
// ❌ navigate captured in stale closure
const navigate = useNavigate();
const handler = useCallback(() => {
  // If navigate reference changes, this is stale
  navigate('/somewhere');
}, []); // missing navigate in deps

// ✅ Include navigate in deps (it's stable in React Router v6, but be explicit)
const handler = useCallback(() => {
  navigate('/somewhere');
}, [navigate]);
```

### setSearchParams replaces all params by default

```tsx
// ❌ Wipes all other search params
setSearchParams({ page: '2' });

// ✅ Preserve existing params with functional update
setSearchParams((prev) => {
  prev.set('page', '2');
  return prev;
});
```

## Error Handling

```tsx
// error-boundary.tsx — route errorElement
import { useRouteError, isRouteErrorResponse } from 'react-router-dom';

export function RouteErrorBoundary() {
  const error = useRouteError();

  if (isRouteErrorResponse(error)) {
    return (
      <div>
        <h1>{error.status}</h1>
        <p>{error.statusText}</p>
      </div>
    );
  }

  const message = error instanceof Error ? error.message : 'Unknown error';
  return <div><h1>Error</h1><p>{message}</p></div>;
}
```

- Throw `Response` objects from loaders/components for HTTP-style errors
- Use `isRouteErrorResponse` to distinguish thrown Responses from unexpected errors
- Each route can have its own `errorElement` — nest for granular recovery

## Works With

| Dependency | Integration |
|-----------|-------------|
| **TanStack Query** | `ensureQueryData` in loaders for prefetch; `useQuery` in components for cache |
| **Zod** | Validate `useParams` and `useSearchParams` at the boundary |
| **Zustand** | Persist filter state to URL via `useSearchParams`, not Zustand |

## Anti-Patterns

- ❌ Using `useEffect` + `useState` for data fetching instead of loaders + TanStack Query
- ❌ Storing URL-representable state (filters, pagination) in component state or Zustand
- ❌ Using `useParams` without validation — all values are `string | undefined`
- ❌ Navigating with string concatenation instead of path helpers
- ❌ Using `useNavigate` inside render (call it in event handlers or effects only)
- ❌ Ignoring loader errors — always provide an `errorElement`
