---
inclusion: manual
---


# Event Modeling (`eventmodeling`)

Plots information flow over time across UI, Commands, and Events.

```mermaid
eventmodeling
  tf 01 ui CheckoutUI
  tf 02 cmd SubmitOrder
  tf 03 evt OrderSubmitted

```

* **Anti-patterns:** Dropping the time-frame (`tf`) prefixes which breaks the chronological rendering.
* **Telemetry metrics:** Token complexity density (event modeling syntax is terse, so large payloads indicate injected data).
* **Other design options:** Integrate JSON payload blocks to define the exact shape of commands and events.