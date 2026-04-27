"""Research state and dependency graph operations for Triptych v2."""

import json
import re
import time
from pathlib import Path

from core.paths import RESEARCH_DIR as DEFAULT_DIR

# The seven sections of the research state, per PRD
SECTIONS = ["Goal", "Questions", "Assumptions", "Attempts",
            "Established Results", "Open Threads", "Next Step"]

# Map short keys to full section names
SECTION_KEYS = {
    "goal": "Goal",
    "questions": "Questions",
    "assumptions": "Assumptions",
    "attempts": "Attempts",
    "established": "Established Results",
    "threads": "Open Threads",
    "next": "Next Step",
}

STATE_TEMPLATE = """# Research State

## Goal

{goal}

## Questions

*(none yet)*

## Assumptions

*(none yet)*

## Attempts

*(none yet)*

## Established Results

*(none yet)*

## Open Threads

*(none yet)*

## Next Step

*(none yet)*
"""


# ── Research state operations ─────────────────────────────────────


def init_research(goal, research_dir=None):
    """Create state.md with the seven-field template and deps.json with empty graph.

    Also seeds session.json with phase="formalization" so the SessionStart
    hook can surface the active goal on the next session. Call sites
    wanting exploration-phase tracking should use `write_session(goal,
    phase="exploration")` directly and skip init_research.
    """
    from core.session import write_session
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    d.mkdir(parents=True, exist_ok=True)
    (d / "state.md").write_text(STATE_TEMPLATE.format(goal=goal), encoding="utf-8")
    (d / "deps.json").write_text(
        json.dumps({"nodes": {}, "edges": []}, indent=2), encoding="utf-8"
    )
    write_session(goal, phase="formalization", research_dir=d)


def read_state(research_dir=None):
    """Read and return the current state.md content. Returns None if not found."""
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    f = d / "state.md"
    return f.read_text(encoding="utf-8") if f.exists() else None


def update_state(section, content, research_dir=None):
    """Update a specific section of state.md by key name.

    Keys: goal, questions, assumptions, attempts, established, threads, next
    """
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    state = (d / "state.md").read_text(encoding="utf-8")

    heading = SECTION_KEYS.get(section, section)
    # Match from "## Heading\n" to the next "## " or end of file
    pattern = re.compile(
        rf"(## {re.escape(heading)}\n)\n.*?(?=\n## |\Z)",
        re.DOTALL,
    )
    replacement = rf"\1\n{content}"
    state = pattern.sub(replacement, state)
    (d / "state.md").write_text(state, encoding="utf-8")


def _append_to_section(state_path, heading, entry):
    """Append entry to a section, replacing '*(none yet)*' if present."""
    state = state_path.read_text(encoding="utf-8")
    pattern = re.compile(rf"(## {re.escape(heading)}\n)\n(.*?)(?=\n## |\Z)", re.DOTALL)
    match = pattern.search(state)
    if match:
        existing = match.group(2).strip()
        new_content = entry if existing == "*(none yet)*" else existing + "\n" + entry
        state = pattern.sub(rf"\1\n{new_content}", state)
    state_path.write_text(state, encoding="utf-8")


