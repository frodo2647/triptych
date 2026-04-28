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

## 5b. User display-name strip

The session prompt frequently puts the user's first name in the agent's mouth — drafted reports often quote "Quinn said X" or "the user (Alice) wanted Y" without the agent realizing it. The other rules don't catch this because a name isn't a secret pattern; it's contextual PII.

Source the user's name from these locations (collect all unique non-trivial tokens, dedupe):

| Source | Field |
|---|---|
| `git config user.name` | full string; also split on whitespace and treat each token as a candidate |
| `~/.claude/settings.json` | `user.name` if present |
| `MEMORY.md` user-profile entries | frontmatter `name:` field; first-line `Name:` patterns |
| `$USER` / `$USERNAME` env vars | only if longer than 2 chars and not a generic handle (`admin`, `user`, `owner`, `root`, `desktop-*`, etc.) |

For each collected token of length ≥ 3, replace whole-word case-insensitive matches in the draft with `<USER>`. Skip tokens that are common English words (`John`, `May`, `Will` etc. — if the token also appears in `/usr/share/dict/words` or equivalent, require a 4+ character match and prefer last-name tokens).

After replacements, run a final occurrence-count of the same tokens. If the count is non-zero, the user-name pass missed something — surface to the user before submit:

> *Sanitizer flagged: name "<token>" still appears N time(s) after scrub. Open draft to review (yes/no)?*

This is the only sanitization step that asks the user a question — it's worth the friction because a slipped-through name is the highest-stakes leak the field-report path can produce.

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
