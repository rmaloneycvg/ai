---
name: NextjsServerComponents
description: Guidelines for choosing between Server and Client Components, when to add 'use client', and composition patterns
inclusion: manual
fileMatchPattern: [
  "**/app/**/*.tsx",
  "**/components/**/*.tsx"
]
---

# Server Components vs Client Components

## Default: Server Components

Every component in the App Router is a **Server Component by default**. Only add `'use client'` when you have a specific reason.

## When to Use Server Components

| Use Case | Why Server |
|----------|-----------|
| Fetching data | Direct database/API access, no client bundle cost |
| Accessing backend resources | Secrets, file system, internal services |
| Rendering static/semi-static content | Zero JS shipped to client |
| SEO-critical content | Fully rendered HTML in initial response |
| Large dependencies | Keep heavy libs (markdown parsers, syntax highlighters) off the client |

## When to Use Client Components (`'use client'`)

| Use Case | Why Client |
|----------|-----------|
| Event handlers (`onClick`, `onChange`, etc.) | Interactivity requires browser |
| useState, useEffect, useRef | React hooks that depend on browser lifecycle |
| Browser APIs | localStorage, geolocation, IntersectionObserver |
| Third-party client libs | AG Grid, Recharts, react-hook-form |
| Real-time updates | WebSocket listeners, polling |
| Zustand stores | Client-side state management |
| TanStack Query hooks | `useQuery`, `useMutation` for client-side data |

## The Boundary Pattern

Push `'use client'` as far down the tree as possible. Don't make a whole page a Client Component — extract the interactive part.

### Wrong: Entire page is client

```typescript
'use client'
import { useState } from 'react'

// This forces everything to be client-rendered
// Can't use async/await, can't directly call server functions
export default function ProjectPage({ params }) {
  // ...
}
```

### Correct: Server page with client islands

```typescript
// app/projects/[id]/page.tsx — Server Component (no directive)
import { getProject } from '@/lib/data'
import { ProjectHeader } from './project-header'
import { ProjectActions } from './project-actions' // Client Component

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const project = await getProject(id)

  return (
    <div>
      <ProjectHeader project={project} />
      <ProjectActions projectId={project.id} />
    </div>
  )
}
```

```typescript
// app/projects/[id]/project-actions.tsx
'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'

export function ProjectActions({ projectId }: { projectId: string }) {
  const [isEditing, setIsEditing] = useState(false)
  return (
    <Button onClick={() => setIsEditing(!isEditing)}>
      {isEditing ? 'Cancel' : 'Edit'}
    </Button>
  )
}
```

## Data Fetching Patterns

### Server Component Fetch (REPLACES TanStack Query for server reads)

```typescript
// app/dashboard/page.tsx — Server Component
async function getMetrics() {
  const res = await fetch('https://api.example.com/metrics', {
    next: { revalidate: 60 }, // ISR: revalidate every 60 seconds
  })
  if (!res.ok) throw new Error('Failed to fetch metrics')
  return res.json()
}

export default async function DashboardPage() {
  const metrics = await getMetrics()
  return <MetricsDisplay data={metrics} />
}
```

### When TanStack Query Is Still Used (Client-Side)

TanStack Query remains the standard for:

1. **Client-side mutations with optimistic updates**
2. **Polling / real-time refetching**
3. **Infinite scroll / pagination controlled by user interaction**
4. **Dependent queries triggered by client state**
5. **Offline support / cache persistence**

```typescript
// components/features/project-members.tsx
'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { addMember, getMembers } from '@/lib/queries/members'

export function ProjectMembers({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient()

  const { data: members } = useQuery({
    queryKey: ['members', projectId],
    queryFn: () => getMembers(projectId),
  })

  const addMemberMutation = useMutation({
    mutationFn: addMember,
    onMutate: async (newMember) => {
      await queryClient.cancelQueries({ queryKey: ['members', projectId] })
      const previous = queryClient.getQueryData(['members', projectId])
      queryClient.setQueryData(['members', projectId], (old: Member[]) => [
        ...old,
        { ...newMember, id: 'temp' },
      ])
      return { previous }
    },
    onError: (_err, _newMember, context) => {
      queryClient.setQueryData(['members', projectId], context?.previous)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['members', projectId] })
    },
  })

  return (/* render members with add functionality */)
}
```

