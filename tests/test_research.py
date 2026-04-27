"""Tests for core/research.py — research state + dependency graph."""

import json
from pathlib import Path

import pytest


# ── Task 1.1: Research state manager ──────────────────────────────


def test_init_research_creates_state_file(research_dir):
    from core.research import init_research

    init_research("Derive EOM for pendulum", research_dir)
    state_file = research_dir / "state.md"
    assert state_file.exists()
    content = state_file.read_text()
    assert "Derive EOM for pendulum" in content


def test_init_research_creates_deps_file(research_dir):
    from core.research import init_research

    init_research("Derive EOM for pendulum", research_dir)
    deps_file = research_dir / "deps.json"
    assert deps_file.exists()
    data = json.loads(deps_file.read_text())
    assert data == {"nodes": {}, "edges": []}


def test_init_research_state_has_all_sections(research_dir):
    from core.research import init_research

    init_research("Test goal", research_dir)
    content = (research_dir / "state.md").read_text()
    for section in ["Goal", "Questions", "Assumptions", "Attempts",
                    "Established Results", "Open Threads", "Next Step"]:
        assert f"## {section}" in content


def test_read_state(research_dir):
    from core.research import init_research, read_state

    init_research("Test goal", research_dir)
    content = read_state(research_dir)
    assert "Test goal" in content
    assert "## Goal" in content


def test_read_state_nonexistent(research_dir):
    from core.research import read_state

    result = read_state(research_dir)
    assert result is None


def test_update_state_goal(research_dir):
    from core.research import init_research, update_state, read_state

    init_research("Old goal", research_dir)
    update_state("goal", "New goal", research_dir)
    content = read_state(research_dir)
    assert "New goal" in content
    assert "Old goal" not in content


def test_update_state_preserves_other_sections(research_dir):
    from core.research import init_research, update_state, read_state

    init_research("My goal", research_dir)
    update_state("questions", "- What is the period?", research_dir)
    content = read_state(research_dir)
    # Goal should still be there
    assert "My goal" in content
    # Questions should be updated
    assert "What is the period?" in content


def test_update_state_each_section(research_dir):
    from core.research import init_research, update_state, read_state

    init_research("Goal", research_dir)
    sections = {
        "questions": "- Q1\n- Q2",
        "assumptions": "- No friction",
        "attempts": "- Tried Lagrangian: worked",
        "established": "- L = T - V (verified)",
        "threads": "- Checking boundary conditions",
        "next": "Compute partial derivatives",
    }
    for key, val in sections.items():
        update_state(key, val, research_dir)

    content = read_state(research_dir)
    for val in sections.values():
        assert val in content


def test_add_attempt(research_dir):
    from core.research import init_research, add_attempt, read_state

    init_research("Goal", research_dir)
    add_attempt("Tried Newtonian approach", "incorrect", "Sign error in forces", research_dir)
    content = read_state(research_dir)
    assert "Tried Newtonian approach" in content
    assert "incorrect" in content
    assert "Sign error in forces" in content


def test_add_attempt_appends(research_dir):
    from core.research import init_research, add_attempt, read_state

    init_research("Goal", research_dir)
    add_attempt("First try", "failed", "Wrong method", research_dir)
    add_attempt("Second try", "partial", "Missing term", research_dir)
    content = read_state(research_dir)
    assert "First try" in content
    assert "Second try" in content


def test_add_established(research_dir):
    from core.research import init_research, add_established, read_state

    init_research("Goal", research_dir)
    add_established("R1", "L = T - V", [], research_dir)
    content = read_state(research_dir)
    assert "L = T - V" in content

    # Should also add to deps.json
    deps = json.loads((research_dir / "deps.json").read_text())
    assert "R1" in deps["nodes"]
    assert deps["nodes"]["R1"]["label"] == "L = T - V"
    assert deps["nodes"]["R1"]["status"] == "verified"


def test_add_established_with_dependencies(research_dir):
    from core.research import init_research, add_node, add_established

    init_research("Goal", research_dir)
    add_node("A1", "assumption", "No friction", "active", research_dir)
    add_established("R1", "L = T - V", ["A1"], research_dir)

    deps = json.loads((research_dir / "deps.json").read_text())
    assert "R1" in deps["nodes"]
    assert {"from": "A1", "to": "R1"} in deps["edges"]


def test_add_observed(research_dir):
    from core.research import init_research, add_observed, read_state

    init_research("Goal", research_dir)
    add_observed("R1", "accuracy = 99.44%", [], research_dir)
    content = read_state(research_dir)
    assert "accuracy = 99.44%" in content
    assert "*(observed)*" in content

    deps = json.loads((research_dir / "deps.json").read_text())
    assert deps["nodes"]["R1"]["status"] == "observed"


