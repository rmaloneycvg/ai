---
name: NextjsMiddleware
description: Edge middleware patterns for cross-cutting concerns like auth, redirects, and request rewriting in Next.js
inclusion: manual
fileMatchPattern: [
  "**/middleware.ts",
  "**/middleware.js"
]
---

# Middleware

## Overview

Next.js middleware runs at the **edge** before a request is completed. It executes before routing, rendering, or any Server Component logic. Use it for cross-cutting concerns that must run on every (or many) request(s).

**Key constraint**: Middleware runs in the Edge Runtime. No Node.js APIs (no `fs`, no native modules, limited `crypto`). Keep it lean.

## File Location

```
project-root/
├── middleware.ts    ← Single file, runs for all matched routes
├── app/
└── ...
```

## Route Matching

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // Logic here
  return NextResponse.next()
}

// Only run middleware on specific paths
export const config = {
  matcher: [
    // Match all paths except static files and api routes you want to skip
    '/((?!_next/static|_next/image|favicon.ico|api/webhooks).*)',
  ],
}
```

### Matcher Patterns

```typescript
export const config = {
  matcher: [
    '/dashboard/:path*',        // All dashboard routes
    '/api/:path*',              // All API routes
    '/((?!public|_next).*)',    // Everything except /public and /_next
  ],
}
```

## Authentication Checks

### Session Validation

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { verifyToken } from '@/lib/auth/edge' // Edge-compatible auth

const PUBLIC_PATHS = ['/login', '/register', '/forgot-password', '/api/webhooks']
const AUTH_PATHS = ['/login', '/register']

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl
  const token = request.cookies.get('session-token')?.value

  // Allow public paths without auth
  if (PUBLIC_PATHS.some((path) => pathname.startsWith(path))) {
    // If user is authenticated and trying to access login/register, redirect to dashboard
    if (AUTH_PATHS.some((path) => pathname.startsWith(path)) && token) {
      const session = await verifyToken(token)
      if (session) {
        return NextResponse.redirect(new URL('/dashboard', request.url))
      }
    }
    return NextResponse.next()
  }

  // Verify token for protected routes
  if (!token) {
    const loginUrl = new URL('/login', request.url)
    loginUrl.searchParams.set('callbackUrl', pathname)
    return NextResponse.redirect(loginUrl)
  }

  const session = await verifyToken(token)
  if (!session) {
    const response = NextResponse.redirect(new URL('/login', request.url))
    response.cookies.delete('session-token')
    return response
  }

  // Attach user info to headers for downstream use
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-user-id', session.userId)
  requestHeaders.set('x-user-role', session.role)

  return NextResponse.next({
    request: { headers: requestHeaders },
  })
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
```

### Role-Based Access Control

```typescript
// middleware.ts (within the middleware function)
const ROLE_ROUTES: Record<string, string[]> = {
  admin: ['/admin'],
  manager: ['/admin', '/team-management'],
}

// After session verification:
const restrictedPaths = Object.entries(ROLE_ROUTES)
  .filter(([_, paths]) => paths.some((p) => pathname.startsWith(p)))

for (const [requiredRole, paths] of restrictedPaths) {
  if (paths.some((p) => pathname.startsWith(p)) && session.role !== requiredRole) {
    return NextResponse.redirect(new URL('/unauthorized', request.url))
  }
}
```

## OAuth2 Integration at the Middleware Layer

### Token Refresh Flow

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

