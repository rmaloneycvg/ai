# System Workflow Diagrams: [Project Name]

**Date:** YYYY-MM-DD | **Author:** [Architect]
**Purpose:** Data flow and interaction patterns for key use cases identified in scope.

---

## Authentication Flow

```mermaid
sequenceDiagram
    participant User as User Browser
    participant App as Application
    participant GW as Gateway
    participant Auth as Auth Provider
    participant DB as Database

    User->>App: Click Login
    App->>GW: Redirect to Auth
    GW->>Auth: Authorization Request
    Auth->>User: Login Page
    User->>Auth: Credentials
    Auth->>Auth: Validate
    Auth->>GW: Authorization Code
    GW->>Auth: Exchange Code for Tokens
    Auth-->>GW: Access Token and Refresh Token
    GW->>DB: Create Session
    GW-->>App: Set HttpOnly Cookie
    App-->>User: Authenticated View
```

---

## CRUD Operation Flow

```mermaid
sequenceDiagram
    participant Client as Client
    participant GW as Gateway
    participant API as API Service
    participant Val as Validator
    participant DB as Database
    participant Cache as Cache
    participant Queue as Queue

    Client->>GW: POST /resource
    GW->>API: Forward
    API->>Val: Validate payload
    alt Invalid
        Val-->>API: Validation errors
        API-->>Client: 400 Bad Request
    else Valid
        API->>DB: INSERT
        DB-->>API: Created record
        API->>Cache: Invalidate related keys
        API->>Queue: Emit ResourceCreated event
        API-->>Client: 201 Created
    end
```

---

## Search Flow

```mermaid
sequenceDiagram
    participant Client as Client
    participant GW as Gateway
    participant API as API Service
    participant Cache as Cache
    participant Search as Search Index

    Client->>GW: GET /search?q=term
    GW->>API: Forward
    API->>Cache: Check search cache
    alt Cache hit
        Cache-->>API: Cached results
    else Cache miss
        API->>Search: Query index
        Search-->>API: Results
        API->>Cache: Store with short TTL
    end
    API-->>Client: Search results
```

---

## File Upload Flow

```mermaid
sequenceDiagram
    participant Client as Client
    participant GW as Gateway
    participant API as API Service
    participant Store as Object Storage
    participant DB as Database
    participant Queue as Queue

    Client->>GW: POST /upload (multipart)
    GW->>API: Forward
    API->>API: Validate file type and size
    API->>Store: Upload to object storage
    Store-->>API: Storage URL
    API->>DB: Save file metadata
    API->>Queue: Emit FileUploaded event
    API-->>Client: 201 with file URL
```

---

## Background Job Flow

```mermaid
sequenceDiagram
    participant Trigger as Trigger Source
    participant Queue as Message Queue
    participant Worker as Worker
    participant DB as Database
    participant External as External Service
    participant DLQ as Dead Letter Queue

    Trigger->>Queue: Publish job
    Queue->>Worker: Deliver
    Worker->>DB: Load context
    Worker->>External: Call external API
    alt Success
        External-->>Worker: Response
        Worker->>DB: Save result
        Worker->>Queue: ACK
    else Failure
        External-->>Worker: Error
        Worker->>Queue: NACK with retry
        Note over Queue,Worker: Retry up to N times
        Queue->>DLQ: Move to DLQ after max retries
    end
```

---

## Notification Flow

```mermaid
flowchart TD
    Event[System Event] --> Router{Notification Router}
    Router -->|Email| EmailQ[Email Queue]
    Router -->|Push| PushQ[Push Queue]
    Router -->|SMS| SMSQ[SMS Queue]
    Router -->|In-App| InAppQ[In-App Queue]

    EmailQ --> EmailWorker[Email Worker]
    PushQ --> PushWorker[Push Worker]
    SMSQ --> SMSWorker[SMS Worker]
    InAppQ --> InAppWorker[In-App Worker]

    EmailWorker --> EmailSvc[Email Service]
    PushWorker --> PushSvc[Push Service]
    SMSWorker --> SMSSvc[SMS Service]
    InAppWorker --> DB[(Database)]
```

---

## Scheduled Task Flow

```mermaid
flowchart TD
    Scheduler[Scheduler / Cron] --> Check{Task Due?}
    Check -->|No| Wait[Wait]
    Check -->|Yes| Lock{Acquire Lock?}
    Lock -->|No| Skip[Skip - Another Instance Running]
    Lock -->|Yes| Execute[Execute Task]
    Execute --> Result{Success?}
    Result -->|Yes| Release[Release Lock]
    Result -->|No| Retry{Retries Left?}
    Retry -->|Yes| Execute
    Retry -->|No| Alert[Alert and Release Lock]
    Release --> Log[Log Completion]
```

---

## Data Sync / Integration Flow

```mermaid
sequenceDiagram
    participant Ext as External System
    participant Webhook as Webhook Receiver
    participant Queue as Queue
    participant Sync as Sync Worker
    participant DB as Database
    participant Notify as Notification Service

    Ext->>Webhook: POST /webhooks/partner
    Webhook->>Webhook: Verify signature
    Webhook->>Queue: Enqueue sync event
    Webhook-->>Ext: 200 OK
    Queue->>Sync: Deliver event
    Sync->>DB: Upsert data
    Sync->>Notify: Alert if conflicts
    Sync->>Queue: ACK
```

---

## Custom Flows

<!-- Add project-specific flows below based on key use cases from the scope document -->

### Flow: [Use Case Name]

<!-- Describe the use case this flow represents -->

```mermaid
sequenceDiagram
    participant A as Actor
    participant B as System
    A->>B: Action
    B-->>A: Response
```

### Flow: [Use Case Name]

<!-- Describe -->

```mermaid
sequenceDiagram
    participant A as Actor
    participant B as System
    A->>B: Action
    B-->>A: Response
```

---

## Flow Summary Table

| Flow | Trigger | Critical Path? | Latency Target | Error Handling |
|------|---------|---------------|----------------|----------------|
| Authentication | User login | Yes | <!-- ms --> | <!-- redirect to error page --> |
| CRUD | User action | Yes | <!-- ms p95 --> | <!-- 4xx/5xx with message --> |
| Search | User query | Yes | <!-- ms p95 --> | <!-- fallback to DB query --> |
| File Upload | User action | No | <!-- seconds --> | <!-- retry with exponential backoff --> |
| Background Job | Event/Schedule | No | <!-- seconds --> | <!-- DLQ after N retries --> |
| Notification | System event | No | <!-- seconds --> | <!-- retry, eventually drop --> |
| Data Sync | External webhook | No | <!-- seconds --> | <!-- DLQ, manual reconciliation --> |
