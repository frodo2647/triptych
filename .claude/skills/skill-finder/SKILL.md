---
name: skill-finder
description: Find and install relevant skills on demand when bundled ones don't cover the task. Use when a task needs domain expertise (stats, bio, chem, EE, specific library) and `.claude/skills/` doesn't already have a matching skill. Triggers - "don't have a skill for", "need a skill that", "fetch a skill", "install a skill for", or any prompt where a K-Dense / awesome-claude-code skill would clearly help.
---

# Skill Finder

Triptych bundles ~30 skills in `.claude/skills/` (Triptych-native + 8 from K-Dense-AI). Claude Code surfaces the full list in every session. **Check that list first.** If the task is already covered, use the bundled skill.

If the task is *not* covered, this skill teaches you how to fetch one on demand from trusted upstream repos.

## Before fetching

- **Is the task short?** If the skill file would be longer than the answer, skip. Just do the task.
- **Is the bundled set actually covered?** Scan the session-reminder list carefully — skills like `/scientific-visualization`, `/sympy`, `/paper-lookup` cover more than their names suggest.
- **Do you already know the pattern?** Generic coding / ML / derivation work doesn't need a new skill. Skills earn their keep when they encode domain-specific conventions that are easy to get wrong (journal formatting, specific statistical tests, PRISMA-style reviews, etc.).

If you still want a skill, continue.

## Trusted sources

Ranked by trust:

1. **PRPM** (https://prpm.dev, ~7,500 packages) — primary fetch source.
   Verified-contributor model, MIT registry, npm-installable CLI.
   `prpm install <name>` is the canonical fetch path.
2. **K-Dense-AI/scientific-agent-skills** (MIT, ~133 skills) — fallback
   for science/methodology when not on PRPM. The 8 we bundle came from here.
3. **anthropics/skills** (Apache 2.0) — fallback. Mostly office-doc + dev
   methodology; low fit for research, high fit as a style reference.
4. **obra/superpowers** (per-skill licenses) — debugging/TDD methodology.
   Useful for editing Triptych's own code; not for research tasks.

Full catalogue with per-domain recommendations in `docs/internal/skill-sources.md`.

## Fetch recipe — PRPM first

```bash
prpm --version || npm i -g prpm
prpm install <name>
# locate where prpm placed it (usually ~/.claude/skills/<name>):
prpm where <name> 2>/dev/null || ls ~/.claude/skills/<name>
# project-scope copy:
cp -r ~/.claude/skills/<name>/ .claude/skills/<name>/
```

Then:
1. Read the fetched SKILL.md frontmatter + first 20 lines. If it doesn't
   match the task or looks low-quality, delete and move on.
2. Update `.claude/skills/THIRD_PARTY.md` with name, source URL (PRPM
   page), license, fetch date.
3. Claude Code picks up new skills on the next prompt — no restart.

## Trust gate

**Auto-fetch only from the per-domain recommended-packages list** in
`docs/internal/skill-sources.md`. For anything else, read SKILL.md
frontmatter + first 20 lines first. PRPM's verified-contributor flag is
not a substitute for reading what you're installing.

## Fallback when PRPM lacks the skill

Use the older direct-clone recipe against K-Dense or anthropics:

```bash
mkdir -p /tmp/kd && cd /tmp/kd
git clone --depth 1 https://github.com/K-Dense-AI/scientific-agent-skills.git
cp -r scientific-agent-skills/scientific-skills/<name>/ \
      <triptych-repo>/.claude/skills/<name>/
```

Same THIRD_PARTY.md update step applies.

## Related

- `docs/internal/skill-sources.md` — full trusted-source catalogue with task→skill cheatsheet
- `.claude/skills/THIRD_PARTY.md` — log of already-vendored external skills
- `docs/internal/ecosystem-scan.md` — broader ecosystem survey (re-evaluated quarterly)