### Hybrid Pattern: Server Fetch + Client Hydration

Pre-fetch on the server, hydrate TanStack Query on the client for subsequent interactions:

```typescript
// app/projects/[id]/page.tsx — Server Component
import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query'
import { getMembers } from '@/lib/queries/members'
import { ProjectMembers } from './project-members'

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const queryClient = new QueryClient()

  await queryClient.prefetchQuery({
    queryKey: ['members', id],
    queryFn: () => getMembers(id),
  })

  return (
    <HydrationBoundary state={dehydrate(queryClient)}>
      <ProjectMembers projectId={id} />
    </HydrationBoundary>
  )
}
```

## Streaming and Suspense

### How Streaming Works

Server Components can stream their output progressively. The shell renders immediately; async components stream in as they resolve.

### Suspense Boundaries for Granular Streaming

```typescript
// app/dashboard/page.tsx
import { Suspense } from 'react'
import { RevenueChart } from './revenue-chart'
import { RecentOrders } from './recent-orders'
import { TopProducts } from './top-products'
import { CardSkeleton, TableSkeleton, ChartSkeleton } from '@/components/ui/skeletons'

export default function DashboardPage() {
  return (
    <div className="grid grid-cols-2 gap-4">
      <Suspense fallback={<ChartSkeleton />}>
        <RevenueChart />
      </Suspense>

      <Suspense fallback={<CardSkeleton count={4} />}>
        <TopProducts />
      </Suspense>

      <div className="col-span-2">
        <Suspense fallback={<TableSkeleton rows={10} />}>
          <RecentOrders />
        </Suspense>
      </div>
    </div>
  )
}
```

### Async Server Components

Each fetches data independently and streams when ready:

```typescript
// app/dashboard/revenue-chart.tsx — Server Component
import { getRevenue } from '@/lib/data'
import { Chart } from '@/components/features/chart' // Client Component (Recharts)

export async function RevenueChart() {
  const revenue = await getRevenue() // Suspense shows fallback until resolved
  return <Chart data={revenue} />
}
```

## Composition Patterns

### Passing Server Components as Children to Client Components

```typescript
// This works — ServerComponent renders on server, result passed as children
<ClientWrapper>
  <ServerComponent />
</ClientWrapper>
```

```typescript
// components/client-wrapper.tsx
'use client'
import { useState } from 'react'

export function ClientWrapper({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(true)
  return isOpen ? <div>{children}</div> : null
}
```

### Sharing Data Between Server Components

Don't pass data through context or props from parent to child server components. Instead, fetch in each component — Next.js automatically deduplicates `fetch` calls with the same URL and options.

```typescript
// Both components call getUser() — only one actual fetch happens
// app/layout.tsx
export default async function Layout({ children }) {
  const user = await getUser() // Fetch #1 (actually executed)
  return <Nav user={user}>{children}</Nav>
}

// app/page.tsx
export default async function Page() {
  const user = await getUser() // Fetch #2 (deduplicated — uses cached result)
  return <Greeting user={user} />
}
```

## Retained Stack Dependencies in Component Context

| Dependency | Component Type | Notes |
|-----------|---------------|-------|
| **AG Grid** | Client Component | Always `'use client'` — requires DOM |
| **shadcn/ui** | Mostly Client | Interactive components need `'use client'`; purely presentational ones can be Server |
| **Zustand** | Client Component | State lives in browser |
| **react-hook-form** | Client Component | Form interactivity requires client |
| **Zod** | Both | Validation in Server Actions (server) and form validation (client) |
| **Recharts/uPlot** | Client Component | SVG/Canvas rendering requires DOM |
| **Storybook** | N/A | Development tool, not rendered in app |

## Anti-Patterns

1. **Don't import server-only code in client components** — use the `server-only` package to enforce boundaries.
2. **Don't serialize non-serializable data** across the server/client boundary (functions, classes, Dates without conversion).
3. **Don't use `'use client'` at the page level** unless the entire page is truly interactive.
4. **Don't fetch data in client components when it could be fetched on the server** and passed as props.
5. **Don't use `useEffect` for initial data fetching** — that's what Server Components are for.
