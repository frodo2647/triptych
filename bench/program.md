# Triptych AutoResearch — Agent Instructions

You are optimizing the Triptych research system. Your goal is to improve the benchmark score by editing ONE file at a time.

## The loop

1. Read the current editable file
2. Read `bench/results.tsv` and `bench/run.log` to understand what's working and what's failing
3. Form a hypothesis about what change would improve the score
4. Edit the file and `git commit`
5. Run: `python -X utf8 bench/eval.py > bench/run.log 2>&1`
6. Extract result: `grep "^score:" bench/run.log`
7. If score improved: keep the commit
8. If score did not improve: `git reset --hard HEAD~1`
9. NEVER STOP.

## What you can edit (one file per cycle)

Everything Claude reads during operation is fair game:

- `CLAUDE.md` — system-wide instructions (start here)
- `.claude/skills/autonomous/SKILL.md` — the autonomous research loop
- `.claude/skills/watcher/SKILL.md` — the watcher protocol
- `.claude/agents/verifier.md` — verifier agent prompt
- `.claude/agents/cross-verifier.md` — cross-verifier agent prompt
- `.claude/rules/*.md` — path-specific rules
- `core/verify.py`, `core/research.py` — infrastructure code

## What you cannot edit

`bench/generators.py`, `bench/eval.py` — these are the immutable evaluation. If you edit them, you're cheating.

## How to use the run log

`bench/run.log` contains per-problem detail: what the problem was, what the pipeline produced, where it went wrong, what the verifier said. READ THIS before forming your next hypothesis. The score tells you IF something improved. The log tells you WHY it failed and WHAT to try.

Look for patterns:
- Which problem types fail most? Focus there.
- Are errors being caught? If not, the verifier prompt needs work.
- Is the pipeline timing out? Maybe the autonomous loop is too verbose.
- Are answers correct but not matching the check? Maybe the output format needs guidance.

## Rules

- One change per cycle. Can't attribute improvement otherwise.
- Always commit before running.
- Always revert if score doesn't improve.
- Read run.log to understand failures before proposing the next change.
- Don't make the same change twice.
- Use a different seed occasionally (`--seed N`) to avoid overfitting to seed 42.