def test_add_observed_coexists_with_established(research_dir):
    from core.research import init_research, add_established, add_observed

    init_research("Goal", research_dir)
    add_established("R1", "proven identity", [], research_dir)
    add_observed("R2", "measured constant", [], research_dir)

    deps = json.loads((research_dir / "deps.json").read_text())
    assert deps["nodes"]["R1"]["status"] == "verified"
    assert deps["nodes"]["R2"]["status"] == "observed"


# ── Task 1.2: Dependency graph operations ─────────────────────────


def test_add_node(research_dir):
    from core.research import init_research, add_node, get_graph

    init_research("Goal", research_dir)
    add_node("A1", "assumption", "No friction", "active", research_dir)
    graph = get_graph(research_dir)
    assert "A1" in graph["nodes"]
    assert graph["nodes"]["A1"]["type"] == "assumption"
    assert graph["nodes"]["A1"]["label"] == "No friction"
    assert graph["nodes"]["A1"]["status"] == "active"


def test_add_edge(research_dir):
    from core.research import init_research, add_node, add_edge, get_graph

    init_research("Goal", research_dir)
    add_node("A1", "assumption", "No friction", "active", research_dir)
    add_node("R1", "result", "EOM derived", "verified", research_dir)
    add_edge("A1", "R1", research_dir)

    graph = get_graph(research_dir)
    assert {"from": "A1", "to": "R1"} in graph["edges"]


def test_invalidate_propagates_downstream(research_dir):
    """A -> B -> C: invalidating A should flag B and C."""
    from core.research import (
        init_research, add_node, add_edge, invalidate, get_graph,
    )

    init_research("Goal", research_dir)
    add_node("A1", "assumption", "No friction", "active", research_dir)
    add_node("R1", "result", "Step 1", "verified", research_dir)
    add_node("R2", "result", "Step 2", "verified", research_dir)
    add_edge("A1", "R1", research_dir)
    add_edge("R1", "R2", research_dir)

    invalidate("A1", research_dir)
    graph = get_graph(research_dir)
    assert graph["nodes"]["A1"]["status"] == "invalidated"
    assert graph["nodes"]["R1"]["status"] == "needs-reverification"
    assert graph["nodes"]["R2"]["status"] == "needs-reverification"


def test_invalidate_does_not_affect_upstream(research_dir):
    """Invalidating a downstream node should not affect upstream."""
    from core.research import (
        init_research, add_node, add_edge, invalidate, get_graph,
    )

    init_research("Goal", research_dir)
    add_node("A1", "assumption", "No friction", "active", research_dir)
    add_node("R1", "result", "Step 1", "verified", research_dir)
    add_edge("A1", "R1", research_dir)

    invalidate("R1", research_dir)
    graph = get_graph(research_dir)
    assert graph["nodes"]["A1"]["status"] == "active"  # unchanged
    assert graph["nodes"]["R1"]["status"] == "invalidated"


def test_get_downstream(research_dir):
    """A -> B -> C: downstream of A is {B, C}."""
    from core.research import (
        init_research, add_node, add_edge, get_downstream,
    )

    init_research("Goal", research_dir)
    add_node("A1", "assumption", "No friction", "active", research_dir)
    add_node("R1", "result", "Step 1", "verified", research_dir)
    add_node("R2", "result", "Step 2", "verified", research_dir)
    add_edge("A1", "R1", research_dir)
    add_edge("R1", "R2", research_dir)

    downstream = get_downstream("A1", research_dir)
    assert downstream == {"R1", "R2"}


def test_get_downstream_empty(research_dir):
    from core.research import init_research, add_node, get_downstream

    init_research("Goal", research_dir)
    add_node("A1", "assumption", "No friction", "active", research_dir)
    assert get_downstream("A1", research_dir) == set()


def test_circular_dependency_handled(research_dir):
    """Circular deps shouldn't cause infinite loops."""
    from core.research import (
        init_research, add_node, add_edge, get_downstream, invalidate, get_graph,
    )

    init_research("Goal", research_dir)
    add_node("R1", "result", "Step 1", "verified", research_dir)
    add_node("R2", "result", "Step 2", "verified", research_dir)
    add_edge("R1", "R2", research_dir)
    add_edge("R2", "R1", research_dir)  # circular

    # Should not hang — just return the reachable set
    downstream = get_downstream("R1", research_dir)
    assert "R2" in downstream

    # Invalidation should also not hang
    invalidate("R1", research_dir)
    graph = get_graph(research_dir)
    assert graph["nodes"]["R1"]["status"] == "invalidated"
    assert graph["nodes"]["R2"]["status"] == "needs-reverification"


def test_get_graph_returns_full_structure(research_dir):
    from core.research import init_research, add_node, add_edge, get_graph

    init_research("Goal", research_dir)
    add_node("A1", "assumption", "X", "active", research_dir)
    add_node("R1", "result", "Y", "verified", research_dir)
    add_edge("A1", "R1", research_dir)

    graph = get_graph(research_dir)
    assert "nodes" in graph
    assert "edges" in graph
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1
