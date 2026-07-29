# Security Policies

## Why This Exists

Security decisions are scattered across infrastructure (CORS in nginx), application code (auth middleware), and deployment (secrets management). This file consolidates security standards into one authoritative source so agents and developers apply them consistently regardless of which layer they're working in.

## Authentication

### OAuth2 Flow (All Web Applications)

**Why OAuth2:** Eliminates password storage liability, provides standardized token lifecycle, and enables SSO across services without custom auth code.

```
┌─────────┐     ┌─────────────┐     ┌─────────────┐
│  Client  │────▶│  Auth Server │────▶│  Resource    │
│ (Browser)│◀────│  (IdP)       │◀────│  Server      │
└─────────┘     └─────────────┘     └─────────────┘
```

**Required flow:** Authorization Code + PKCE (never implicit grant)

```typescript
// Token storage — HttpOnly cookie, never localStorage
// Why: XSS cannot access HttpOnly cookies. localStorage is readable by any script.
res.cookie('access_token', token, {
  httpOnly: true,
  secure: true,
  sameSite: 'strict',
  maxAge: 15 * 60 * 1000, // 15 minutes
});
```

**Token lifecycle:**
- Access token: 15 minutes max
- Refresh token: 7 days, rotated on each use
- Why short-lived access tokens: limits the blast radius of a leaked token

### Session Management

```typescript
// Why server-side sessions: revocation is immediate (vs. JWT where you wait for expiry)
interface Session {
  userId: string;
  createdAt: Date;
  lastActivity: Date;
  ipAddress: string;
  userAgent: string;
}
```

- Invalidate sessions on password change
- Maximum 5 concurrent sessions per user
- Idle timeout: 30 minutes
- Absolute timeout: 8 hours

## Authorization

### Role-Based Access Control (RBAC)

**Why RBAC over ad-hoc checks:** Centralizes permission logic, makes auditing possible, and prevents permission sprawl where individual endpoints each invent their own access rules.

```typescript
// Middleware pattern
export function requireRole(...roles: Role[]) {
  return (req: Request, res: Response, next: NextFunction) => {
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        error: { code: 'FORBIDDEN', message: 'Insufficient permissions' }
      });
    }
    next();
  };
}

// Usage
router.delete('/users/:id', requireRole('admin'), deleteUser);
router.get('/users', requireRole('admin', 'manager'), listUsers);
```

### Principle of Least Privilege

- Services connect to databases with minimum required permissions (read-only where possible)
- API keys are scoped to specific operations
- Service accounts have no more access than their function requires
- Why: compromised component can only access what it's explicitly granted

## Input Validation

### Defense in Depth

**Why validate at every layer:** Network perimeter defenses fail. A WAF bypass, internal service compromise, or direct API access can all deliver malicious input. Each layer must protect itself.

```
Request → nginx (rate limit) → API (schema validation) → Service (business rules) → DB (constraints)
```

### Validation Rules

```typescript
// Always validate with Zod at the API boundary
// Why Zod: runtime validation + TypeScript type inference from a single schema

const CreateUserSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100).regex(/^[a-zA-Z\s'-]+$/),
  // Why regex: prevents script injection in name fields rendered in HTML/email
});

// Never trust client-provided IDs for authorization
// Why: IDOR (Insecure Direct Object Reference) is a top-10 OWASP vulnerability
router.get('/documents/:id', async (req, res) => {
  const doc = await db.document.findFirst({
    where: { id: req.params.id, ownerId: req.user.id }, // Always filter by owner
  });
});
```

### SQL Injection Prevention

```typescript
// Always use parameterized queries — never string concatenation
// Why: parameterized queries separate code from data at the protocol level

// ✅ Correct
const user = await db.query('SELECT * FROM users WHERE id = $1', [userId]);

// ❌ Never
const user = await db.query(`SELECT * FROM users WHERE id = '${userId}'`);
```

## CORS Configuration

