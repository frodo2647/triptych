---
description: Detects first-time Triptych setup and triggers onboarding
---

If `CLAUDE.local.md` does not exist in the project root, this is a first boot. Run the `/first-boot` skill — it routes to Stage 0 (fast-path: subagent does setup in the background while the main agent works on the user's task) when the first message is substantive, or Stage 1 (slow-path: guided ceremony) when the user came in cold. Either way, setup must not block engagement with a user who arrived with a real task.
