# Triptych

*A free, three-panel workspace that turns Claude Code into a tool for solving real problems — not just coding ones.*

> *Heads up: this is a personal project. I'm a physics student, I built it for myself, and I'll keep adding to it when I have time.*

## What it is

Claude Code is amazing for coding because it sits inside a tight feedback loop — filesystem, compiler, terminal — and wrong code crashes. For a wrong derivation, nothing crashes. A plausible-looking formula doesn't produce an error. So I kept watching Claude confidently generate nonsense for problems I actually cared about.

The other thing I noticed: AI is most useful when you push back on it. The times I learned the most were when I argued with Claude, asked it to argue against itself, made it justify something that *seemed* right. Just accepting the answer means you both stop thinking. There's [some research](https://www.wsj.com/tech/ai/is-ai-smarter-than-humans-cyborg-956e0f0e) suggesting this is the difference between people who get sharper using AI and people who atrophy — but mostly it just matched how I actually wanted to work.

Triptych is the workspace I built for that. Three panels connected through the filesystem:

```
┌─────────────┬─────────────┬─────────────┐
│  Workspace  │   Display   │  Terminal   │
│             │             │             │
│  You work   │ Claude shows│ Claude Code │
│  here:      │ its work:   │ runs here   │
│  draw,      │ plots,      │             │
│  write,     │ equations,  │             │
│  annotate   │ derivations │             │
│             │             │             │
└─────────────┴─────────────┴─────────────┘
```

- **Workspace** (left): drawing canvas, document editor, spreadsheet, code editor, markdown, PDF viewer, desktop window watcher
- **Display** (middle): matplotlib, plotly, Three.js, KaTeX, step-by-step derivations, research state graphs
- **Terminal** (right): Claude Code itself, with full filesystem access and a verification pipeline

You can resize the panels however you want — drag the dividers to make the whiteboard bigger, shrink the terminal, or whatever fits the task.

The filesystem is how everything talks. When Claude writes to `workspace/output/`, the display auto-reloads. When you draw something in the workspace, Claude can see it. No database, no plugin registry, no build step. Files all the way down.

## The whiteboard

The thing I reach for most. Sketch a problem by hand — write out a Lagrangian, work through the algebra, draw a free-body diagram — and Claude reads your canvas natively. You can do physics the way you actually think (handwritten, messy) while Claude checks your work in the background, flags a mistake mid-derivation, or formalizes what you wrote into LaTeX when you're done. No transcribing from paper to chat.

Because it runs in your browser, you can open it on a tablet at the same time as your laptop.

## Working in parallel

Because Claude Code is agentic, the live checking isn't the only thing happening in the background. While you're deriving something by hand, it can be running a numerical solver on the equations it's already seen, building a simulation of the system, pulling up a relevant paper, or generating plots of the limiting cases. By the time you finish the algebra, the next thing you would've asked for is usually already sitting in the display.

## Who it's for

