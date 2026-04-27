# r/ClaudeAI post — ready-to-paste copy

## When to post

Ideally ~6 hours after the Show HN post goes live, same day. Tuesday–Thursday afternoon US time. This way the HN audience and the Reddit audience aren't competing for your attention in the same hour, and you can actually reply to comments on both.

## Flair

Use **"Built with Claude"** flair. The sub explicitly supports project shares under this flair — they want (1) what you built, (2) how, (3) screenshots/demo, (4) at least one example prompt. All four are covered below.

## Title

```
I built Triptych — turns Claude Code into a research tool, not just coding
```

Alternatives if that one doesn't feel right:

- `Triptych: a three-panel workspace that turns Claude Code into a research tool`
- `Built a three-panel workspace for doing research with Claude Code`
- `I'm a physics student — built Triptych, a research workspace for Claude Code`

## Post body

```
Hey everyone. I've been using Claude Code a lot for my physics research, and it
always felt slightly wrong — like I was forcing a coding tool to do work it
wasn't really shaped for. So over the last few months I built Triptych, a
three-panel workspace that sits on top of Claude Code and gives it room to
actually do research.

A bit of motivation up front: Claude Code works so well for coding because
the filesystem and compiler close the loop — wrong code crashes. For a
wrong derivation, nothing crashes. Worse, I noticed my best sessions weren't
the ones where I just accepted Claude's answer; they were the ones where I
argued with it, made it argue against itself, and surfaced what it was
silently assuming. Triptych is shaped around that kind of back-and-forth
rather than around "give me the answer."

**The three panels:**

- **Left — workspace for me:** tldraw drawing canvas, document editor,
  spreadsheet, markdown editor with KaTeX, code editor, PDF viewer, and a
  "desktop window watcher" that lets Claude see any window on my desktop
- **Middle — display for Claude:** matplotlib and plotly charts, LaTeX
  equations, Three.js 3D surfaces and vector fields, step-by-step derivations,
  a research state graph that tracks verified results
- **Right — Claude Code itself** with full filesystem access

The filesystem is the communication channel. When Claude writes a plot to
`workspace/output/`, the display auto-reloads. When I sketch something on the
canvas, Claude can see the screenshot. No database, no plugin registry —
files all the way down.

**The whiteboard is the part I reach for most.** I can sketch a problem by
hand — write out a Lagrangian, work through the algebra, draw a free-body
diagram — and Claude reads the canvas directly. So I do physics the way I
actually think (handwritten, messy) while Claude checks my algebra
mid-derivation and formalizes what I wrote into LaTeX when I'm done. Because
it runs in the browser, I open it on a tablet for the whiteboard at the same
time as my laptop for the display.

**Working in parallel.** Because Claude Code is agentic, while I'm deriving
something by hand it can be running a numerical solver on the equations
it's already seen, building a simulation of the system, or generating plots
of the limiting cases in the background. By the time I finish the algebra,
the next thing I'd ask for is usually already sitting in the display.

**Verification + push-back.** An independent agent checks every significant
claim without seeing Claude's reasoning, using SymPy, numerical spot-checks,
and dimensional analysis. At milestones a second agent re-derives the
result via a different method, and a separate red-team agent reads the
work and tries to challenge it. The red-team is calibrated to return
"nothing substantive" when the work is sound — an agent that always finds
problems is just as useless as one that never does. There's also a sister
pass that surfaces unstated assumptions before a result becomes
load-bearing.

**Triptych vs autoresearch.** If you have a clear metric to optimize
(benchmark score, latency, accuracy on a fixed set), Karpathy's autoresearch
is probably the right tool. Triptych is for the messier stuff in between —
derivations, design calls, anything where the work is partly figuring out
what counts as the right answer.

**Example session** (one of my actual prompts):

> "I have a coupled oscillator system with two masses and three springs.
> Set up the Lagrangian, derive the equations of motion, solve for the
> normal modes, and show me a 3D visualization of each mode with a slider
> for the mode amplitude."

Claude writes the Lagrangian to the display as rendered LaTeX, the derivation
appears step by step with numbered equations, the verifier agent checks each
step independently, and a Three.js panel shows up with a slider. Takes about
a minute.

**Five commands, the rest is automatic.** The whole user-facing API is
five commands shaped like the arc of doing research: `/start`, `/explore`,
`/work`, `/check`, `/wrap`. Plain language works too. Everything else
(verifier, watcher, domain mentors for physics/math/ml, ~40 methodology
skills) activates automatically when relevant. If you're ever lost, type
`/triptych` — it reads where you are, asks what you're trying to do, and
recommends a next move without auto-deciding for you.

**Ask it to build whatever you want.** Triptych runs Claude Code with
filesystem access to its own source, so if there's a display type or
workspace addon I haven't built, you can just ask Claude to add it while
you're using the tool. If Claude Code can do it, Triptych can do it.

**Heads up — it's not really a study tool.** If you're a student working
through homework you can use it however you want, but you'll probably learn
the material less well than if you struggled through it yourself.

**Free, runs locally, BYO Claude Code install.** It's a personal project —
I'm a physics student and I work on it when I have time.

GitHub: https://github.com/frodo2647/triptych

Would love to hear what you'd want in a tool like this, or if anyone ends
up using it for something real.
```

## Screenshots (optional)

The "Built with Claude" flair invites screenshots/demo but doesn't require them. Posting without is fine — the rough-around-the-edges energy fits a personal-project share. If you do want one, the highest-leverage shot is whiteboard + Claude's formal LaTeX rendering side by side; it tells the "handwritten in, formal math out" story in one frame. Skip the perfectionism — a real session screenshot beats a staged one.

## After you post

- Reply to every top-level comment for at least the first 2 hours
- If someone asks "how is this different from [other tool]" — answer honestly and specifically, not defensively
- If someone asks for a specific feature, either ship it that day if it's small, or add it to an issues list you link back to — both convert skeptics into fans
- Don't cross-link to the HN post; let each community be its own thing

## If the post underperforms

r/ClaudeAI upvotes take a few hours to show direction. Don't judge it for at least 4 hours. If it's still at <10 upvotes by then, the title is probably the issue — rewrite and try again in a week with a different angle (lead with a specific use case instead of the "physics student" framing).
