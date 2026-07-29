---
name: backend-rest-api-feature
description: Add or modify REST API endpoints for Node.js or C# backends. Covers routing, validation, caching, error handling, and integration tests. NOT for cron jobs (use backend-cron-feature) or frontend components (use react-components).
---

# Backend REST API Feature

## Environment Scope

**write+validate** — Writes route handlers, schemas, tests, and middleware. Runs `npx tsc --noEmit` (Node) or `dotnet build --no-restore` (C#) to validate compilation. Does NOT start the server or run integration tests against live services — instructs user to run those.

## Workflow

1. **Check Existing State** — Does a route for this path/method already exist? Search route files for the proposed endpoint. If it exists, ask user if they want to modify it or if this is a new endpoint.
2. **Gather Context** — Read existing route structure, middleware chain, and error handling patterns in the project. Identify which stack (Node.js or C#) is in use.
3. **Generate Spec** — List: HTTP method + path, request schema (Zod/FluentValidation), response type, caching strategy, files to create/modify. Present as EARS requirements.
4. **Await Approval** — Present the spec. Do NOT write code until user confirms.
5. **Implement** — Create/modify route, handler, schema, and integration test.
6. **Verify** — Run type check (`tsc --noEmit` or `dotnet build`). Expected: <15s. If fails, enter failure loop.
7. **Document** — Update API types/client if frontend consumes this endpoint. Note in PR description.

### Failure Recovery (max 3 retries)

6a. Read compiler error → identify type mismatch, missing import, or schema issue
6b. Fix the specific file
6c. Re-run type check
6d. After 3 failures → show errors to user, ask for guidance

### Rollback

If user cancels mid-implementation:
1. Revert route file to pre-modification state
2. Delete new handler/schema files if created
3. Revert test file additions
4. Confirm with `git diff --stat`

## Node.js API Endpoint

### Route Definition
```typescript
import { Router } from 'express';
import { z } from 'zod';
import { validate } from '@/middleware/validate';
import { cache } from '@/middleware/cache';

const router = Router();

const CreateWidgetSchema = z.object({
  name: z.string().min(1).max(255),
  type: z.enum(['standard', 'premium']),
});

router.get('/widgets', cache({ ttl: 60 }), getWidgets);
router.post('/widgets', validate(CreateWidgetSchema), createWidget);
```

### Handler Pattern
```typescript
export async function getWidgets(req: Request, res: Response, next: NextFunction) {
  try {
    const widgets = await widgetService.findAll(req.query);
    res.json({ data: widgets });
  } catch (error) {
    next(new AppError('Failed to fetch widgets', 500, error));
  }
}
```

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": [{ "field": "name", "message": "Required" }]
  }
}
```

## C# API Endpoint

### Controller Pattern
```csharp
[ApiController]
[Route("api/[controller]")]
public class WidgetsController : ControllerBase
{
    [HttpGet]
    [ResponseCache(Duration = 60)]
    public async Task<ActionResult<IEnumerable<WidgetDto>>> GetAll(
        [FromQuery] WidgetFilterDto filter, CancellationToken ct)
    {
        var widgets = await _widgetService.GetAllAsync(filter, ct);
        return Ok(widgets);
    }

    [HttpPost]
    public async Task<ActionResult<WidgetDto>> Create(
        [FromBody] CreateWidgetDto dto, CancellationToken ct)
    {
        var widget = await _widgetService.CreateAsync(dto, ct);
        return CreatedAtAction(nameof(GetById), new { id = widget.Id }, widget);
    }
}
```

### Validation (FluentValidation)
```csharp
public class CreateWidgetDtoValidator : AbstractValidator<CreateWidgetDto>
{
    public CreateWidgetDtoValidator()
    {
        RuleFor(x => x.Name).NotEmpty().MaximumLength(255);
        RuleFor(x => x.Type).IsInEnum();
    }
}
```

## Caching Strategy

Choose the appropriate caching layer:
- **Response cache** — static or slowly-changing list endpoints
- **Distributed cache (Redis)** — frequently accessed, shared across instances
- **In-memory cache** — single-instance, high-read endpoints

→ See detailed steering for implementation patterns.

## Integration Testing

```typescript
describe('POST /api/widgets', () => {
  it('creates a widget', async () => {
    const res = await request(app)
      .post('/api/widgets')
      .send({ name: 'Test', type: 'standard' })
      .expect(201);
    expect(res.body.data.name).toBe('Test');
  });

  it('validates request body', async () => {
    await request(app)
      .post('/api/widgets')
      .send({})
      .expect(400);
  });
});
```

## Guardrails

- NEVER create an endpoint without request validation (Zod or FluentValidation)
- NEVER skip integration test — every endpoint ships with at least happy-path + validation-error tests
- NEVER return inconsistent error formats — always use the standard error envelope
- NEVER expose internal error details (stack traces, DB errors) in API responses
- NEVER add a GET endpoint without considering caching strategy
- NEVER skip CORS/auth configuration for new endpoints
- NEVER modify existing endpoint contracts without versioning or user approval

## Checklist

- [ ] Route defined with correct HTTP method
- [ ] Request validation schema (Zod or FluentValidation)
- [ ] Response typed (TypeScript interface or C# DTO)
- [ ] Error handling with consistent error format
- [ ] Caching configured for GET endpoints
- [ ] Integration test covering happy path + validation errors + auth
- [ ] Rate limiting considered for public endpoints
- [ ] CORS configured if new origin needed
- [ ] API docs/types updated

## References

- `steering/security/policies.md` — OAuth2, RBAC, input validation, CORS, rate limiting
- `steering/preferences/stack/node/api-caching.md` — Node.js caching patterns (Redis, in-memory, HTTP headers, stampede prevention)
- `steering/preferences/stack/csharp/api-caching.md` — C# caching patterns (IDistributedCache, ResponseCache, output caching)
- `steering/orchestration/local.md` — Tilt service setup, nginx routing, OAuth2/CORS configuration
- `skills/react-components.md` — If building frontend to consume the API
