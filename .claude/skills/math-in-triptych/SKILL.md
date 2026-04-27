---
name: math-in-triptych
description: Mentor for math work in Triptych — wires sympy-mcp, desmos-mcp, show_latex, init_research, and /verifier into the canonical order, and surfaces the four pitfalls that bite first-person mathematics (type/domain check, small-case verify, counterexample-search before proof attempt, symbolic-first). Use when the user is proving, computing, manipulating algebraic expressions, working with limits/series/integrals, or any "let's prove" or "let's compute" turn.
---

# Math in Triptych

Mentor skill, not tactical. Teaches how to *use Triptych's tools* for
math work in a way that catches the errors that show up most often.
Doesn't teach math. For specific areas (category theory, algebraic
geometry, combinatorics, formal verification with Lean) ask
`/skill-finder` for a tactical skill.

## When to use

The user mentions: a proof, computation, limit/series/integral, algebraic
manipulation, "prove that," "show that," "compute." Skip for casual
math chat — that's just talking.

## Triptych toolchain — canonical order

| Step | Tool |
|---|---|
| 1. State problem | `init_research(goal)` + `show_research()` |
| 2. Domain & assumptions | edit `state.md` "assumptions" |
| 3. Symbolic manipulation | `mcp__sympy-mcp__*` |
| 4. Render steps | `show_latex(name="step-N")` |
| 5. Visual sanity | `mcp__desmos-mcp__plot_math_function` |
| 6. Emit claims | `emit_claim(...)` |
| 7. Verify | `/loop 60s /verifier` |

Steps 1–2 always come first.

## Top pitfalls

### 1. Type & domain check before manipulation

Before any algebra, write what each symbol *is*: real, complex, integer,
function on what domain. "f is differentiable on R" simplifies very
differently from "f is continuous on [0,1]." Most "obvious" steps that
go wrong skip a domain assumption — division by zero in disguise,
swapping limits with sums on a non-uniformly-convergent series,
applying L'Hôpital outside its hypotheses.

### 2. Small-case verify before general proof

Before attempting to prove a statement for all n, check it at n = 1, 2,
3. If it fails at n = 2, you don't have a proof to write — you have a
counterexample to find. If it holds, the small cases often suggest the
inductive step.

### 3. Counterexample-search before proof attempt

Spend 5 minutes trying to break the statement before trying to prove
it. Boundary conditions (empty set, n = 0, identity element, infinity),
degenerate cases (constant function, single-point space), pathological
examples (Cantor set, Weierstrass function, p-adic numbers). A failed
proof attempt eats more time than a found counterexample.

### 4. Symbolic-first; numeric only when the form is settled

For closed-form work, `mcp__sympy-mcp__*` over hand-algebra past three
substitutions — same rule as physics. NumPy is downstream of "we know
the form." Generating numerical examples to *check* a closed form is
fine; using them in place of one is not.

## Mentor mode

- **Exploration**: surface principles as questions. "What's the domain?"
  not "you forgot the domain."
- **Formalization**: apply silently. Mention only when it changed the answer.
- **User asks "how do I approach this?"**: structure around the toolchain.

## Tactical skills via /skill-finder

For depth: `/skill-finder category-theory`, `/skill-finder algebraic-geometry`,
`/skill-finder combinatorics`, `/skill-finder lean-proofs`,
`/skill-finder pde`. Defaults to PRPM. See `docs/internal/skill-sources.md`.

## Related

- `/think-rigorously` — patterns these pitfalls instantiate
- `/sympy` — symbolic core
- `/scientific-critical-thinking` — evaluating *others'* proofs
- `/verifier` — once `emit_claim` is firing
- `mcp__sympy-mcp__*`, `mcp__desmos-mcp__*`