def add_attempt(description, outcome, reason, research_dir=None,
                old_val=None, new_val=None):
    """Append an attempt to the Attempts section.

    Also appends a structured JSON line to `attempts.jsonl` so dashboards
    (e.g. `show_autoresearch`) can read attempt history without scraping
    the rendered markdown.
    """
    from core.session import touch_session
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    d.mkdir(parents=True, exist_ok=True)

    metric_part = ''
    if old_val is not None and new_val is not None:
        metric_part = f' ({old_val} → {new_val})'
    entry = f"- **{description}** — outcome: {outcome}. {reason}{metric_part}"
    _append_to_section(d / "state.md", "Attempts", entry)

    record = {
        "ts": time.time(),
        "description": description,
        "outcome": outcome,
        "reason": reason,
        "old_val": old_val,
        "new_val": new_val,
    }
    with open(d / "attempts.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    touch_session(d)


def read_attempts(research_dir=None):
    """Return the list of structured attempts (oldest first), or [] if none.

    If `attempts.jsonl` is missing (e.g. research dirs created before the
    structured log existed), fall back to parsing the `## Attempts` section of
    `state.md` so dashboards don't silently show an empty history after
    upgrading.
    """
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    f = d / "attempts.jsonl"
    if f.exists():
        return [json.loads(line) for line in f.read_text(encoding="utf-8").splitlines() if line]
    state = d / "state.md"
    if not state.exists():
        return []
    return _parse_attempts_from_state(state.read_text(encoding="utf-8"))


def _parse_attempts_from_state(state_text):
    """Parse bullet-format attempts from a state.md Attempts section.

    Format written by `add_attempt`:
      - **description** — outcome: kept. reason (old_val → new_val)
    The metric suffix is optional.
    """
    m = re.search(r"## Attempts\s*\n(.*?)(?=\n## |\Z)", state_text, re.DOTALL)
    if not m:
        return []
    body = m.group(1).strip()
    if not body or body == "*(none yet)*":
        return []
    bullet_re = re.compile(
        r"^-\s+\*\*(?P<desc>.+?)\*\*\s+[—-]\s+outcome:\s+(?P<outcome>\w+)\.\s*"
        r"(?P<reason>.*?)"
        r"(?:\s+\((?P<old>[-0-9.eE+]+)\s*→\s*(?P<new>[-0-9.eE+]+)\))?\s*$"
    )
    attempts = []
    for line in body.splitlines():
        line = line.rstrip()
        if not line.startswith("-"):
            continue
        bm = bullet_re.match(line)
        if not bm:
            continue
        def _num(s):
            if s is None:
                return None
            try:
                return float(s)
            except ValueError:
                return None
        attempts.append({
            "ts": None,
            "description": bm.group("desc"),
            "outcome": bm.group("outcome"),
            "reason": bm.group("reason").strip(),
            "old_val": _num(bm.group("old")),
            "new_val": _num(bm.group("new")),
        })
    return attempts


def add_established(id, label, depends_on, research_dir=None):
    """Add a formally verified result to Established Results AND deps.json.

    Use this when the verifier has signed off — i.e. a corresponding result
    entry exists in verification.log. For empirical results confident from
    measurement but not formally verified, use `add_observed()` instead.
    """
    from core.session import touch_session
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    _append_to_section(d / "state.md", "Established Results", f"- [{id}] {label}")
    add_node(id, "result", label, "verified", d)
    for dep_id in depends_on:
        add_edge(dep_id, id, d)
    touch_session(d)


def add_observed(id, label, depends_on, research_dir=None):
    """Add an empirically observed result (not formally verified).

    Use for results you're confident about from measurement or direct
    observation — training metrics, experimental readings, literature
    consensus — but that haven't been checked by the verifier loop. Both
    `add_observed` and `add_established` land in the Established Results
    section; the node status in deps.json distinguishes them (`observed`
    vs `verified`), which lets displays render them distinctly.
    """
    from core.session import touch_session
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    _append_to_section(d / "state.md", "Established Results", f"- [{id}] {label} *(observed)*")
    add_node(id, "result", label, "observed", d)
    for dep_id in depends_on:
        add_edge(dep_id, id, d)
    touch_session(d)


def add_thread(id, label, depends_on, research_dir=None):
    """Add an unverified result to Open Threads AND deps.json."""
    from core.session import touch_session
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    _append_to_section(d / "state.md", "Open Threads", f"- [{id}] {label} *(unverified)*")
    add_node(id, "result", label, "unverified", d)
    for dep_id in depends_on:
        add_edge(dep_id, id, d)
    touch_session(d)


# ── Dependency graph operations ───────────────────────────────────


def _read_graph(research_dir):
    """Read deps.json and return the graph dict."""
    f = Path(research_dir) / "deps.json"
    return json.loads(f.read_text())


def _write_graph(graph, research_dir):
    """Write graph dict to deps.json."""
    f = Path(research_dir) / "deps.json"
    f.write_text(json.dumps(graph, indent=2))


def add_node(id, type, label, status, research_dir=None):
    """Add a node to deps.json."""
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    graph = _read_graph(d)
    graph["nodes"][id] = {"type": type, "label": label, "status": status}
    _write_graph(graph, d)


def add_edge(from_id, to_id, research_dir=None):
    """Add a directed edge to deps.json."""
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    graph = _read_graph(d)
    edge = {"from": from_id, "to": to_id}
    if edge not in graph["edges"]:
        graph["edges"].append(edge)
    _write_graph(graph, d)


def get_graph(research_dir=None):
    """Return the full graph object from deps.json."""
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    return _read_graph(d)


def get_downstream(node_id, research_dir=None):
    """Return all nodes that depend (directly or transitively) on the given node.

    Returns a set of node IDs. Handles circular dependencies gracefully.
    """
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    graph = _read_graph(d)

    # Build adjacency list: from_id -> [to_id, ...]
    adj = {}
    for edge in graph["edges"]:
        adj.setdefault(edge["from"], []).append(edge["to"])

    # BFS to find all downstream nodes
    visited = set()
    queue = list(adj.get(node_id, []))
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        queue.extend(adj.get(current, []))

    return visited


def invalidate(node_id, research_dir=None):
    """Set node to 'invalidated', propagate 'needs-reverification' downstream."""
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    graph = _read_graph(d)

    graph["nodes"][node_id]["status"] = "invalidated"

    downstream = get_downstream(node_id, d)
    for nid in downstream:
        if nid != node_id:  # don't overwrite the source node in circular graphs
            graph["nodes"][nid]["status"] = "needs-reverification"

    _write_graph(graph, d)


# ── Watcher log operations ────────────────────────────────────────


def log_watcher(content, entry_type="observation", confidence="medium", research_dir=None):
    """Append an entry to the watcher log (JSONL).

    Types: observation, error, idea, background-check, transition
    """
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    d.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": time.time(),
        "type": entry_type,
        "content": content,
        "confidence": confidence,
    }
    with open(d / "watcher.log", "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_watcher_log(research_dir=None):
    """Read the watcher log. Returns list of dicts."""
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    log = d / "watcher.log"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().strip().split("\n") if line]
