# Data Patterns

## Overview: What Next.js Replaces

| Pattern | Before (React SPA) | After (Next.js) |
|---------|-------------------|-----------------|
| Initial page data | TanStack Query in useEffect | Server Component `fetch()` |
| Static pages | Build-time generation only | ISR — static + revalidation |
| API endpoints | Express routes | Route Handlers (`app/api/`) |
| Form submissions | Client-side fetch + mutation | Server Actions |
| Cache invalidation | TanStack Query `invalidateQueries` | `revalidatePath` / `revalidateTag` + TQ for client cache |

**TanStack Query is still used** for client-side concerns: mutations with optimistic UI, polling, infinite scroll, and any data that changes based on client interaction without navigation.

## Incremental Static Regeneration (ISR)

ISR generates static pages at build time and regenerates them in the background after a specified interval.

### Time-Based Revalidation

```typescript
// app/blog/[slug]/page.tsx
async function getPost(slug: string) {
  const res = await fetch(`https://cms.example.com/posts/${slug}`, {
    next: { revalidate: 3600 }, // Revalidate every hour
  })
  return res.json()
}

export default async function BlogPost({
  params,
}: {
  params: Promise<{ slug: string }>
}) {
  const { slug } = await params
  const post = await getPost(slug)
  return <Article post={post} />
}
```

### Segment-Level Revalidation Config

```typescript
// app/blog/[slug]/page.tsx
export const revalidate = 3600 // Revalidate this entire route every hour

export default async function BlogPost({ params }) {
  // All fetches in this page inherit the 3600s revalidation
  // unless they specify their own
}
```

### Static vs Dynamic

```typescript
// Force static generation (default for pages with no dynamic data)
export const dynamic = 'force-static'

// Force dynamic rendering (SSR on every request)
export const dynamic = 'force-dynamic'

// Auto (default) — Next.js decides based on whether dynamic functions are used
export const dynamic = 'auto'
```

## Revalidation Strategies

### On-Demand Revalidation by Path

```typescript
// app/api/revalidate/route.ts
import { revalidatePath } from 'next/cache'
import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  const { path, secret } = await request.json()

  if (secret !== process.env.REVALIDATION_SECRET) {
    return NextResponse.json({ error: 'Invalid secret' }, { status: 401 })
  }

  revalidatePath(path)
  return NextResponse.json({ revalidated: true })
}
```

### On-Demand Revalidation by Tag

```typescript
// Fetch with a tag
async function getProducts() {
  const res = await fetch('https://api.example.com/products', {
    next: { tags: ['products'] },
  })
  return res.json()
}

// Revalidate all fetches with the 'products' tag
import { revalidateTag } from 'next/cache'

export async function updateProduct(formData: FormData) {
  'use server'
  await db.products.update(/* ... */)
  revalidateTag('products')
}
```

### Tag Strategy Patterns

```typescript
// Granular tags for targeted invalidation
await fetch(`/api/projects/${id}`, {
  next: { tags: ['projects', `project-${id}`] },
})

// Invalidate one project
revalidateTag(`project-${id}`)

// Invalidate all projects
revalidateTag('projects')
```

## Server Actions

Server Actions are async functions that run on the server, callable from Client Components. They REPLACE custom API routes for mutations.

### Defining Server Actions

```typescript
// lib/actions/projects.ts
'use server'

import { z } from 'zod'
import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'

const CreateProjectSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
})

export async function createProject(formData: FormData) {
  const parsed = CreateProjectSchema.safeParse({
    name: formData.get('name'),
    description: formData.get('description'),
  })

  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors }
  }

  const project = await db.projects.create({ data: parsed.data })
  revalidatePath('/projects')
  redirect(`/projects/${project.id}`)
}
```

### Using Server Actions in Forms

```typescript
// Progressive enhancement — works without JS
import { createProject } from '@/lib/actions/projects'

export default function NewProjectPage() {
  return (
    <form action={createProject}>
      <input name="name" required />
      <textarea name="description" />
      <button type="submit">Create Project</button>
    </form>
  )
}
```

### Server Actions with Client Validation (react-hook-form + zod)

```typescript
// components/features/create-project-form.tsx
'use client'

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useTransition } from 'react'
import { createProject } from '@/lib/actions/projects'

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().max(500).optional(),
})

type FormData = z.infer<typeof schema>

