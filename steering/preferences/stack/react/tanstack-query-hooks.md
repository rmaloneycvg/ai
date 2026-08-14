---
inclusion: manual
---

# TanStack Query Hooks Steering

> All server state lives in TanStack Query. Never duplicate it into Zustand or useState. Hooks are the interface; query key factories are the backbone.

## When to Use

- `useQuery` — fetch and cache server data, re-render on updates
- `useMutation` — create/update/delete operations with optimistic UI
- `useInfiniteQuery` — paginated or cursor-based infinite scroll
- `useQueryClient` — imperative cache access (invalidation, prefetch, optimistic set)
- `useSuspenseQuery` — fetch with React Suspense (component suspends until data resolves)

## Best Practices

### Hierarchical Query Keys with Factories

```typescript
// lib/query-keys.ts
export const queryKeys = {
  projects: {
    all: ['projects'] as const,
    lists: () => [...queryKeys.projects.all, 'list'] as const,
    list: (filters: ProjectFilters) => [...queryKeys.projects.lists(), filters] as const,
    details: () => [...queryKeys.projects.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.projects.details(), id] as const,
  },
  members: {
    all: ['members'] as const,
    byProject: (projectId: string) => [...queryKeys.members.all, projectId] as const,
  },
} as const;
```

### Query Options Pattern (Reusable + Loader-Friendly)

```typescript
// hooks/queries/use-projects.ts
import { queryOptions } from '@tanstack/react-query';
import { z } from 'zod';
import { queryKeys } from '@/lib/query-keys';

const ProjectSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  status: z.enum(['active', 'archived']),
});

export function projectsQueryOptions(page: number) {
  return queryOptions({
    queryKey: queryKeys.projects.list({ page }),
    queryFn: async () => {
      const res = await fetch(`/api/projects?page=${page}`);
      if (!res.ok) throw new Error('Failed to fetch projects');
      return z.array(ProjectSchema).parse(await res.json()); // Runtime validation
    },
    staleTime: 5 * 60 * 1000,
  });
}
```

### Defaults (query-client.ts)

```typescript
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 min — don't refetch fresh data
      gcTime: 10 * 60 * 1000,    // 10 min — keep inactive cache
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
```

## Example Use

### Optimistic Mutation (Cancel → Snapshot → Set → Rollback → Invalidate)

```tsx
// hooks/mutations/use-delete-project.ts
export function useDeleteProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (projectId: string) => {
      const res = await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('Delete failed');
    },
    onMutate: async (projectId) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.projects.lists() });
      const previous = queryClient.getQueryData(queryKeys.projects.lists());
      queryClient.setQueriesData(
        { queryKey: queryKeys.projects.lists() },
        (old: Project[] | undefined) => old?.filter((p) => p.id !== projectId),
      );
      return { previous };
    },
    onError: (_err, _projectId, context) => {
      if (context?.previous) {
        queryClient.setQueriesData({ queryKey: queryKeys.projects.lists() }, context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    },
  });
}
```

### useSuspenseQuery with Error Boundary

```tsx
// Component suspends until data resolves — no isLoading check needed
export function ProjectDetail({ projectId }: { projectId: string }) {
  const { data: project } = useSuspenseQuery(projectDetailQueryOptions(projectId));
  return <h1>{project.name}</h1>;
}

// Parent provides Suspense + ErrorBoundary
function ProjectPage({ projectId }: { projectId: string }) {
  return (
    <ErrorBoundary fallback={<p>Failed to load project</p>}>
      <Suspense fallback={<Skeleton className="h-64" />}>
        <ProjectDetail projectId={projectId} />
      </Suspense>
    </ErrorBoundary>
  );
}
```

### Mutation with React Hook Form

Connect `useMutation` to form `onSubmit` — RHF handles validation UX, TQ handles the server call and cache invalidation:

```tsx
const mutation = useMutation({
  mutationFn: createProject,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.projects.all });
    form.reset();
  },
});

// In JSX:
<form onSubmit={form.handleSubmit((data) => mutation.mutate(data))}>
  <Button disabled={mutation.isPending}>
    {mutation.isPending ? 'Creating...' : 'Create'}
  </Button>
  {mutation.isError && <p className="text-destructive">{mutation.error.message}</p>}
</form>
```

## Pitfalls

- **Not invalidating after mutations** — stale list data persists until `staleTime` expires
- **`staleTime: 0` globally** — causes refetch on every mount, defeats caching purpose
- **Missing error boundaries with `useSuspenseQuery`** — unhandled errors crash the app
- **Putting query data into Zustand** — duplicates cache, creates sync bugs
- **Dynamic query keys without stable references** — object/array in queryKey must be deterministic (no `new Date()`)
- **Forgetting `enabled: false`** — queries with undefined params fire with `undefined`, causing 400s

## Error Handling

| Pattern | When |
|---------|------|
| `useQuery` + `isError` / `error` | Inline error UI next to the component |
| `useSuspenseQuery` + `ErrorBoundary` | Declarative error boundaries, cleaner component code |
| `useMutation` + `onError` callback | Toast notifications, form error display |
| Global `QueryCache` `onError` | Logging, generic error toasts for unhandled cases |

```typescript
// Global error handler — only toast for background refetch failures
export const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      if (query.state.data !== undefined) {
        toast.error(`Something went wrong: ${error.message}`);
      }
    },
  }),
});
```

## Works With

| Dependency | Integration |
|-----------|-------------|
| **Zod** | Validate API responses in `queryFn` with `.parse()` |
| **React Hook Form** | `useMutation` in form `onSubmit`; invalidate queries on success |
| **React Router** | `ensureQueryData` / `prefetchQuery` in route loaders |
| **Zustand** | Zustand for client state, TQ for server state — never overlap |
| **Server Actions (Next.js)** | Call server actions inside `mutationFn` for Next.js apps |

## Anti-Patterns

- ❌ `useEffect` + `useState` for data fetching — use `useQuery`
- ❌ Storing fetched data in Zustand — TanStack Query is the cache
- ❌ Manual `refetch()` instead of `invalidateQueries` after mutations
- ❌ Query keys as flat strings — use hierarchical arrays with factories
- ❌ `staleTime: Infinity` without explicit invalidation strategy
- ❌ Calling `queryClient.setQueryData` without also invalidating (stale overwrite)
