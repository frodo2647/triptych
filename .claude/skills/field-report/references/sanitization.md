# Sanitization Rules — Full Specification

Run these rules in order against every string before any rendering.
The rendered draft IS the transmitted draft, byte-for-byte.

## 1. Path replacement

Match each absolute-path prefix and replace with `<HOME>/...`:

| Pattern | Replace |
|---|---|
| `C:\\Users\\<u>` | `<HOME>` |
| `C:/Users/<u>` | `<HOME>` |
| `/Users/<u>` | `<HOME>` |
| `/home/<u>` | `<HOME>` |

`<u>` matches any segment up to the next path separator. Apply
case-insensitively on Windows paths.

## 2. Secret-shaped line drop

If a line matches the case-insensitive regex below, drop the entire line
and replace with `[redacted: secret-shaped]`:

```
(?i)(api[_-]?key|secret|password|passwd|token|netrc|bearer\s+\S+|sk-[A-Za-z0-9]{16,})
```

## 3. Env-var value drop

For any environment variable whose name matches the secret-shaped regex
above, replace its value with `<redacted>`. The variable name stays;
the value goes.

## 4. URL query-string strip

Strip query strings starting with these parameters:
`?key=`, `?token=`, `?api_key=`, `?access_token=`, `?auth=`, `?password=`.
Replace with `?<redacted-query>`.

## 5. Email pattern strip

Replace `[\w.+-]+@[\w-]+\.[\w.-]+` matches with `<redacted-email>`.

## 6. File-content truncation

Any file content over 200 lines: keep the first 50 and last 50, and
replace the middle with `[truncated, N total lines]`.

## 7. Path whitelist

Drop any reference to a file outside this allowlist (replace the
section with `[path outside whitelist]`):

- `workspace/research/...`
- `workspace/files/...`
- `.claude/skills/...` (skill bodies, not user data)
- `tools.md`
- `CLAUDE.md`
- `docs/internal/skill-sources.md`

`workspace/output/`, `workspace/snapshots/`, `core/`, `displays/`,
`integrations/`, `scripts/` are all out — those are either user-rendered
content (might contain personal results) or the framework code, and the
maintainer can read the framework source themselves.

## 8. Final scan

After applying rules 1–7, scan the draft a second time for any remaining
secret-shaped strings, paths with usernames, or email patterns. Anything
still matching is dropped on the second pass with a `[redacted: missed]`
marker. If the second pass finds anything, log a warning to the user
("sanitizer made a second-pass redaction; please review the draft
carefully before approving submission") so they double-check rule
gaps before approving.
