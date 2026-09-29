---
inclusion: manual
---

# User Journey (`journey`)

Maps user experience, assigning scores to specific actions across phases.

```mermaid
journey
    title E-Commerce Checkout
    section Cart
      Review Items: 5: User
      Apply Promo: 3: User
    section Payment
      Process Auth: 4: System

```

* **Anti-patterns:** Missing sections (phases); using non-numeric scores.
* **Telemetry metrics:** Parse failure rate on actor declarations.
* **Other design options:** Map alternative failure paths as separate journeys rather than cramming them into the happy path.