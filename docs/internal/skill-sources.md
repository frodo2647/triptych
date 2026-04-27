# Skill Sources — where to pull more skills from when you need them

Triptych bundles a curated set of skills in `.claude/skills/`. When a task
needs domain knowledge those don't cover, the agent can fetch additional
skills from trusted upstream repos on demand instead of waiting for a
maintainer to vendor them.

This doc is the map: repos we trust, what they cover, how to pull a single
skill without cloning the whole pile.

## PRPM (https://prpm.dev) — primary fetch source

**Why PRPM first**: verified contributors, MIT-licensed registry,
~7,500 packages, npm-installable CLI. One-shot install.

```bash
prpm --version || npm i -g prpm
prpm install <name>
prpm where <name>      # locate the install path
cp -r <prpm-path>/<name> .claude/skills/<name>
```

### Recommended packages by domain

The maintainer fills these in after browsing PRPM. The structure ships;
agents only auto-fetch from this list. Anything else, read SKILL.md
frontmatter + first 20 lines first.

**physics** — TBD (search PRPM for: general-relativity, fluid-dynamics,
qft, plasma, computational-physics)

**math** — TBD (search PRPM for: category-theory, algebraic-geometry,
combinatorics, lean-proofs, pde)

**ml** — TBD (search PRPM for: pytorch-internals, jax, huggingface,
rlhf, distributed-training)

**other** — agent searches PRPM with the user's domain query; user
confirms before install.

## Fallback sources

The repos below remain in use when a needed skill isn't on PRPM.

## Trusted repos

### K-Dense-AI/scientific-agent-skills (MIT)

- **URL**: https://github.com/K-Dense-AI/scientific-agent-skills
- **License**: MIT
- **Content**: ~133 skills covering scientific writing, research workflows, bio/chem/clinical, ML, physics, math. Each skill is an `agentskills.io`-compliant SKILL.md with reference files and helper scripts.
- **Already bundled** (don't re-fetch): `scientific-writing`, `scientific-critical-thinking`, `scientific-visualization`, `paper-lookup`, `citation-management`, `peer-review`, `hypothesis-generation`, `sympy`.

When to pull more from K-Dense:

| Task cue | Skill to fetch |
|---|---|
| "train a classifier", "sklearn workflow", "baseline model" | `scikit-learn` |
| "fine-tune a transformer", "LoRA", "HuggingFace" | `transformers` |
| "write a training loop", "distributed training" | `pytorch-lightning` |
| "explain this model", "feature importance", "SHAP" | `shap` |
| "t-test", "ANOVA", "significance", "confidence interval" | `statistical-analysis` |
| "brainstorm hypotheses" (open-ended, not structured) | `scientific-brainstorming` |
| "evaluate this journal/paper/author" | `scholar-evaluation` |
| "IMRAD template", "Nature submission format" | `venue-templates` |
| "systematic review", "PRISMA", "7-phase literature" | `literature-review` (deeper than ours) |

To pull one skill on demand:

```bash
mkdir -p /tmp/kd && cd /tmp/kd
git clone --depth 1 https://github.com/K-Dense-AI/scientific-agent-skills.git
cp -r scientific-agent-skills/scientific-skills/<name>/ \
      <triptych>/.claude/skills/<name>/
# Update .claude/skills/THIRD_PARTY.md with the new entry + fetch date
```

Claude Code picks it up on the next prompt; no server restart.

### anthropics/skills (Apache 2.0)

- **URL**: https://github.com/anthropics/skills
- **License**: Apache 2.0
- **Content**: Anthropic's reference skill pack. Document I/O (docx, pdf, pptx, xlsx), design/frontend, dev/meta (mcp-builder, skill-creator).
- **Fit for Triptych**: low — these are mostly office-document and dev-methodology skills. Keep as reference for SKILL.md *style*, not as a bundling source.
- Skills from here (if any turn out useful): `pdf`, `skill-creator` when building a new Triptych-native skill.

### obra/superpowers

- **URL**: https://github.com/obra/superpowers
- **License**: check per-skill
- **Content**: Agentic methodology — TDD, four-phase debugging, subagent code review, "TDD for skills."
- **Fit for Triptych**: process/methodology, not knowledge. Skip for research work, useful when editing Triptych's own code in a disciplined way.

### VoltAgent/awesome-agent-skills

- **URL**: https://github.com/VoltAgent/awesome-agent-skills
- **License**: mixed (per-skill)
- **Content**: 1000+ curated skills, cross-platform. Discovery index.
- **Fit**: hunting ground when nothing in K-Dense or Anthropic matches. Pick carefully — signal-to-noise varies.

## When to fetch vs. when to skip

**Fetch** when:
- The task is in a supported domain and the bundled skills don't cover it
- The fetch costs seconds, the alternative costs minutes of re-deriving conventions
- The upstream SKILL.md is high-quality (read the frontmatter + first 20 lines before committing to use)

**Skip and just do the task** when:
- The task is short and the skill would be longer than the answer
- Nothing relevant exists (don't force-fit an unrelated skill)
- The existing bundled skills actually cover it and you're just anxious

## Recording what you pulled

Every time a skill is fetched on demand and kept:
1. Add it to `.claude/skills/THIRD_PARTY.md` with source URL, license, and fetch date.
2. If it's a good fit and likely to be reused, commit it alongside the change.
3. If it's one-off, pull it into a branch and delete before merging — don't leave personal vendored skills on `master`.

## Revisiting this list

Re-check quarterly against `docs/internal/ecosystem-scan.md` — that doc is the broader survey of the Claude Code / agent-skill ecosystem. When the ecosystem scan gets refreshed, see if any new high-signal repos should be added here.
