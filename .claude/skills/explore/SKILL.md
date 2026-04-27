---
name: explore
description: Brainstorming and ideation mode — generate hypotheses, survey landscapes, draw connections, identify what's worth working on. Second of five core commands (start → explore → work → check → wrap). Use when the goal is "figure out what to ask" rather than "answer this specific thing." Pulls in /hypothesis-generation, /literature-review, /think-rigorously naturally.
---

# /explore

The "what should we even be asking" mode. Different from `/work` in that there's no specific claim to verify yet — the output is a sharper question, not a verified result.

## When to use

- Right after `/start` if the goal is open-ended ("what's interesting in X?")
- When `/work` hits a dead end and the framing needs to be re-examined
- When the user types "explore" / "brainstorm" / "what could we do about X?"

## Step 1: Set the phase

If session phase is not already exploration, set it:

```python
import sys; sys.path.insert(0, '.')
from core.session import write_session
s = read_session()
write_session(s['goal'], phase='exploration')
```

Don't seed research state yet — that's a formalization boundary.

## Step 2: Surface the question

What are we actually exploring? If `/explore` was called with args (`/explore <topic>`), use them. Otherwise pull the goal from session state and ask: *"What's the angle? Generating hypotheses, surveying prior work, looking for connections, or just thinking out loud?"*

The four sub-modes have different shapes:

| Sub-mode | Wraps | Behavior |
|---|---|---|
| **Generate hypotheses** | `/hypothesis-generation` | 8-step structured ideation — produces 3-5 competing hypotheses with mechanisms |
| **Survey literature** | `/literature-review`, `/paper-lookup` | Search, extract claims, build annotated bibliography, identify gaps |
| **Connect ideas** | `/think-rigorously` (exploration mode), domain mentor | Suggest analogies, related problems, alternative framings |
| **Think out loud** | Free form, watcher logs observations | Conversational; agent surfaces patterns, asks Socratic questions |

If unclear, just pick "think out loud" — it's the lowest-commitment mode.

## Step 3: Stay generative, not verificatory

During exploration:

- **Don't** emit claims (`emit_claim`) — there's nothing to verify yet.
- **Do** log ideas, framings, connections, candidate hypotheses to a live `show_progress` panel so the human can see what's accumulating.
- **Do** catch obvious errors (2+2=5 is always wrong, even in exploration) — but don't run formal verification.
- **Do** suggest related work, analogies, alternative approaches the user might not have considered.

```python
from displays import show_progress
show_progress(
    goal=session_goal,
    decisions=['Looking at <X>', 'Considering <Y> framing'],
    name='explore',
)
```

Update the panel as the conversation moves.

## Step 4: Track candidate questions

As specific testable questions emerge from the exploration, list them. The point of `/explore` is to *narrow* — at the end, there should be a candidate goal worth formalizing.

Add them to the live progress panel under decisions, or use `add_observed` if a candidate is solid enough:

```python
from core.research import add_observed
add_observed('Q1', 'Candidate question: <text>', depends_on=[])
```

## Step 5: Crystallize and hand off

When the exploration has produced something concrete, ask:

*"Ready to crystallize? It looks like the question is `<X>`. Want to /work on that, keep exploring, or save it for next time?"*

If the user says yes: invoke `/work <crystallized goal>`. The transition seeds research state and activates the verifier.

If the user wants to keep exploring: stay in this mode.

If the user wants to save it: write the candidate to "Open Threads" via `add_thread` or to session.json so next `/start` resumes warmly.

## Args

- `/explore` — interactive flow.
- `/explore <topic>` — starts with a specific topic in mind.

## Hard rules

- **Never seed research state in exploration mode.** That boundary is the agent's job to recognize.
- **No formal verification.** Claims and `/verifier` are for `/work`. Exploration is generative.
- **Watch for the crystallization signal.** When the user says "let's prove that," "let me derive," "I want to formalize" — that's the cue to suggest `/work`.
- **Don't keep exploring forever.** If 30+ minutes go by without a candidate question, surface it: *"We've covered a lot — anything here you want to commit to, or is it useful to keep wandering?"*
