---
name: physics-in-triptych
description: Mentor for physics work in Triptych — wires sympy-mcp, desmos-mcp, manim-mcp, show_latex, init_research, and /verifier into the canonical order, and surfaces the five pitfalls physicists actually fall into. Use when the user is deriving an equation of motion, solving a Lagrangian/Hamiltonian, working a mechanics/EM/QM problem, or any "let's derive" turn.
---

# Physics in Triptych

Mentor skill, not tactical. Teaches how to *use Triptych's tools* for
physics work in a way that catches the errors physicists actually make.
Doesn't teach physics. For sub-disciplines (GR, fluid dynamics, plasma,
QFT) ask `/skill-finder` to fetch a tactical skill.

## When to use

The user mentions: a derivation, equation of motion, Lagrangian/Hamiltonian,
mechanics/EM/QM problem, or "let's derive." Skip for back-of-envelope
conversational physics — that's just talking.

## Triptych toolchain — canonical order

| Step | Tool |
|---|---|
| 1. State problem | `init_research(goal)` + `show_research()` |
| 2. Assumptions & frame | edit `state.md` "assumptions" |
| 3. Symbolic manipulation | `mcp__sympy-mcp__*` |
| 4. Render steps | `show_latex(name="step-N")` |
| 5. Quick visual sanity | `mcp__desmos-mcp__plot_math_function` |
| 6. Animate dynamics | `mcp__manim-mcp__execute_manim_code` |
| 7. Emit claims | `emit_claim(...)` |
| 8. Verify | `/loop 60s /verifier` |

Steps 1–2 always come first. Skip the rest if not needed.

## Top pitfalls

### 1. Dimensional analysis is free; do it first

Before any algebra, write expected dimensions of every symbol and every
side. Use `mcp__sympy-mcp__quantity_simplify_units` or track [M L T] by
hand. Wrong units → no later care fixes it. Failure mode: missing `c²`
hidden inside a long derivation.

### 2. Pick a frame and sign convention before equation 1

Ambiguous frames are the second-largest error source. Before F = ma,
state which frame (lab/body/rotating), which axes, which sign for the
force. Put it in `state.md` under "assumptions."

### 3. Limit-case sanity before general result

Once a closed form is in hand, plug in: ε → 0, m → ∞, v → c, θ → 0.
Each must reduce to something obvious. Render side-by-side via
`show_latex(name="limit-checks")`.

### 4. Symbolic first, numeric only after the form is settled

NumPy is faster and lossier; SymPy is exact. Get the closed form,
simplify, check limits — *then* substitute numerical values.

### 5. `/sympy` past three substitutions

Past three nested substitutions, hand-algebra error rate jumps. Hand
off to `mcp__sympy-mcp__substitute_expression` and `simplify_expression`.
If the user prefers hand-derivation for pedagogy, let them — but offer
to cross-check with sympy.

## Mentor mode

- **Exploration**: surface principles as questions. "What frame?" not
  "you forgot to pick a frame."
- **Formalization**: apply silently. Mention only when one changed the answer.
- **User asks "how do I approach this?"**: structure around the toolchain table.

## Tactical skills via /skill-finder

For depth: `/skill-finder general-relativity`,
`/skill-finder fluid-dynamics`, `/skill-finder qft`,
`/skill-finder plasma`, `/skill-finder computational-physics`. Defaults
to PRPM; falls back to K-Dense / awesome-claude-code clone. See
`docs/internal/skill-sources.md`.

## Related

- `/think-rigorously` — patterns these pitfalls instantiate
- `/sympy` — symbolic core
- `/scientific-critical-thinking` — evaluating *others'* physics claims
- `/verifier` — once `emit_claim` is firing
- `/integration-design` — before adding any new physics tool bridge
- `mcp__sympy-mcp__*`, `mcp__desmos-mcp__*`, `mcp__manim-mcp__*`
