# Preferred Technology Stack

**Last Updated:** YYYY-MM-DD
**Maintained By:** [Tech Lead / Architecture Team]
**Purpose:** Default stack preference for new projects. Input to `sdlc-design-architecture` gap analysis.

---

## Frontend

| Layer | Preferred | Version | Rationale |
|-------|-----------|---------|-----------|
| Framework | <!-- e.g., React, Vue, Angular, Svelte --> | | |
| Meta-framework | <!-- e.g., Next.js, Nuxt, SvelteKit, Remix --> | | |
| State Management | <!-- e.g., Zustand, Redux, Pinia --> | | |
| Server State | <!-- e.g., TanStack Query, SWR, Apollo --> | | |
| Component Library | <!-- e.g., shadcn/ui, Radix, MUI --> | | |
| Styling | <!-- e.g., Tailwind CSS, CSS Modules, styled-components --> | | |
| Forms | <!-- e.g., React Hook Form + Zod, Formik --> | | |
| Data Grid | <!-- e.g., AG Grid, TanStack Table --> | | |
| Charts | <!-- e.g., Recharts, D3, uPlot --> | | |
| Testing (Unit) | <!-- e.g., Vitest, Jest --> | | |
| Testing (E2E) | <!-- e.g., Playwright, Cypress --> | | |
| Testing (Visual) | <!-- e.g., Storybook, Chromatic --> | | |

## Backend

| Layer | Preferred | Version | Rationale |
|-------|-----------|---------|-----------|
| Language | <!-- e.g., TypeScript/Node, Python, Go, C#, Java --> | | |
| Framework | <!-- e.g., Express, Fastify, FastAPI, ASP.NET, Spring --> | | |
| API Style | <!-- e.g., REST, GraphQL, gRPC, tRPC --> | | |
| Validation | <!-- e.g., Zod, Joi, Pydantic, FluentValidation --> | | |
| ORM / Data Access | <!-- e.g., Prisma, Drizzle, SQLAlchemy, EF Core --> | | |
| Job Queue | <!-- e.g., BullMQ, Celery, Hangfire --> | | |
| Real-time | <!-- e.g., WebSocket (native), Socket.io, SSE --> | | |

## Database & Storage

| Layer | Preferred | Version | Rationale |
|-------|-----------|---------|-----------|
| Primary DB | <!-- e.g., PostgreSQL, MySQL, SQL Server --> | | |
| Document Store | <!-- e.g., MongoDB, DynamoDB, CosmosDB --> | | |
| Cache | <!-- e.g., Redis, Memcached, Valkey --> | | |
| Search | <!-- e.g., Elasticsearch, OpenSearch, Meilisearch, Typesense --> | | |
| Object Storage | <!-- e.g., S3, GCS, Azure Blob --> | | |
| Message Queue | <!-- e.g., RabbitMQ, Kafka, SQS, NATS --> | | |

## Authentication & Security

| Layer | Preferred | Version | Rationale |
|-------|-----------|---------|-----------|
| Auth Provider | <!-- e.g., Auth0, Clerk, Keycloak, AWS Cognito, custom --> | | |
| Auth Protocol | <!-- e.g., OAuth2 + PKCE, SAML, OIDC --> | | |
| Secrets Management | <!-- e.g., Vault, AWS Secrets Manager, Azure Key Vault --> | | |
| WAF / DDoS | <!-- e.g., Cloudflare, AWS WAF, Azure Front Door --> | | |

## Infrastructure & DevOps

| Layer | Preferred | Version | Rationale |
|-------|-----------|---------|-----------|
| Cloud Provider | <!-- e.g., AWS, GCP, Azure --> | | |
| Container Runtime | <!-- e.g., Docker --> | | |
| Orchestration | <!-- e.g., Kubernetes, ECS, Cloud Run --> | | |
| IaC | <!-- e.g., Terraform, Pulumi, CDK, Bicep --> | | |
| CI/CD | <!-- e.g., GitHub Actions, GitLab CI, CircleCI --> | | |
| CDN | <!-- e.g., CloudFront, Cloudflare, Fastly --> | | |
| API Gateway | <!-- e.g., Kong, AWS API Gateway, nginx, Traefik --> | | |
| Local Dev | <!-- e.g., Tilt, docker-compose, DevContainers --> | | |

## Observability

| Layer | Preferred | Version | Rationale |
|-------|-----------|---------|-----------|
| Logging | <!-- e.g., Datadog, ELK, CloudWatch, Loki --> | | |
| Metrics | <!-- e.g., Prometheus + Grafana, Datadog, CloudWatch --> | | |
| Tracing | <!-- e.g., Jaeger, Tempo, Datadog APM, OpenTelemetry --> | | |
| Error Tracking | <!-- e.g., Sentry, Bugsnag, Rollbar --> | | |
| Alerting | <!-- e.g., PagerDuty, OpsGenie, Grafana Alerting --> | | |
| Uptime Monitoring | <!-- e.g., Better Uptime, Pingdom, UptimeRobot --> | | |

## AI / ML

| Layer | Preferred | Version | Rationale |
|-------|-----------|---------|-----------|
| LLM Provider | <!-- e.g., OpenAI, Anthropic, Azure OpenAI, self-hosted --> | | |
| Embedding Model | <!-- e.g., OpenAI ada, Cohere, local sentence-transformers --> | | |
| Vector Store | <!-- e.g., Pinecone, Weaviate, pgvector, Qdrant --> | | |
| Orchestration | <!-- e.g., LangChain, LlamaIndex, custom --> | | |

## Third-Party Services

| Concern | Preferred | Rationale |
|---------|-----------|-----------|
| Email (Transactional) | <!-- e.g., SendGrid, Postmark, SES, Resend --> | |
| Email (Marketing) | <!-- e.g., Mailchimp, Customer.io, Brevo --> | |
| SMS | <!-- e.g., Twilio, MessageBird, Vonage --> | |
| Payments | <!-- e.g., Stripe, Braintree, Adyen --> | |
| Analytics | <!-- e.g., PostHog, Mixpanel, Amplitude, GA4 --> | |
| Feature Flags | <!-- e.g., LaunchDarkly, Unleash, PostHog, Flagsmith --> | |
| File Upload | <!-- e.g., UploadThing, Cloudinary, imgix --> | |

---

## Selection Criteria

When evaluating a technology for this template:

1. **Team proficiency** — Can we ship with this today, or does it require ramp-up?
2. **Community health** — Active maintenance, responsive to security issues, growing ecosystem
3. **Operational cost** — TCO at our expected scale (not just free tier)
4. **Hiring market** — Can we find engineers who know this?
5. **Migration path** — If we need to move off it, how painful is that?
6. **Compliance** — Does it support our regulatory requirements natively?

---

## Notes

<!-- Add context about why certain choices were made, past experiences, etc. -->