Research, hard derivations, data analysis, writing papers — any problem you're actually trying to solve and where the right answer isn't obvious from a number going down. If you have a clear metric to optimize (a Kaggle score, a benchmark, a latency budget), [autoresearch](https://github.com/karpathy/autoresearch) is purpose-built for that and will probably serve you better. Triptych is for the messier stuff in between — deriving, designing, exploring, deciding — where the work is partly figuring out what counts as right.

**Not a study tool.** One thing worth flagging: Triptych isn't really designed as a learning aid. You can use it however you want, but if you lean on it to do your homework, you're probably going to learn the material less well than if you worked through it yourself.

## How to use it

Triptych has five commands shaped like the arc of doing research:

```
/start    Begin a session — set the goal, pick mode
/explore  Generate ideas, survey, hypothesize
/work     Do the work — derive, prove, compute, analyze (verifier on)
/check    Push back at a milestone — challenge assumptions and conclusions
/wrap     Close out — summarize for next session, clean up
```

Mnemonic: **start → explore → work → check → wrap.** That's the whole API. Plain-language phrasing works too — "let's derive X" picks up `/work`, "I'm done for today" picks up `/wrap`. If you're ever unsure where you are or what to do next, type `/triptych` — it reads where you are, asks what you're trying to do, and recommends a next move (without auto-deciding for you).

Everything else (verifier, watcher, domain mentors, dozens of methodology skills) activates automatically when relevant. Power users can call them directly; most of the time you don't need to.

## Quick start

### Option 1: GitHub Codespaces (zero install)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/frodo2647/triptych)

1. Click the button above
2. If you're on API billing, set your `ANTHROPIC_API_KEY` in Codespaces secrets (Settings → Codespaces → Secrets). Subscription users can skip this and run `claude login` inside the terminal instead.
3. Wait for the environment to build (a couple of minutes)
4. Open port 3000 when prompted

### Option 2: Docker (local, no dependency management)

```bash
git clone https://github.com/frodo2647/triptych.git
cd triptych
cp .env.example .env          # only edit if you're on API billing; subscription users can leave it as-is
docker compose up
```

Open `http://localhost:3000`.

### Option 3: Native (if you want to hack on it)

Prerequisites: Node.js 18+, Python 3.10+, [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code). Run `npm run preflight` if you want to verify them automatically.

```bash
git clone https://github.com/frodo2647/triptych.git
cd triptych
npm install
pip install -r requirements.txt
cp .env.example .env          # only edit if you're on API billing; subscription users can leave it as-is
npm run dev
```

Open `http://localhost:3000`.

## What's included

### Workspaces (your panel)

| Workspace | What it does |
|-----------|-------------|
| Document editor | TipTap rich text — headings, tables, task lists, images |
| Spreadsheet | Univer — 450+ formulas, Excel-like UI, dark mode |
| Code editor | CodeMirror 6 with syntax highlighting |
| Markdown | WYSIWYG editor with KaTeX math |
| tldraw | Freeform drawing and whiteboarding |
| PDF viewer | Read and annotate PDFs |
| CircuitJS | Falstad's circuit simulator, with a bridge Claude can drive |
| Window watcher | Watch any desktop window — Claude reads screenshots natively |
| File browser | Navigate, upload, and manage files |

### Displays (Claude's panel)

| Display | What it does |
|---------|-------------|
| matplotlib / plotly | Static and interactive charts |
| KaTeX / LaTeX | Rendered equations |
| Three.js | 3D surfaces, vector fields, parametric curves |
| Derivation | Step-by-step math with numbered equations |
| Research state | Dependency graph of verified results |
| Progress | Live panel showing current step, decisions, and metrics |
| Code / Markdown / HTML | Syntax-highlighted code, rich text, raw HTML |
| Tables | Data tables from lists, dicts, or DataFrames |

### MCP servers (built in)

| Server | What it does |
|--------|-------------|
| sympy-mcp | Symbolic math computation |
| arxiv-latex-mcp | Paper lookup and LaTeX extraction |
| desmos-mcp | Interactive graphing |
| firecrawl | Web search and scraping |
| context7 | Library documentation |
| Hugging Face | Model and dataset search |

## Verification

When Claude makes a significant claim during a derivation, an independent verifier agent checks it using SymPy, Wolfram Alpha, numerical spot-checks, and dimensional analysis. The verifier never sees Claude's reasoning, only the claim — which avoids the rubber-stamping problem where a model "checks" its own work by re-reading its own reasoning.

At milestones, a second agent re-derives the result via a different method. If they converge, confidence is high. If they diverge, both are shown.

There's also a red-team pass for milestones — a separate agent reads the work and tries to challenge it. It's calibrated to return "nothing substantive" when the work is sound rather than inventing issues to seem thorough; an agent that always finds problems is just as useless as one that never does. There's a sister pass that surfaces unstated assumptions and counterfactuals before a result becomes load-bearing.

## Extending it

You're not locked into the features I've built. Triptych runs Claude Code with full filesystem access to its own source, so if you think of something you want — a new display type, a workspace addon, a verification check for a specific domain, even a change to the server — just ask Claude to build it. **If Claude Code can do it, Triptych can do it.**

If you want to build something by hand:

- **New workspace:** Write an HTML file to `workspaces/`. It shows up immediately.
- **New display:** Write a Python module in `displays/`. Import and call from the terminal.
- **New integration:** Write a Python module in `integrations/` that subclasses `EmbeddedTool` (owns an iframe) or `ExternalTool` (links out with a summary panel). CircuitJS and Weights & Biases are the reference implementations.
- **New skill:** Write a `SKILL.md` in `.claude/skills/your-skill/`. Claude loads it on demand.

See `tools.md` for the full addon reference.

## Architecture

Deliberately minimal. ~1000 lines of TypeScript (server), ~800 lines of JavaScript (shell), Python display and integration modules, HTML workspace addons:

- **Express + WebSocket** on port 3000
- **node-pty** for the Claude Code terminal
- **chokidar** watches `workspace/output/` for display auto-reload
- **Filesystem** is the communication channel between every component

No database. No build step. No plugin registry.

## Security

Triptych runs locally on your machine. The server binds to localhost.

**Permissions:** Claude Code runs with `--dangerously-skip-permissions` so the verification pipeline and autonomous skills can work unattended. `.claude/settings.json` ships with an allowlist that auto-approves common operations (python, git, file editing) and denies dangerous patterns (piped remote execution). These rules work on every platform.

**Sandbox (macOS/Linux):** For extra OS-level security, copy `.claude/sandbox.example.json` into `.claude/settings.local.json`. This restricts filesystem writes to the project directory and limits network access to known domains. It uses Apple Seatbelt (macOS) or bubblewrap (Linux) and cannot be bypassed by prompt injection. Native Windows sandboxing is planned but not yet available.

**Trust model:** Same as VS Code with extensions — you installed it, you trust it, it has the same filesystem access you do. To change the behavior, edit `.claude/settings.json` or the spawn args in `server/index.ts`.

## Why

I wanted to sketch physics problems by hand and have Claude actually understand them, without copying anything into a chat. Nothing quite fit, so I built this.

## Contributing

Contributions are welcome, though fair warning: I'm a student and busy, so I can't promise a quick turnaround on reviews — things might sit for a while. Easiest ways to help:

1. **New display addons** — Python modules in `displays/` that generate dark-themed HTML
2. **New workspace addons** — HTML files in `workspaces/` with capture.js integration
3. **Bug reports** — Open an issue with steps to reproduce, OS, and Node/Python versions
4. **Skill improvements** — Better prompting in `.claude/skills/`

```bash
npm test          # TypeScript tests (vitest)
python -m pytest  # Python tests
```

## Credits

Triptych stands on a lot of other people's work:

- **[K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills)** (MIT) — Eight bundled knowledge skills (`scientific-writing`, `scientific-critical-thinking`, `scientific-visualization`, `paper-lookup`, `citation-management`, `peer-review`, `hypothesis-generation`, `sympy`). Vendored in `.claude/skills/`; see `.claude/skills/THIRD_PARTY.md` for attribution.
- **[Karpathy autoresearch](https://github.com/karpathy/autoresearch)** — Inspiration for the `/autoresearch` skill (metric-driven self-improvement loop).
- **[obra/superpowers](https://github.com/obra/superpowers)** (MIT) — Inspiration for the "small core command set, everything else auto-activates" skill design.
- **[Falstad CircuitJS](https://www.falstad.com/circuit/)** — The CircuitJS workspace embeds Paul Falstad's circuit simulator via iframe (no code vendored).
- **Workspace editors** — [tldraw](https://tldraw.dev/) (whiteboard), [TipTap](https://tiptap.dev/) (rich text), [Univer](https://univer.ai/) (spreadsheet), [CodeMirror 6](https://codemirror.net/), [Milkdown](https://milkdown.dev/) (markdown), all loaded from CDN.
- **Display libraries** — matplotlib, plotly, [KaTeX](https://katex.org/), [Three.js](https://threejs.org/), [D3.js](https://d3js.org/), pandas, sympy, scipy, numpy.
- **Server stack** — Express, WebSocket (`ws`), node-pty, chokidar, dotenv, vitest.
- **Hybrid-intelligence research** — The "back-and-forth makes you sharper" framing is informed by [the WSJ piece on the cyborg study](https://www.wsj.com/tech/ai/is-ai-smarter-than-humans-cyborg-956e0f0e) and adjacent MIT cognitive-offloading work.

If I missed crediting something, please open an issue.

## License

MIT
