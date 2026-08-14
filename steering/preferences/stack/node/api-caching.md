---
inclusion: manual
---

# Node.js API Caching Patterns

## Why This Exists

API performance is the primary driver of user-perceived speed. A cache miss on a hot endpoint under load means N concurrent database queries for the same data. This document defines a layered caching strategy so agents apply the right technique at the right layer — preventing both over-caching (stale data) and under-caching (unnecessary database load).

## Caching Layers

```
Client → CDN → nginx (proxy_cache) → App (in-memory) → Redis → Database
```

Apply from left to right — stop at the first layer that satisfies the use case.

## 1. HTTP Cache Headers

```typescript
import { Request, Response, NextFunction } from 'express';

interface CacheOptions {
  ttl: number;
  private?: boolean;
  staleWhileRevalidate?: number;
}

export function httpCache(opts: CacheOptions) {
  return (_req: Request, res: Response, next: NextFunction) => {
    const directives = [
      opts.private ? 'private' : 'public',
      `max-age=${opts.ttl}`,
    ];
    if (opts.staleWhileRevalidate) {
      directives.push(`stale-while-revalidate=${opts.staleWhileRevalidate}`);
    }
    res.set('Cache-Control', directives.join(', '));
    next();
  };
}

// Usage
router.get('/widgets', httpCache({ ttl: 60, staleWhileRevalidate: 300 }), getWidgets);
```

**Use for:** GET endpoints returning public/list data that doesn't vary per-user.

**Don't use for:** Authenticated/personalized responses, data requiring immediate consistency after writes.

## 2. Redis Distributed Cache

```typescript
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

export async function cached<T>(
  key: string,
  ttlSeconds: number,
  fetcher: () => Promise<T>,
): Promise<T> {
  const raw = await redis.get(key);
  if (raw) return JSON.parse(raw);

  const data = await fetcher();
  await redis.set(key, JSON.stringify(data), 'EX', ttlSeconds);
  return data;
}

export async function invalidate(pattern: string): Promise<void> {
  const keys = await redis.keys(pattern);
  if (keys.length > 0) await redis.del(...keys);
}
```

### Cache Key Strategy
```typescript
const key = `widgets:list:${JSON.stringify(sortedFilters)}`;
const key = `widgets:${id}`;
const key = `user:${userId}:preferences`;
```

### Invalidation After Mutation
```typescript
export async function createWidget(data: CreateWidgetDto) {
  const widget = await db.widget.create({ data });
  await invalidate('widgets:list:*');
  return widget;
}
```

## 3. In-Memory Cache (Single Instance)

```typescript
import { LRUCache } from 'lru-cache';

const cache = new LRUCache<string, unknown>({
  max: 500,
  ttl: 1000 * 60 * 5,
  ttlAutopurge: true,
});

export function memCached<T>(key: string, ttlMs: number, fetcher: () => Promise<T>): Promise<T> {
  const hit = cache.get(key) as T | undefined;
  if (hit !== undefined) return Promise.resolve(hit);
  return Promise.resolve(fetcher()).then((data) => {
    cache.set(key, data, { ttl: ttlMs });
    return data;
  });
}
```

**Use for:** Config/feature flags, static reference data, expensive computations.

**Don't use for:** Multi-instance deployments (use Redis), user-specific data (memory bloat).

## 4. Request-Level Deduplication

```typescript
import { AsyncLocalStorage } from 'async_hooks';

const requestStore = new AsyncLocalStorage<Map<string, Promise<unknown>>>();

export function requestCacheMiddleware(req: Request, res: Response, next: NextFunction) {
  requestStore.run(new Map(), next);
}

export function deduped<T>(key: string, fetcher: () => Promise<T>): Promise<T> {
  const store = requestStore.getStore();
  if (!store) return fetcher();
  if (store.has(key)) return store.get(key) as Promise<T>;
  const promise = fetcher();
  store.set(key, promise);
  return promise;
}
```

## 5. Cache Stampede Prevention

```typescript
import { Mutex } from 'async-mutex';

const locks = new Map<string, Mutex>();

export async function cachedWithLock<T>(key: string, ttl: number, fetcher: () => Promise<T>): Promise<T> {
  const hit = await redis.get(key);
  if (hit) return JSON.parse(hit);

  if (!locks.has(key)) locks.set(key, new Mutex());
  return locks.get(key)!.runExclusive(async () => {
    const recheck = await redis.get(key);
    if (recheck) return JSON.parse(recheck);
    const data = await fetcher();
    await redis.set(key, JSON.stringify(data), 'EX', ttl);
    return data;
  });
}
```

## Decision Matrix

| Scenario | Layer | TTL |
|----------|-------|-----|
| Public list endpoint | HTTP headers + nginx proxy_cache | 30-60s |
| User dashboard data | Redis | 30s |
| Product catalog | Redis + HTTP headers | 5min |
| Feature flags | In-memory | 30s |
| Report generation | Redis + lock | 10min |
| Search autocomplete | In-memory LRU | 60s |
| Per-request dedup | Request-level | request lifetime |

## Testing

```typescript
describe('cached()', () => {
  beforeEach(() => redis.flushall());

  it('returns cached result on second call', async () => {
    const fetcher = vi.fn().mockResolvedValue({ id: 1 });
    await cached('test', 60, fetcher);
    await cached('test', 60, fetcher);
    expect(fetcher).toHaveBeenCalledTimes(1);
  });
});
```

## Anti-Patterns

- ❌ Caching POST/PUT/DELETE responses
- ❌ Caching without invalidation strategy
- ❌ Unbounded in-memory cache (OOM risk)
- ❌ Cache keys with timestamps or random values
- ❌ Ignoring `Vary` header for content negotiation
- ❌ TTL longer than data freshness requirement