export function CreateProjectForm() {
  const [isPending, startTransition] = useTransition()
  const { register, handleSubmit, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  })

  const onSubmit = (data: FormData) => {
    const formData = new FormData()
    formData.set('name', data.name)
    if (data.description) formData.set('description', data.description)

    startTransition(() => {
      createProject(formData)
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('name')} />
      {errors.name && <span>{errors.name.message}</span>}
      <textarea {...register('description')} />
      <button type="submit" disabled={isPending}>
        {isPending ? 'Creating...' : 'Create Project'}
      </button>
    </form>
  )
}
```

### Server Actions + TanStack Query (Optimistic Updates)

When you need optimistic UI alongside server mutations:

```typescript
'use client'

import { useMutation, useQueryClient } from '@tanstack/react-query'
import { deleteProject } from '@/lib/actions/projects'

export function DeleteProjectButton({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: async () => {
      const formData = new FormData()
      formData.set('id', projectId)
      return deleteProject(formData)
    },
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: ['projects'] })
      const previous = queryClient.getQueryData(['projects'])
      queryClient.setQueryData(['projects'], (old: Project[]) =>
        old.filter((p) => p.id !== projectId)
      )
      return { previous }
    },
    onError: (_err, _vars, context) => {
      queryClient.setQueryData(['projects'], context?.previous)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  return (
    <button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
      Delete
    </button>
  )
}
```

## Route Handlers

Route Handlers are for when you need a traditional API endpoint (webhooks, third-party integrations, non-form mutations from external clients). Prefer Server Actions for app-internal mutations.

### Basic Route Handler

```typescript
// app/api/projects/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { z } from 'zod'
import { getSession } from '@/lib/auth'

export async function GET(request: NextRequest) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const { searchParams } = new URL(request.url)
  const page = parseInt(searchParams.get('page') ?? '1')
  const limit = parseInt(searchParams.get('limit') ?? '20')

  const projects = await db.projects.findMany({
    where: { userId: session.user.id },
    skip: (page - 1) * limit,
    take: limit,
  })

  return NextResponse.json({ data: projects, page, limit })
}

const CreateProjectBody = z.object({
  name: z.string().min(1),
  description: z.string().optional(),
})

export async function POST(request: NextRequest) {
  const session = await getSession()
  if (!session) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const body = await request.json()
  const parsed = CreateProjectBody.safeParse(body)

  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.flatten().fieldErrors },
      { status: 400 }
    )
  }

  const project = await db.projects.create({
    data: { ...parsed.data, userId: session.user.id },
  })

  return NextResponse.json(project, { status: 201 })
}
```

### Dynamic Route Handlers

```typescript
// app/api/projects/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  const project = await db.projects.findUnique({ where: { id } })

  if (!project) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 })
  }

  return NextResponse.json(project)
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params
  await db.projects.delete({ where: { id } })
  return new NextResponse(null, { status: 204 })
}
```

### Webhook Route Handler

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { headers } from 'next/headers'
import Stripe from 'stripe'

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!)

export async function POST(request: NextRequest) {
  const body = await request.text()
  const headersList = await headers()
  const signature = headersList.get('stripe-signature')!

  let event: Stripe.Event
  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    )
  } catch (err) {
    return NextResponse.json({ error: 'Invalid signature' }, { status: 400 })
  }

  switch (event.type) {
    case 'checkout.session.completed':
      await handleCheckoutComplete(event.data.object)
      break
    // ... other event types
  }

  return NextResponse.json({ received: true })
}
```

### Route Handler Caching

```typescript
// GET route handlers are cached by default (like pages)
// Force dynamic if you need fresh data every request:
export const dynamic = 'force-dynamic'

// Or use time-based revalidation:
export const revalidate = 60
```

## Decision Matrix: Server Action vs Route Handler vs TanStack Query

| Scenario | Solution |
|----------|----------|
| Form submission from your app | Server Action |
| Mutation needing optimistic UI | Server Action + TanStack Query `useMutation` |
| External webhook receiver | Route Handler |
| Third-party API integration | Route Handler |
| Client-side polling/real-time data | TanStack Query `useQuery` with `refetchInterval` |
| Infinite scroll | TanStack Query `useInfiniteQuery` |
| Initial page data load | Server Component `fetch()` |
| Data depending on client state (filters, search) | TanStack Query `useQuery` with dynamic queryKey |
| Static content with periodic refresh | ISR (`next: { revalidate: N }`) |