async function refreshAccessToken(refreshToken: string): Promise<{
  accessToken: string
  refreshToken: string
  expiresAt: number
} | null> {
  try {
    const res = await fetch(`${process.env.OAUTH_ISSUER}/oauth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        refresh_token: refreshToken,
        client_id: process.env.OAUTH_CLIENT_ID!,
        client_secret: process.env.OAUTH_CLIENT_SECRET!,
      }),
    })

    if (!res.ok) return null

    const data = await res.json()
    return {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      expiresAt: Date.now() + data.expires_in * 1000,
    }
  } catch {
    return null
  }
}

export async function middleware(request: NextRequest) {
  const accessToken = request.cookies.get('access-token')?.value
  const refreshToken = request.cookies.get('refresh-token')?.value
  const expiresAt = parseInt(request.cookies.get('token-expires-at')?.value ?? '0')

  // Token is still valid
  if (accessToken && expiresAt > Date.now() + 60_000) {
    return NextResponse.next()
  }

  // Token expired or expiring soon — attempt refresh
  if (refreshToken) {
    const tokens = await refreshAccessToken(refreshToken)

    if (tokens) {
      const response = NextResponse.next()
      response.cookies.set('access-token', tokens.accessToken, {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        path: '/',
      })
      response.cookies.set('refresh-token', tokens.refreshToken, {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        path: '/',
      })
      response.cookies.set('token-expires-at', String(tokens.expiresAt), {
        httpOnly: true,
        secure: true,
        sameSite: 'lax',
        path: '/',
      })
      return response
    }
  }

  // No valid tokens — redirect to login
  const loginUrl = new URL('/login', request.url)
  loginUrl.searchParams.set('callbackUrl', request.nextUrl.pathname)
  return NextResponse.redirect(loginUrl)
}
```

## Redirects

### Path-Based Redirects

```typescript
// middleware.ts
const REDIRECTS: Record<string, string> = {
  '/old-blog': '/blog',
  '/docs/v1': '/docs',
  '/settings/account': '/settings/profile',
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check static redirects
  const redirectTo = REDIRECTS[pathname]
  if (redirectTo) {
    return NextResponse.redirect(new URL(redirectTo, request.url), 308)
  }

  return NextResponse.next()
}
```

### Conditional Redirects

```typescript
// Redirect based on subscription status
export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname.startsWith('/pro-features')) {
    const session = await getEdgeSession(request)
    if (session && !session.isPro) {
      return NextResponse.redirect(new URL('/upgrade', request.url))
    }
  }

  return NextResponse.next()
}
```

## Geolocation

```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const country = request.geo?.country ?? 'US'
  const city = request.geo?.city ?? 'Unknown'
  const region = request.geo?.region ?? 'Unknown'

  // Set headers for downstream use
  const requestHeaders = new Headers(request.headers)
  requestHeaders.set('x-geo-country', country)
  requestHeaders.set('x-geo-city', city)
  requestHeaders.set('x-geo-region', region)

  // Country-based routing
  if (country === 'DE' && !request.nextUrl.pathname.startsWith('/de')) {
    return NextResponse.redirect(new URL(`/de${request.nextUrl.pathname}`, request.url))
  }

  // Block restricted regions
  const BLOCKED_COUNTRIES = ['XX', 'YY'] // Example
  if (BLOCKED_COUNTRIES.includes(country)) {
    return NextResponse.rewrite(new URL('/blocked', request.url))
  }

  return NextResponse.next({
    request: { headers: requestHeaders },
  })
}
```

### Using Geo Data in Server Components

```typescript
// app/page.tsx — Server Component
import { headers } from 'next/headers'

export default async function HomePage() {
  const headersList = await headers()
  const country = headersList.get('x-geo-country') ?? 'US'

  return (
    <div>
      <PricingTable currency={getCurrencyForCountry(country)} />
    </div>
  )
}
```

## A/B Testing

### Cookie-Based Assignment

```typescript
// middleware.ts
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

const EXPERIMENTS = {
  'new-pricing-page': { variants: ['control', 'variant-a', 'variant-b'], weight: [50, 25, 25] },
  'checkout-flow': { variants: ['control', 'streamlined'], weight: [50, 50] },
}

function assignVariant(weights: number[]): number {
  const random = Math.random() * 100
  let cumulative = 0
  for (let i = 0; i < weights.length; i++) {
    cumulative += weights[i]
    if (random < cumulative) return i
  }
  return 0
}

export function middleware(request: NextRequest) {
  const response = NextResponse.next()

  for (const [experiment, config] of Object.entries(EXPERIMENTS)) {
    const cookieName = `exp-${experiment}`
    const existing = request.cookies.get(cookieName)?.value

    if (!existing || !config.variants.includes(existing)) {
      const variantIndex = assignVariant(config.weight)
      const variant = config.variants[variantIndex]

      response.cookies.set(cookieName, variant, {
        httpOnly: false, // Accessible to client analytics
        maxAge: 60 * 60 * 24 * 30, // 30 days
        path: '/',
      })
    }
  }

  return response
}
```

### Using Experiment Variants in Components

```typescript
// app/pricing/page.tsx — Server Component
import { cookies } from 'next/headers'
import { PricingControl } from './pricing-control'
import { PricingVariantA } from './pricing-variant-a'
import { PricingVariantB } from './pricing-variant-b'

export default async function PricingPage() {
  const cookieStore = await cookies()
  const variant = cookieStore.get('exp-new-pricing-page')?.value ?? 'control'

  switch (variant) {
    case 'variant-a':
      return <PricingVariantA />
    case 'variant-b':
      return <PricingVariantB />
    default:
      return <PricingControl />
  }
}
```

### A/B Test with Rewrites (Same URL, Different Content)

```typescript
// middleware.ts — rewrite to different page based on variant
export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  if (pathname === '/checkout') {
    const variant = request.cookies.get('exp-checkout-flow')?.value
    if (variant === 'streamlined') {
      return NextResponse.rewrite(new URL('/checkout-streamlined', request.url))
    }
  }

  return NextResponse.next()
}
```

## Performance Guidelines

1. **Keep middleware fast** — it runs on every matched request. Target < 50ms.
2. **No database calls** — use lightweight token verification (JWT decode, not DB lookup).
3. **Minimize external fetches** — only token refresh endpoints or fast edge KV stores.
4. **Use `matcher`** to limit which routes trigger middleware.
5. **Cache decisions in cookies** — don't recompute A/B assignments on every request.

## Anti-Patterns

1. **Don't fetch application data in middleware** — that's what Server Components are for.
2. **Don't use Node.js-only libraries** — middleware runs in Edge Runtime.
3. **Don't do heavy computation** — it blocks the entire request.
4. **Don't store sensitive data in non-httpOnly cookies** — except experiment variants meant for client analytics.
5. **Don't use middleware for rendering logic** — use it for routing decisions, auth gates, and request enrichment only.
