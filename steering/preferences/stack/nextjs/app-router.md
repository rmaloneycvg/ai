---
inclusion: manual
---

# App Router Steering

## Mandate

**Use the App Router exclusively.** The Pages Router (`pages/` directory) is not used in this stack. All routing is file-based under `app/`.

## File-Based Routing

### Core File Conventions

| File | Purpose |
|------|---------|
| `page.tsx` | Route UI — makes a segment publicly accessible |
| `layout.tsx` | Shared UI that wraps child routes, preserves state across navigations |
| `loading.tsx` | Instant loading UI (Suspense boundary) |
| `error.tsx` | Error boundary for the segment |
| `not-found.tsx` | UI for `notFound()` calls |
| `route.ts` | API endpoint (cannot coexist with `page.tsx` in same segment) |
| `template.tsx` | Like layout but re-mounts on navigation (rare — use only when you need fresh state per navigation) |
| `default.tsx` | Fallback for parallel routes when no match |

### Route Segments

```
app/
├── dashboard/           → /dashboard
│   ├── settings/        → /dashboard/settings
│   └── [teamId]/        → /dashboard/:teamId (dynamic)
│       └── [memberId]/  → /dashboard/:teamId/:memberId (nested dynamic)
```

### Dynamic Segments

```typescript
// app/projects/[projectId]/page.tsx
export default async function ProjectPage({
  params,
}: {
  params: Promise<{ projectId: string }>
}) {
  const { projectId } = await params
  const project = await getProject(projectId)
  return <ProjectView project={project} />
}
```

### Catch-All Segments

```
app/docs/[...slug]/page.tsx     → /docs/a, /docs/a/b, /docs/a/b/c
app/docs/[[...slug]]/page.tsx   → /docs, /docs/a, /docs/a/b (optional catch-all)
```

## Layouts

### Rules

1. **Root layout is required** — must include `<html>` and `<body>` tags.
2. **Layouts don't re-render** on navigation between child routes — they preserve state.
3. **Layouts are Server Components by default** — only add `'use client'` if the layout itself needs interactivity.
4. **Layouts cannot access `pathname`** — use a Client Component with `usePathname()` for active nav states.

### Root Layout Pattern

```typescript
// app/layout.tsx
import { Inter } from 'next/font/google'
import { Providers } from '@/components/providers'

const inter = Inter({ subsets: ['latin'] })

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
```

### Nested Layout Pattern

```typescript
// app/(auth)/layout.tsx
import { redirect } from 'next/navigation'
import { getSession } from '@/lib/auth'
import { Sidebar } from '@/components/sidebar'

export default async function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getSession()
  if (!session) redirect('/login')

  return (
    <div className="flex">
      <Sidebar user={session.user} />
      <main className="flex-1">{children}</main>
    </div>
  )
}
```

## Loading States

`loading.tsx` creates an automatic Suspense boundary. The loading UI shows instantly while the page content streams in.

```typescript
// app/dashboard/loading.tsx
import { Skeleton } from '@/components/ui/skeleton'

export default function DashboardLoading() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-64" />
      <Skeleton className="h-96 w-full" />
    </div>
  )
}
```

### Granular Loading with Suspense

For more control than route-level loading, use Suspense directly:

```typescript
// app/dashboard/page.tsx
import { Suspense } from 'react'
import { MetricsCards } from './metrics-cards'
import { RecentActivity } from './recent-activity'
import { Skeleton } from '@/components/ui/skeleton'

export default function DashboardPage() {
  return (
    <div>
      <h1>Dashboard</h1>
      <Suspense fallback={<Skeleton className="h-32" />}>
        <MetricsCards />
      </Suspense>
      <Suspense fallback={<Skeleton className="h-64" />}>
        <RecentActivity />
      </Suspense>
    </div>
  )
}
```

## Error Boundaries

`error.tsx` must be a Client Component. It catches errors in its segment and all child segments.

```typescript
// app/dashboard/error.tsx
'use client'

import { useEffect } from 'react'
import { Button } from '@/components/ui/button'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="flex flex-col items-center gap-4 py-16">
      <h2>Something went wrong</h2>
      <p className="text-muted-foreground">{error.message}</p>
      <Button onClick={reset}>Try again</Button>
    </div>
  )
}
```

### Global Error Boundary

```typescript
// app/global-error.tsx
'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        <h2>Something went wrong</h2>
        <button onClick={reset}>Try again</button>
      </body>
    </html>
  )
}
```

## Route Groups

Organize routes without affecting URL structure using `(folderName)`:

