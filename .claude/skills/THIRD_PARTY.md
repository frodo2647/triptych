# Third-Party Skills — Attribution and Provenance

This directory contains Triptych-native skills alongside vendored third-party
skills. Third-party skills are copied verbatim from their upstream source.

## Vendored from K-Dense-AI/scientific-agent-skills (MIT)

Source: https://github.com/K-Dense-AI/scientific-agent-skills
License: MIT (see LICENSE.md in upstream repo)

Vendored on 2026-04-21:

- `scientific-writing/` — IMRAD, citations, reporting guidelines
- `scientific-critical-thinking/` — bias/confounder analysis, GRADE, statistical pitfalls
- `scientific-visualization/` — publication-quality figure design
- `paper-lookup/` — multi-database paper search (arXiv, OpenAlex, Crossref, …)
- `citation-management/` — DOI → BibTeX, validation, deduplication
- `peer-review/` — manuscript review workflow
- `hypothesis-generation/` — 8-step hypothesis workflow
- `sympy/` — symbolic derivation best practices

Each skill retains its upstream frontmatter (`metadata.skill-author: K-Dense Inc.`, `license: MIT license`) so attribution travels with the file.

## Why vendor instead of submodule or on-demand fetch

- Agent discovery is simpler when every skill is a direct subdirectory.
- The 8 vendored skills total ~1.3 MB — trivial in a research repo.
- No network dependency at session start.

For skills Triptych doesn't vendor, see `docs/internal/skill-sources.md` — the
agent can WebFetch or `git clone` on demand when a task needs deeper domain
knowledge the bundled set doesn't cover.

## Updating

To refresh a vendored skill:

```
cd /tmp && git clone --depth 1 https://github.com/K-Dense-AI/scientific-agent-skills.git
cp -r scientific-agent-skills/scientific-skills/<name>/ \
      <triptych>/.claude/skills/<name>/
```

Update the vendored-on date in this file and commit.
