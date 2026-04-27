# Show HN — ready-to-paste copy

## When to post

Tuesday, Wednesday, or Thursday, **8–10am US Eastern**. Avoid Monday (too much competition after the weekend) and Friday (the front page turns over slowly into the weekend).

## Submission

**URL:** your GitHub repo (not a blog post about it, not a landing page — the repo itself)

**Title** (exact, don't tweak):

```
Show HN: Triptych – A three-panel workspace for hard problems with Claude Code
```

Use the en-dash (`–`), not a hyphen. Keep "Show HN:" with the colon and a space. No marketing words ("revolutionary", "AI-powered", etc.) — HN flags those fast.

Earlier draft was "...turns Claude Code into a research tool." Either works. The current one signals the actual scope (research, derivations, anything where there's no clear metric to optimize) without making "research tool" promises.

## First comment (paste immediately after submitting)

HN convention is that you drop one top-level comment with the backstory right after posting. Don't add other top-level comments after this one — reply in existing threads instead.

```
Hi HN — I'm a physics student, and I built Triptych because I kept wanting
to use Claude Code for the research problems I was working on, not just
coding tasks.

Two things motivated it. The first: Claude Code works well for coding
because the filesystem + compiler close the feedback loop — wrong code
crashes. For a wrong derivation nothing crashes, and a plausible-looking
formula doesn't produce an error. So I kept watching Claude confidently
generate nonsense for problems I cared about, with no way to catch it.

The second: I noticed I learned more from sessions where I argued with
Claude than from sessions where I just took the answer. Asking it to
push back on itself, surfacing what it was assuming, making it justify
something that seemed right — that was where the work actually got
sharper. There's some research kicking around about this being the
difference between people who get smarter using AI and people who atrophy
[1], but mostly it just matched how I wanted to work anyway.

Triptych is three panels connected through the filesystem:

  - Workspace (left): drawing canvas, document/markdown editors, PDF viewer,
    spreadsheet, code editor
  - Display (middle): plots, LaTeX equations, Three.js 3D, step-by-step
    derivations, research state graphs
  - Terminal (right): Claude Code itself

The part I reach for most is the whiteboard. I sketch problems by hand and
Claude reads the canvas directly, so I work through physics the way I
actually think (handwritten, messy) while Claude checks my algebra
mid-derivation and formalizes what I wrote into LaTeX when I'm done. And
because Claude Code is agentic, while I'm deriving something it can be
running a numerical solver, building a simulation, or plotting limiting
cases in parallel — so the next thing I'd ask for is usually already
waiting in the display.

For the back-and-forth piece: an independent agent verifies every
significant claim without seeing Claude's reasoning, using SymPy,
numerical spot-checks, and dimensional analysis. At milestones a second
agent re-derives the result via a different method, and a red-team pass
challenges the conclusion (calibrated to say "nothing substantive" when
the work is sound — an agent that always finds problems is as useless as
one that never does).

If you're optimizing a clear metric — a Kaggle score, a latency budget —
Karpathy's autoresearch is probably the right tool. Triptych is for the
messier stuff in between, where the work is partly figuring out what
counts as the right answer.

There's a tiny user-facing API — five commands shaped like the arc of
doing research: /start (set the goal), /explore (brainstorm), /work
(derive/prove/compute), /check (push back at a milestone), /wrap (close
out). Plain language picks them up too. Everything else (verifier,
watcher, domain mentors, ~40 methodology skills) activates automatically
when relevant — you don't need to remember any of it.

One thing I like: Triptych runs Claude Code with filesystem access to its
own source, so if there's a feature you want that I haven't built, you can
just ask Claude to add it. If Claude Code can do it, Triptych can do it.

Free, runs locally — bring your own Claude Code install. Worth flagging it
isn't really designed as a study tool, so if you're a student working
through homework you can use it however you want, but you'll probably
learn the material less well than struggling through it yourself.

Personal project — happy to answer questions and would love to hear what's
missing.

[1]: https://www.wsj.com/tech/ai/is-ai-smarter-than-humans-cyborg-956e0f0e
```

## After you post

1. **Stick around for 2–3 hours.** This is non-negotiable. The first couple of hours is where the comment value compounds, and disappearing tanks the post.
2. **Reply to every top-level comment**, even the critical ones. Especially the critical ones — HN rewards authors who engage honestly with skeptics.
3. **Don't argue with people who misread the project.** Correct the misreading once, calmly, then move on. Arguing lowers the whole thread.
4. **Don't post follow-up top-level comments from your own account.** Only reply inside existing threads. This is an explicit HN norm and violating it reads as pushy.

## If it flops

HN allows one re-submit after ~24 hours if the first post got zero traction (usually defined as <5 upvotes, no comments). Don't re-submit more than once. If the second one also doesn't catch, the post title or timing isn't the problem — come back in a month with a new feature or a real writeup.

## Common mistakes that tank Show HN posts

- Signup walls or "request access" gates (Triptych has neither — lean into it)
- Marketing language in the title or first comment
- Posting and disappearing
- Claiming the project does more than it does — HN commenters are ruthless about this, and "it's a student project" won't save you
- Arguing with skeptics
- Posting on Monday morning or Friday afternoon
