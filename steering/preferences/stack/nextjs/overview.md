# Next.js Stack Overview

## Base Stack Inheritance

This stack inherits the full React dependency graph defined in `../react/dependency-graph.md`. All dependencies from that graph are available unless explicitly replaced by a Next.js native feature below.

## What Next.js REPLACES

| Concern | React Stack Solution | Next.js Native Replacement |
|---------|---------------------|---------------------------|
| Routing | react-router / manual | App Router (file-based routing) |
| Server-side data fetching | TanStack Query everywhere | `fetch()` in Server Components with caching/revalidation |
| Static site generation | External build tooling | ISR + `generateStaticParams` |
| API layer | Express / standalone server | Route Handlers (`app/api/`) + Server Actions |
| Code splitting | Manual `React.lazy()` | Automatic per-route splitting |
| Image optimization | Manual / third-party | `next/image` |
| Font optimization | Manual loading | `next/font` |
| Metadata / SEO | react-helmet / manual | Metadata API (`generateMetadata`) |
| Environment variables | dotenv + manual config | Built-in `.env` handling with `NEXT_PUBLIC_` prefix |
| Middleware / edge logic | Express middleware | `middleware.ts` at edge |
| Bundling / compilation | Vite / webpack manual | Turbopack (built-in) |

## What Next.js KEEPS from the React Dependency Graph

| Dependency | Why It's Kept |
|-----------|---------------|
| **AG Grid** | Complex data grids — no Next.js equivalent |
| **TanStack Query** | Client-side mutations, optimistic updates, cache invalidation on the client. Server-side fetching is replaced by RSC `fetch()`, but TQ remains essential for interactive client patterns |
| **Vitest** | Unit/integration testing — Next.js has no test runner |
| **Playwright** | E2E testing — no replacement |
| **shadcn/ui** | Component library — Next.js has no UI components |
| **Zustand** | Client-side state management — Next.js has no state management solution |
| **react-hook-form** | Form handling on client components — Server Actions handle submission but RHF handles validation UX |
| **Zod** | Schema validation — used in Server Actions, route handlers, and client forms |
| **Recharts / uPlot** | Charting — no Next.js equivalent |
| **Storybook** | Component development/documentation — no replacement |
| **TypeScript** | Type safety — Next.js has first-class TS support but doesn't replace it |

## Key Principles

1. **Server-first**: Default to Server Components. Only add `'use client'` when you need interactivity, browser APIs, or client-side state.
2. **Use the platform**: If Next.js provides a native way to do something, use it. Don't add libraries that duplicate built-in functionality.
3. **Colocate data fetching**: Fetch data where it's used (in the component that needs it), not at the top of a route and prop-drilled down.
4. **Progressive enhancement**: Server Actions work without JavaScript. Forms should function before client hydration.
5. **Edge-aware**: Middleware runs at the edge. Keep it lean — no heavy dependencies, no database calls from middleware.

## File Structure Convention

```
app/
├── (auth)/              # Route group for authenticated pages
│   ├── dashboard/
│   │   ├── page.tsx
│   │   ├── loading.tsx
│   │   └── error.tsx
│   └── layout.tsx
├── (public)/            # Route group for public pages
│   ├── login/
│   │   └── page.tsx
│   └── layout.tsx
├── api/                 # Route handlers
│   └── [resource]/
│       └── route.ts
├── layout.tsx           # Root layout
├── not-found.tsx
└── global-error.tsx
middleware.ts            # Edge middleware
lib/
├── actions/             # Server Actions
├── queries/             # TanStack Query hooks (client-side)
├── validators/          # Zod schemas
└── stores/              # Zustand stores
components/
├── ui/                  # shadcn components
└── features/            # Feature-specific components
```

## Decision Framework

When implementing a feature, ask:

1. Can this be done entirely on the server? → Server Component + `fetch()`
2. Does it need interactivity? → Client Component + TanStack Query (for async) or Zustand (for sync state)
3. Does it need a form? → Server Action for submission + react-hook-form for client validation UX
4. Does it need an API endpoint? → Route Handler in `app/api/`
5. Does it need auth checking before render? → Middleware
6. Does it need SEO? → `generateMetadata` + Server Component
