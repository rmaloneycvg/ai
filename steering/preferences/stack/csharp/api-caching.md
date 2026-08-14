---
inclusion: manual
---

# C# API Caching Patterns

## Why This Exists

.NET provides multiple caching abstractions at different layers (response caching, output caching, IMemoryCache, IDistributedCache). Without clear guidance, developers mix approaches inconsistently or default to no caching at all. This document defines when to use each layer and why, ensuring consistent cache behavior across all C# services.

## Caching Layers

```
Client → CDN → nginx/Kestrel (response cache) → App (IMemoryCache) → IDistributedCache (Redis) → Database
```

## 1. Response Caching (HTTP Layer)

### Attribute-Based
```csharp
[HttpGet]
[ResponseCache(Duration = 60, VaryByQueryKeys = new[] { "page", "pageSize" })]
public async Task<ActionResult<IEnumerable<WidgetDto>>> GetAll(
    [FromQuery] int page = 1, [FromQuery] int pageSize = 20)
{
    var widgets = await _widgetService.GetAllAsync(page, pageSize);
    return Ok(widgets);
}
```

### Profile-Based (reusable)
```csharp
// Program.cs
builder.Services.AddResponseCaching();
builder.Services.Configure<MvcOptions>(options =>
{
    options.CacheProfiles.Add("Default60", new CacheProfile
    {
        Duration = 60,
        Location = ResponseCacheLocation.Any,
    });
    options.CacheProfiles.Add("Private30", new CacheProfile
    {
        Duration = 30,
        Location = ResponseCacheLocation.Client,
    });
});

// Controller
[ResponseCache(CacheProfileName = "Default60")]
public async Task<ActionResult<WidgetDto>> GetById(Guid id) { ... }
```

## 2. Output Caching (.NET 7+)

More powerful than response caching — supports tag-based invalidation.

```csharp
// Program.cs
builder.Services.AddOutputCache(options =>
{
    options.AddBasePolicy(b => b.NoCache());
    options.AddPolicy("CachePublic60", b => b
        .Expire(TimeSpan.FromSeconds(60))
        .Tag("widgets"));
});
app.UseOutputCache();

// Controller
[HttpGet]
[OutputCache(PolicyName = "CachePublic60")]
public async Task<ActionResult<IEnumerable<WidgetDto>>> GetAll() { ... }

// Invalidation after mutation
[HttpPost]
public async Task<ActionResult<WidgetDto>> Create(
    CreateWidgetDto dto, IOutputCacheStore cacheStore, CancellationToken ct)
{
    var widget = await _widgetService.CreateAsync(dto, ct);
    await cacheStore.EvictByTagAsync("widgets", ct);
    return CreatedAtAction(nameof(GetById), new { id = widget.Id }, widget);
}
```

## 3. IDistributedCache (Redis)

```csharp
// Program.cs
builder.Services.AddStackExchangeRedisCache(options =>
{
    options.Configuration = builder.Configuration.GetConnectionString("Redis");
    options.InstanceName = "app:";
});

// Service
public class WidgetService
{
    private readonly IDistributedCache _cache;
    private readonly IWidgetRepository _repo;

    public async Task<WidgetDto?> GetByIdAsync(Guid id, CancellationToken ct)
    {
        var key = $"widget:{id}";
        var cached = await _cache.GetStringAsync(key, ct);
        if (cached is not null)
            return JsonSerializer.Deserialize<WidgetDto>(cached);

        var widget = await _repo.GetByIdAsync(id, ct);
        if (widget is null) return null;

        var dto = widget.ToDto();
        await _cache.SetStringAsync(key, JsonSerializer.Serialize(dto),
            new DistributedCacheEntryOptions { AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5) },
            ct);
        return dto;
    }

    public async Task InvalidateAsync(Guid id, CancellationToken ct)
    {
        await _cache.RemoveAsync($"widget:{id}", ct);
    }
}
```

### Generic Cache Helper
```csharp
public static class CacheExtensions
{
    public static async Task<T> GetOrSetAsync<T>(
        this IDistributedCache cache,
        string key,
        TimeSpan ttl,
        Func<CancellationToken, Task<T>> factory,
        CancellationToken ct = default) where T : class
    {
        var cached = await cache.GetStringAsync(key, ct);
        if (cached is not null)
            return JsonSerializer.Deserialize<T>(cached)!;

        var data = await factory(ct);
        await cache.SetStringAsync(key, JsonSerializer.Serialize(data),
            new DistributedCacheEntryOptions { AbsoluteExpirationRelativeToNow = ttl }, ct);
        return data;
    }
}

// Usage
var widgets = await _cache.GetOrSetAsync(
    "widgets:all",
    TimeSpan.FromMinutes(5),
    async ct => await _repo.GetAllAsync(ct),
    cancellationToken);
```

## 4. IMemoryCache (In-Process)

```csharp
builder.Services.AddMemoryCache();

public class ConfigService
{
    private readonly IMemoryCache _cache;

    public async Task<AppConfig> GetConfigAsync()
    {
        return await _cache.GetOrCreateAsync("config", async entry =>
        {
            entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromSeconds(30);
            return await _configRepo.GetLatestAsync();
        });
    }
}
```

**Use for:** Feature flags, config, static reference data.

**Don't use for:** Multi-instance deployments, user-specific data.

## 5. Cache Stampede Prevention (SemaphoreSlim)

```csharp
private static readonly ConcurrentDictionary<string, SemaphoreSlim> _locks = new();

public async Task<T> GetOrSetWithLockAsync<T>(string key, TimeSpan ttl,
    Func<CancellationToken, Task<T>> factory, CancellationToken ct) where T : class
{
    var cached = await _cache.GetStringAsync(key, ct);
    if (cached is not null) return JsonSerializer.Deserialize<T>(cached)!;

    var semaphore = _locks.GetOrAdd(key, _ => new SemaphoreSlim(1, 1));
    await semaphore.WaitAsync(ct);
    try
    {
        cached = await _cache.GetStringAsync(key, ct);
        if (cached is not null) return JsonSerializer.Deserialize<T>(cached)!;

        var data = await factory(ct);
        await _cache.SetStringAsync(key, JsonSerializer.Serialize(data),
            new DistributedCacheEntryOptions { AbsoluteExpirationRelativeToNow = ttl }, ct);
        return data;
    }
    finally { semaphore.Release(); }
}
```

## Decision Matrix

| Scenario | Layer | TTL |
|----------|-------|-----|
| Public list endpoints | Output Cache + tag invalidation | 60s |
| Single resource GET | IDistributedCache (Redis) | 5min |
| Dashboard aggregation | Redis + lock | 30s |
| Feature flags / config | IMemoryCache | 30s |
| Static reference data | IMemoryCache | 10min |
| Heavy report | Redis + SemaphoreSlim | 10min |

## Anti-Patterns

- ❌ Using `IMemoryCache` in multi-instance deployments without awareness of inconsistency
- ❌ Not passing `CancellationToken` through cache operations
- ❌ Caching null results without short TTL (negative cache stampede)
- ❌ Missing invalidation on mutations (stale reads)
- ❌ Serializing EF entities directly (lazy loading / proxy issues)
- ❌ Cache keys without namespace prefix (collisions across services)
