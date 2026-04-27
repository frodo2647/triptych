---
name: field-report
description: User-controlled feedback to the Triptych maintainer. Mines the current session for context, sanitizes locally, drafts a GitHub issue body, asks the user to review the full draft, and only on explicit approval submits via gh issue create. Use when the user says "/field-report", "send feedback", "report a bug to maintainer", "tell the team about this," or wants to share a missing-skill / new-use-case observation. NEVER auto-invoked; user-only trigger.
---

# Field Report

Privacy-first feedback channel from a Triptych user to the maintainer's
GitHub repo. Built so nothing leaves the machine without the user
seeing the exact text and saying yes.

## When to use

- User invokes `/field-report` directly
- User says "send feedback," "report this bug," "tell the maintainer,"
  "this is a missing skill"
- **NEVER auto-invoke.** This skill only runs when the user asks for it.

## Flow — every step gates on user approval

### 1. Greet and elicit type

Ask: "What kind of report? (bug / missing-skill / new-use-case / general)"
Store the answer.

### 2. Ask permission before any read

"To draft this report I'd like to read: `state.md`, the last 20 entries
of `claims.jsonl`, recent verification failures, session memory, and
`tools.md` known-issues. OK?" Wait for yes. On no, ask the user to
provide the context themselves.

### 3. Read the whitelisted set

Only these paths:
- `workspace/research/state.md`
- last 20 lines of `workspace/research/claims.jsonl`
- recent failures in `workspace/research/verification/*.jsonl`
- `memory/` entries with mtime within this session
- `tools.md` lines matching the user's complaint
- last 50 lines of any log file modified in the last hour

Any other path → drop with note in draft.

### 4. Sanitize locally before any rendering

**CRITICAL: sanitization always precedes rendering.** Apply these rules
in order (full list in `references/sanitization.md`):

- Strip absolute paths matching `C:\\Users\\<u>`, `/Users/<u>`, `/home/<u>` → `<HOME>/...`
- Drop lines matching `(?i)(api[_-]?key|secret|password|token|netrc|bearer\s+\S+|sk-[A-Za-z0-9]{16,})`
- Drop env-var values for keys matching the regex above
- Truncate file contents > 200 lines → `[truncated, N lines]`
- Strip URLs containing `?key=`, `?token=`, or `?api_key=`
- Strip email regex `[\w.+-]+@[\w-]+\.[\w.-]+`

### 5. Draft a markdown issue body

Sections: Title, Type, Environment (OS, Triptych version from
`package.json`, Python version), Reproduction, Expected, Actual,
Sanitized excerpts.

### 6. Print the FULL draft to the terminal and ask

```
Exact text to submit. Reply: yes / edit / cancel.
```

On `edit`, write draft to `workspace/files/field-report-<ts>.md` and
wait. On `cancel`, abort silently.

### 7. Submit only on explicit `yes`

```bash
gh issue create \
  --repo "${TRIPTYCH_FEEDBACK_REPO:-frodo2647/triptych}" \
  --title "<title>" \
  --body-file <draft-tmp-file>
```

`TRIPTYCH_FEEDBACK_REPO` env var overrides default. Fallback when
`gh --version` fails: write draft to `workspace/files/field-report-<ts>.md`
and tell the user the URL + path so they can submit manually.

## Privacy invariants

**IMPORTANT** — these are non-negotiable:

1. Nothing leaves the machine until step 6 returns `yes`.
2. Sanitization always precedes rendering — the user only sees sanitized text.
3. The rendered draft IS what gets submitted byte-for-byte. No silent edits between step 6 and step 7.
4. No ambient telemetry. Ever.
5. If the user is unsure, default to `cancel`.

## Related

- `references/sanitization.md` — full sanitization ruleset
- `gh` (GitHub CLI) — the only outbound channel
- `core.research`, `memory/` — read sources for context
- `/skill-finder` — if the report is "missing skill: X," offer to fetch it via PRPM first
