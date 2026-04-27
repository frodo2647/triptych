---
name: ml-in-triptych
description: Mentor for machine-learning work in Triptych — wires data exploration, seed control, overfit-1-batch, W&B (External), /autoresearch, and show_progress into the canonical order, and surfaces the five pitfalls that bite ML work most (W&B-not-Optuna-embed, seed every RNG, gradient-finite first step, train/val leakage, ablate one variable). Use when the user is training a model, tuning hyperparameters, working with a dataset, debugging a training loop, or any "let's train" turn.
---

# ML in Triptych

Mentor skill, not tactical. Teaches how to *use Triptych's tools* for
ML work in a way that catches the errors ML practitioners actually make.
Doesn't teach ML. For specific frameworks (PyTorch internals, JAX,
HuggingFace transformers, RLHF) ask `/skill-finder` for a tactical
skill.

## When to use

The user mentions: training a model, tuning hyperparameters, debugging
a loss curve, working a dataset, "let's train," "the model isn't
learning." Skip for casual ML chat — that's just talking.

## Triptych toolchain — canonical order

| Step | Tool |
|---|---|
| 1. Profile dataset | `data:explore-data` |
| 2. State problem & metric | `init_research(goal)` |
| 3. Seed control | every RNG (np, torch, python, cuda) |
| 4. Overfit on 1 batch | sanity-check the model can fit anything |
| 5. Track runs | **W&B (External)** via `integrations/wandb.py` |
| 6. Show training live | `show_progress(...)` updating per epoch |
| 7. Sweep | `/autoresearch` for metric-driven iteration |
| 8. Emit + verify claims about results | `emit_claim(...)`, `/loop 60s /verifier` |

Skip steps the work doesn't need. Steps 1–4 always come before 5–8.

## Top pitfalls

### 1. W&B as External, not Optuna embedded

Optuna Dashboard fights the panel size — trial 1 cost 4 scripts +
`min-width: 1400px` clamp. W&B as `ExternalTool` ships clean. Default to
W&B for run tracking; reach for Optuna only for its TPE/CMA-ES search,
and run it headless feeding metrics to W&B. See `/integration-design`.

### 2. Seed every RNG

`np.random.seed`, `torch.manual_seed`, `torch.cuda.manual_seed_all`,
`random.seed`, `PYTHONHASHSEED`. Not seeding turns "the model is
worse" into a coin flip. Pin in code, log to W&B, surface in `state.md`.

### 3. Gradient-finite check on first step

Log `grad.norm()` after the first backward pass. NaN/Inf there → loss
formulation, init scale, or mixed-precision config is wrong; more
epochs won't fix it. Fail fast, fail loud.

### 4. Train/val leakage audit

Same sample in both splits? Time-series peeking ahead? GroupKFold for
IDs spanning splits? Most "too good to be true" results are leakage.
Audit takes 5 minutes; post-hoc cleanup of a leaked benchmark takes
weeks.

### 5. Ablate one variable at a time

LR + optimizer + batch size in one run gives no signal about which
mattered. `/autoresearch` enforces one-axis sweeps; hand-tuning, write
the change in `state.md` "Tests" before pressing run.

## Mentor mode

- **Exploration**: surface principles as questions. "Did we seed?" not
  "you forgot to seed."
- **Formalization**: apply silently. Mention only when it changed the result.
- **User asks "why is the model bad?"**: walk pitfalls 2–4 first.

## Tactical skills via /skill-finder

For depth: `/skill-finder pytorch-internals`, `/skill-finder jax`,
`/skill-finder huggingface-transformers`, `/skill-finder rlhf`,
`/skill-finder distributed-training`. Defaults to PRPM. See
`docs/internal/skill-sources.md`.

## Related

- `/think-rigorously` — patterns these pitfalls instantiate
- `/autoresearch` — Karpathy-style metric-driven iteration loop
- `/integration-design` — when adding any new ML tool bridge
- `/scientific-critical-thinking` — evaluating *others'* ML claims
- `integrations/wandb.py` — canonical ExternalTool reference
- `data:explore-data`, `data:data-validation` — bundled data skills