```
app/
├── (marketing)/         # Does NOT appear in URL
│   ├── about/           → /about
│   ├── blog/            → /blog
│   └── layout.tsx       # Marketing-specific layout
├── (app)/               # Does NOT appear in URL
│   ├── dashboard/       → /dashboard
│   ├── settings/        → /settings
│   └── layout.tsx       # App-specific layout (with sidebar, auth)
└── layout.tsx           # Root layout shared by all
```

### Use Cases for Route Groups

1. **Separate layouts** for marketing vs app sections
2. **Organize by feature** without URL pollution
3. **Separate auth concerns** — `(auth)` group requires session, `(public)` group doesn't
4. **Multiple root layouts** — each route group can have its own root layout (opt-in, rarely needed)

## Parallel Routes

Render multiple pages simultaneously in the same layout using named slots (`@slotName`):

```
app/
├── @dashboard/
│   ├── page.tsx
│   └── default.tsx
├── @notifications/
│   ├── page.tsx
│   └── default.tsx
├── layout.tsx
└── page.tsx
```

```typescript
// app/layout.tsx with parallel routes
export default function Layout({
  children,
  dashboard,
  notifications,
}: {
  children: React.ReactNode
  dashboard: React.ReactNode
  notifications: React.ReactNode
}) {
  return (
    <div className="grid grid-cols-3">
      <div className="col-span-2">{dashboard}</div>
      <div>{notifications}</div>
    </div>
  )
}
```

### Conditional Parallel Routes

```typescript
// app/layout.tsx — show different slots based on auth state
import { getSession } from '@/lib/auth'

export default async function Layout({
  children,
  authenticated,
  guest,
}: {
  children: React.ReactNode
  authenticated: React.ReactNode
  guest: React.ReactNode
}) {
  const session = await getSession()
  return session ? authenticated : guest
}
```

### Default Files

**Always provide `default.tsx`** for parallel route slots. Next.js renders `default.tsx` when it can't recover the slot's active state during soft navigation.

```typescript
// app/@notifications/default.tsx
export default function Default() {
  return null
}
```

## Intercepting Routes

Intercept a route to show it in a different context (e.g., modal) while preserving the full-page version for direct navigation/refresh:

```
app/
├── feed/
│   ├── page.tsx
│   └── (..)photo/[id]/   # Intercepts /photo/[id] from /feed
│       └── page.tsx       # Shows as modal
├── photo/[id]/
│   └── page.tsx           # Full page version (direct nav or refresh)
```

### Interception Conventions

| Convention | Matches |
|-----------|---------|
| `(.)` | Same level |
| `(..)` | One level up |
| `(..)(..)` | Two levels up |
| `(...)` | From root |

### Modal Pattern with Intercepting Routes

```typescript
// app/feed/(..)photo/[id]/page.tsx — intercepted version (modal)
import { Modal } from '@/components/ui/modal'
import { PhotoView } from '@/components/photo-view'

export default async function InterceptedPhoto({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return (
    <Modal>
      <PhotoView id={id} />
    </Modal>
  )
}
```

```typescript
// app/photo/[id]/page.tsx — direct navigation version (full page)
import { PhotoView } from '@/components/photo-view'

export default async function PhotoPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  return <PhotoView id={id} />
}
```

## Navigation

### Link Component

```typescript
import Link from 'next/link'

// Prefetches by default in production
<Link href="/dashboard">Dashboard</Link>

// Dynamic route
<Link href={`/projects/${project.id}`}>View Project</Link>

// Disable prefetch for rarely-visited links
<Link href="/settings" prefetch={false}>Settings</Link>
```

### Programmatic Navigation

```typescript
'use client'
import { useRouter } from 'next/navigation'

export function NavigationButton() {
  const router = useRouter()
  return (
    <button onClick={() => router.push('/dashboard')}>
      Go to Dashboard
    </button>
  )
}
```

### Server-Side Redirects

```typescript
import { redirect } from 'next/navigation'

export default async function Page() {
  const session = await getSession()
  if (!session) redirect('/login')
  // ...
}
```

## Metadata

```typescript
// Static metadata
export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Your project dashboard',
}

// Dynamic metadata
export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>
}): Promise<Metadata> {
  const { id } = await params
  const project = await getProject(id)
  return {
    title: project.name,
    description: project.description,
  }
}
```

## Static Generation with Dynamic Routes

```typescript
// app/blog/[slug]/page.tsx
export async function generateStaticParams() {
  const posts = await getAllPosts()
  return posts.map((post) => ({ slug: post.slug }))
}

export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const post = await getPost(slug)
  return <article>{post.content}</article>
}
```