**Why explicit CORS:** Browsers enforce same-origin policy. CORS headers explicitly opt-in to cross-origin access. A misconfigured wildcard (`*`) with credentials allows any site to make authenticated requests on behalf of your users.

```nginx
# nginx CORS config — per-origin, never wildcard with credentials
map $http_origin $cors_origin {
    default "";
    "https://app.example.com" "https://app.example.com";
    "https://staging.example.com" "https://staging.example.com";
    "http://localhost:3000" "http://localhost:3000";
}

add_header Access-Control-Allow-Origin $cors_origin always;
add_header Access-Control-Allow-Credentials "true" always;
add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
add_header Access-Control-Allow-Headers "Authorization, Content-Type" always;
```

## Secrets Management

**Why no secrets in code/config:** Secrets in git history are permanent (rewriting history is unreliable). One leaked `.env` in a public repo exposes production credentials.

| Environment | Secrets Source | Why |
|-------------|---------------|-----|
| Local dev | `.env.local` (gitignored) | Developer convenience, never committed |
| CI/CD | Pipeline secrets (GitHub Actions secrets, etc.) | Encrypted at rest, scoped to pipeline |
| Staging/Prod | Vault / AWS Secrets Manager / Azure Key Vault | Rotation, audit trail, access control |

### Rules

- `.env` files are in `.gitignore` — always
- Secrets are injected as environment variables, never baked into images
- Rotate credentials on any suspected exposure
- Use short-lived credentials where possible (IAM roles > static keys)

## Security Headers

**Why headers:** They instruct the browser to enable protections that are off by default. Each header closes a specific attack vector.

```nginx
# Required on all responses
add_header X-Content-Type-Options "nosniff" always;       # Prevents MIME-type sniffing (XSS via content-type confusion)
add_header X-Frame-Options "DENY" always;                 # Prevents clickjacking
add_header X-XSS-Protection "0" always;                   # Disabled — modern CSP is better, this header causes issues
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

# Content Security Policy — adjust per app
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:;" always;
```

## Rate Limiting

**Why rate limit:** Without it, a single client can exhaust server resources, brute-force credentials, or scrape data. Rate limiting is the cheapest DDoS mitigation.

```nginx
# nginx rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=60r/m;
limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;  # Stricter for auth

location /api/ {
    limit_req zone=api burst=20 nodelay;
}

location /api/auth/ {
    limit_req zone=auth burst=3 nodelay;  # 5 req/min for login attempts
}
```

## Dependency Security

**Why pin versions:** Unpinned dependencies can silently pull in compromised versions. Supply-chain attacks (event-stream, ua-parser-js, colors) prove this isn't theoretical.

- Pin exact versions in package.json / pyproject.toml (no `^` or `~`)
- Run `npm audit` / `pip audit` in CI — fail the build on high/critical
- Review new dependencies before adding: check maintainers, download stats, last publish date
- Prefer well-known packages over obscure alternatives

## Container Security

**Why non-root containers:** If a container is compromised, the attacker gets whatever permissions the container process has. Root in a container = root on the host (without additional hardening).

```dockerfile
# Always run as non-root
FROM node:20-slim AS production
RUN addgroup --system app && adduser --system --ingroup app app
USER app
WORKDIR /app
COPY --chown=app:app . .
```

- Use minimal base images (slim/alpine/distroless)
- No secrets in Dockerfile or image layers
- Scan images for vulnerabilities in CI (`trivy`, `grype`)
- Set read-only filesystem where possible

## Anti-Patterns

- ❌ Storing tokens in localStorage (XSS accessible)
- ❌ Using `*` for CORS origin with credentials
- ❌ String-concatenating user input into queries
- ❌ Trusting client-provided user IDs for authorization decisions
- ❌ Committing `.env` files or hardcoding secrets
- ❌ Running containers as root
- ❌ Disabling security headers "because they break things"
- ❌ Rate limiting only at the application level (nginx is cheaper/faster)
- ❌ Using implicit OAuth grant flow
- ❌ Long-lived access tokens without refresh rotation
