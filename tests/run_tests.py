"""Run tests without pytest (workaround for pytest hanging on this system).

Usage: python tests/run_tests.py
"""

import sys
import json
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

PASSED = 0
FAILED = 0
ERRORS = []


def run_test(name, fn):
    global PASSED, FAILED
    try:
        d = Path(tempfile.mkdtemp()) / "research"
        d.mkdir()
        fn(d)
        PASSED += 1
        print(f"  PASS  {name}")
    except Exception as e:
        FAILED += 1
        ERRORS.append((name, e))
        print(f"  FAIL  {name}: {e}")


# ── Task 1.1: Research state manager ──────────────────────────────

def test_init_creates_state(d):
    from core.research import init_research
    init_research("Derive EOM for pendulum", d)
    assert (d / "state.md").exists()
    assert "Derive EOM for pendulum" in (d / "state.md").read_text()

def test_init_creates_deps(d):
    from core.research import init_research
    init_research("Derive EOM for pendulum", d)
    assert (d / "deps.json").exists()
    assert json.loads((d / "deps.json").read_text()) == {"nodes": {}, "edges": []}

def test_init_has_all_sections(d):
    from core.research import init_research
    init_research("Test goal", d)
    content = (d / "state.md").read_text()
    for section in ["Goal", "Questions", "Assumptions", "Attempts",
                    "Established Results", "Open Threads", "Next Step"]:
        assert f"## {section}" in content, f"Missing section: {section}"

def test_read_state(d):
    from core.research import init_research, read_state
    init_research("Test goal", d)
    content = read_state(d)
    assert "Test goal" in content
    assert "## Goal" in content

def test_read_state_nonexistent(d):
    from core.research import read_state
    assert read_state(d) is None

def test_update_state_goal(d):
    from core.research import init_research, update_state, read_state
    init_research("Old goal", d)
    update_state("goal", "New goal", d)
    content = read_state(d)
    assert "New goal" in content
    assert "Old goal" not in content

def test_update_preserves_other_sections(d):
    from core.research import init_research, update_state, read_state
    init_research("My goal", d)
    update_state("questions", "- What is the period?", d)
    content = read_state(d)
    assert "My goal" in content
    assert "What is the period?" in content

def test_update_each_section(d):
    from core.research import init_research, update_state, read_state
    init_research("Goal", d)
    sections = {
        "questions": "- Q1\n- Q2",
        "assumptions": "- No friction",
        "attempts": "- Tried Lagrangian: worked",
        "established": "- L = T - V (verified)",
        "threads": "- Checking boundary conditions",
        "next": "Compute partial derivatives",
    }
    for key, val in sections.items():
        update_state(key, val, d)
    content = read_state(d)
    for val in sections.values():
        assert val in content, f"Missing: {val}"

def test_add_attempt(d):
    from core.research import init_research, add_attempt, read_state
    init_research("Goal", d)
    add_attempt("Tried Newtonian approach", "incorrect", "Sign error in forces", d)
    content = read_state(d)
    assert "Tried Newtonian approach" in content
    assert "incorrect" in content
    assert "Sign error in forces" in content

def test_add_attempt_appends(d):
    from core.research import init_research, add_attempt, read_state
    init_research("Goal", d)
    add_attempt("First try", "failed", "Wrong method", d)
    add_attempt("Second try", "partial", "Missing term", d)
    content = read_state(d)
    assert "First try" in content
    assert "Second try" in content

def test_add_established(d):
    from core.research import init_research, add_established, read_state
    init_research("Goal", d)
    add_established("R1", "L = T - V", [], d)
    content = read_state(d)
    assert "L = T - V" in content
    deps = json.loads((d / "deps.json").read_text())
    assert "R1" in deps["nodes"]
    assert deps["nodes"]["R1"]["label"] == "L = T - V"
    assert deps["nodes"]["R1"]["status"] == "verified"

def test_add_established_with_deps(d):
    from core.research import init_research, add_node, add_established
    init_research("Goal", d)
    add_node("A1", "assumption", "No friction", "active", d)
    add_established("R1", "L = T - V", ["A1"], d)
    deps = json.loads((d / "deps.json").read_text())
    assert "R1" in deps["nodes"]
    assert {"from": "A1", "to": "R1"} in deps["edges"]

def test_add_observed(d):
    from core.research import init_research, add_observed, read_state
    init_research("Goal", d)
    add_observed("R1", "accuracy = 99.44%", [], d)
    content = read_state(d)
    assert "accuracy = 99.44%" in content
    assert "*(observed)*" in content
    deps = json.loads((d / "deps.json").read_text())
    assert deps["nodes"]["R1"]["status"] == "observed"

def test_add_observed_coexists_with_established(d):
    from core.research import init_research, add_established, add_observed
    init_research("Goal", d)
    add_established("R1", "proven identity", [], d)
    add_observed("R2", "measured constant", [], d)
    deps = json.loads((d / "deps.json").read_text())
    assert deps["nodes"]["R1"]["status"] == "verified"
    assert deps["nodes"]["R2"]["status"] == "observed"

# ── Task 1.2: Dependency graph operations ─────────────────────────

def test_add_node(d):
    from core.research import init_research, add_node, get_graph
    init_research("Goal", d)
    add_node("A1", "assumption", "No friction", "active", d)
    graph = get_graph(d)
    assert "A1" in graph["nodes"]
    assert graph["nodes"]["A1"]["type"] == "assumption"
    assert graph["nodes"]["A1"]["label"] == "No friction"
    assert graph["nodes"]["A1"]["status"] == "active"

def test_add_edge(d):
    from core.research import init_research, add_node, add_edge, get_graph
    init_research("Goal", d)
    add_node("A1", "assumption", "No friction", "active", d)
    add_node("R1", "result", "EOM derived", "verified", d)
    add_edge("A1", "R1", d)
    graph = get_graph(d)
    assert {"from": "A1", "to": "R1"} in graph["edges"]

def test_invalidate_propagates(d):
    from core.research import init_research, add_node, add_edge, invalidate, get_graph
    init_research("Goal", d)
    add_node("A1", "assumption", "No friction", "active", d)
    add_node("R1", "result", "Step 1", "verified", d)
    add_node("R2", "result", "Step 2", "verified", d)
    add_edge("A1", "R1", d)
    add_edge("R1", "R2", d)
    invalidate("A1", d)
    graph = get_graph(d)
    assert graph["nodes"]["A1"]["status"] == "invalidated"
    assert graph["nodes"]["R1"]["status"] == "needs-reverification"
    assert graph["nodes"]["R2"]["status"] == "needs-reverification"

def test_invalidate_no_upstream(d):
    from core.research import init_research, add_node, add_edge, invalidate, get_graph
    init_research("Goal", d)
    add_node("A1", "assumption", "No friction", "active", d)
    add_node("R1", "result", "Step 1", "verified", d)
    add_edge("A1", "R1", d)
    invalidate("R1", d)
    graph = get_graph(d)
    assert graph["nodes"]["A1"]["status"] == "active"
    assert graph["nodes"]["R1"]["status"] == "invalidated"

def test_get_downstream(d):
    from core.research import init_research, add_node, add_edge, get_downstream
    init_research("Goal", d)
    add_node("A1", "assumption", "No friction", "active", d)
    add_node("R1", "result", "Step 1", "verified", d)
    add_node("R2", "result", "Step 2", "verified", d)
    add_edge("A1", "R1", d)
    add_edge("R1", "R2", d)
    assert get_downstream("A1", d) == {"R1", "R2"}

def test_get_downstream_empty(d):
    from core.research import init_research, add_node, get_downstream
    init_research("Goal", d)
    add_node("A1", "assumption", "No friction", "active", d)
    assert get_downstream("A1", d) == set()

def test_circular_dependency(d):
    from core.research import init_research, add_node, add_edge, get_downstream, invalidate, get_graph
    init_research("Goal", d)
    add_node("R1", "result", "Step 1", "verified", d)
    add_node("R2", "result", "Step 2", "verified", d)
    add_edge("R1", "R2", d)
    add_edge("R2", "R1", d)
    assert "R2" in get_downstream("R1", d)
    invalidate("R1", d)
    graph = get_graph(d)
    assert graph["nodes"]["R1"]["status"] == "invalidated"
    assert graph["nodes"]["R2"]["status"] == "needs-reverification"

def test_get_graph_full(d):
    from core.research import init_research, add_node, add_edge, get_graph
    init_research("Goal", d)
    add_node("A1", "assumption", "X", "active", d)
    add_node("R1", "result", "Y", "verified", d)
    add_edge("A1", "R1", d)
    graph = get_graph(d)
    assert "nodes" in graph and "edges" in graph
    assert len(graph["nodes"]) == 2
    assert len(graph["edges"]) == 1


# ── Task 1.3: Research display addon ──────────────────────────────

def test_show_research_produces_html(d):
    from core.research import init_research
    from displays.research import show_research
    init_research("Test goal", d)
    out = d / "output"
    show_research(research_dir=d, output_dir=out)
    html_file = out / "research.html"
    assert html_file.exists()
    content = html_file.read_text()
    assert "<!DOCTYPE html>" in content
    assert "Test goal" in content

def test_show_research_has_graph_with_nodes(d):
    from core.research import init_research, add_node, add_edge
    from displays.research import show_research
    init_research("Test", d)
    add_node("A1", "assumption", "No friction", "active", d)
    add_node("R1", "result", "EOM", "verified", d)
    add_edge("A1", "R1", d)
    out = d / "output"
    show_research(research_dir=d, output_dir=out)
    content = (out / "research.html").read_text()
    assert '"A1"' in content
    assert '"R1"' in content
    assert "No friction" in content

def test_show_research_status_colors(d):
    from core.research import init_research, add_node
    from displays.research import show_research, STATUS_COLORS
    init_research("Test", d)
    add_node("A1", "assumption", "X", "active", d)
    add_node("R1", "result", "Y", "verified", d)
    add_node("R2", "result", "Z", "invalidated", d)
    out = d / "output"
    show_research(research_dir=d, output_dir=out)
    content = (out / "research.html").read_text()
    for color in STATUS_COLORS.values():
        assert color in content

def test_show_research_no_state(d):
    from displays.research import show_research
    out = d / "output"
    show_research(research_dir=d, output_dir=out)
    content = (out / "research.html").read_text()
    assert "No research state initialized" in content


# ── Task 2.1: Verification system ─────────────────────────────────

def test_emit_claim(d):
    from core.verify import emit_claim, read_log
    cid = emit_claim("x^2 derivative is 2x", "differentiation of x^2", research_dir=d)
    assert cid.startswith("C")
    log = read_log(d)
    assert len(log) == 1
    assert log[0]["type"] == "claim"
    assert log[0]["claim"] == "x^2 derivative is 2x"
    assert log[0]["id"] == cid

def test_emit_claim_appends(d):
    from core.verify import emit_claim, read_log
    emit_claim("claim 1", "ctx 1", research_dir=d)
    emit_claim("claim 2", "ctx 2", research_dir=d)
    log = read_log(d)
    assert len(log) == 2
    assert log[0]["claim"] == "claim 1"
    assert log[1]["claim"] == "claim 2"

def test_emit_claim_with_depends(d):
    from core.verify import emit_claim, read_log
    emit_claim("claim 1", "ctx", depends=["A1", "R1"], research_dir=d)
    log = read_log(d)
    assert log[0]["depends"] == ["A1", "R1"]

def test_write_result(d):
    from core.verify import emit_claim, write_result, read_log
    cid = emit_claim("2+2=4", "arithmetic", research_dir=d)
    write_result(cid, "verified", "numerical", "confirmed", research_dir=d)
    log = read_log(d)
    assert len(log) == 2
    result = log[1]
    assert result["type"] == "result"
    assert result["claimId"] == cid
    assert result["status"] == "verified"

def test_write_flag(d):
    from core.verify import write_flag, read_log
    write_flag("missing-claim", "new equations without claims", research_dir=d)
    log = read_log(d)
    assert len(log) == 1
    assert log[0]["type"] == "flag"
    assert log[0]["kind"] == "missing-claim"

def test_read_verification_results_unread(d):
    import time
    from core.verify import emit_claim, write_result, read_verification_results
    cid = emit_claim("claim", "ctx", research_dir=d)
    time.sleep(0.01)
    write_result(cid, "verified", "sympy", "ok", research_dir=d)
    results = read_verification_results(d)
    assert len(results) == 1
    assert results[0]["status"] == "verified"

def test_clear_results(d):
    import time
    from core.verify import emit_claim, write_result, read_verification_results, clear_results
    cid = emit_claim("claim", "ctx", research_dir=d)
    time.sleep(0.01)
    write_result(cid, "verified", "sympy", "ok", research_dir=d)
    clear_results(d)
    time.sleep(0.01)
    results = read_verification_results(d)
    assert len(results) == 0

def test_clear_then_new_results(d):
    import time
    from core.verify import emit_claim, write_result, read_verification_results, clear_results
    cid1 = emit_claim("claim 1", "ctx", research_dir=d)
    time.sleep(0.01)
    write_result(cid1, "verified", "sympy", "ok", research_dir=d)
    clear_results(d)
    time.sleep(0.01)
    cid2 = emit_claim("claim 2", "ctx", research_dir=d)
    time.sleep(0.01)
    write_result(cid2, "failed", "numerical", "mismatch", research_dir=d)
    results = read_verification_results(d)
    assert len(results) == 1
    assert results[0]["claimId"] == cid2

def test_jsonl_format(d):
    from core.verify import emit_claim, write_result
    cid = emit_claim("test", "ctx", research_dir=d)
    write_result(cid, "verified", "manual", "ok", research_dir=d)
    # Each line should be valid JSON
    log_path = d / "verification.log"
    lines = log_path.read_text().strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        parsed = json.loads(line)
        assert "type" in parsed
        assert "timestamp" in parsed

def test_read_log_empty(d):
    from core.verify import read_log
    assert read_log(d) == []

# ── Task 2.4: Verification → research state wiring ───────────────

def test_verified_claim_flows_to_state(d):
    from core.research import init_research, read_state, get_graph
    from core.verify import emit_claim, write_result
    from core.verify import process_result
    init_research("Goal", d)
    cid = emit_claim("L = T - V", "Lagrangian definition", depends=["A1"], research_dir=d)
    write_result(cid, "verified", "sympy", "confirmed", research_dir=d)
    process_result(cid, "verified", "L = T - V", ["A1"], d)
    state = read_state(d)
    assert "L = T - V" in state
    graph = get_graph(d)
    assert cid in graph["nodes"]
    assert graph["nodes"][cid]["status"] == "verified"

def test_failed_claim_goes_to_attempts(d):
    from core.research import init_research, read_state, get_graph
    from core.verify import emit_claim, write_result
    from core.verify import process_result
    init_research("Goal", d)
    cid = emit_claim("d/dx(x^2) = 3x", "differentiation", research_dir=d)
    write_result(cid, "failed", "sympy", "should be 2x", research_dir=d)
    process_result(cid, "failed", "d/dx(x^2) = 3x", [], d)
    state = read_state(d)
    assert "d/dx(x^2) = 3x" in state
    assert "failed" in state
    graph = get_graph(d)
    assert cid not in graph["nodes"]

def test_uncertain_claim_to_threads(d):
    from core.research import init_research, read_state, get_graph
    from core.verify import emit_claim, write_result
    from core.verify import process_result
    init_research("Goal", d)
    cid = emit_claim("convergence holds", "limit argument", research_dir=d)
    write_result(cid, "uncertain", "reasoning", "hard to verify", research_dir=d)
    process_result(cid, "uncertain", "convergence holds", [], d)
    state = read_state(d)
    assert "convergence holds" in state
    graph = get_graph(d)
    assert cid in graph["nodes"]
    assert graph["nodes"][cid]["status"] == "unverified"


# ── Task 3: Watcher system ────────────────────────────────────────

def test_log_watcher(d):
    from core.research import log_watcher, read_watcher_log
    log_watcher("Noticed sign error in line 3", "error", "high", d)
    entries = read_watcher_log(d)
    assert len(entries) == 1
    assert entries[0]["type"] == "error"
    assert entries[0]["content"] == "Noticed sign error in line 3"
    assert entries[0]["confidence"] == "high"
    assert "timestamp" in entries[0]

def test_log_watcher_appends(d):
    from core.research import log_watcher, read_watcher_log
    log_watcher("First observation", "observation", "medium", d)
    log_watcher("Second observation", "idea", "low", d)
    entries = read_watcher_log(d)
    assert len(entries) == 2
    assert entries[0]["type"] == "observation"
    assert entries[1]["type"] == "idea"

def test_read_watcher_log_empty(d):
    from core.research import read_watcher_log
    assert read_watcher_log(d) == []

def test_watcher_transition_triggers_init(d):
    """When watcher detects transition, it should log and init research state."""
    from core.research import log_watcher, read_watcher_log, init_research, read_state
    # Simulate: watcher detects transition, logs it, inits research state
    log_watcher("Equations appearing - transitioning to formalization", "transition", "high", d)
    init_research("Derive equation of motion for pendulum", d)
    entries = read_watcher_log(d)
    assert any(e["type"] == "transition" for e in entries)
    state = read_state(d)
    assert "Derive equation of motion" in state

def test_watcher_log_jsonl_format(d):
    from core.research import log_watcher
    log_watcher("test entry", "observation", "medium", d)
    log_path = d / "watcher.log"
    lines = log_path.read_text().strip().split("\n")
    for line in lines:
        parsed = json.loads(line)
        assert "timestamp" in parsed
        assert "type" in parsed


# ── Task 5.1: Edge cases ──────────────────────────────────────────

def test_assumption_invalidation_end_to_end(d):
    """Full flow: build derivation chain, invalidate assumption, verify propagation."""
    from core.research import init_research, add_node, add_edge, invalidate, get_graph
    from core.verify import emit_claim, process_result
    init_research("Test derivation", d)
    # Build: A1 -> R1 -> R2
    add_node("A1", "assumption", "No friction", "active", d)
    process_result("R1", "verified", "T = 1/2 mv^2", ["A1"], d)
    process_result("R2", "verified", "E = T + V", ["R1"], d)
    # Invalidate the assumption
    invalidate("A1", d)
    graph = get_graph(d)
    assert graph["nodes"]["A1"]["status"] == "invalidated"
    assert graph["nodes"]["R1"]["status"] == "needs-reverification"
    assert graph["nodes"]["R2"]["status"] == "needs-reverification"

def test_process_result_no_state_file(d):
    """process_result should handle missing state.md gracefully by creating it via init."""
    from core.research import init_research
    from core.verify import process_result
    # Init first (process_result expects state.md to exist)
    init_research("Goal", d)
    # This should work without error
    process_result("C1", "verified", "2+2=4", [], d)

def test_read_state_before_init(d):
    """read_state returns None when state doesn't exist."""
    from core.research import read_state
    assert read_state(d) is None

def test_read_log_before_init(d):
    """read_log returns empty list when log doesn't exist."""
    from core.verify import read_log
    assert read_log(d) == []

def test_emit_claim_creates_dir(d):
    """emit_claim should create the research dir if it doesn't exist."""
    import shutil
    from core.verify import emit_claim
    sub = d / "nested" / "research"
    cid = emit_claim("test", "ctx", research_dir=sub)
    assert cid.startswith("C")
    assert (sub / "verification.log").exists()

def test_show_research_empty_graph(d):
    """show_research renders cleanly when graph has no nodes."""
    from core.research import init_research
    from displays.research import show_research
    init_research("Empty test", d)
    out = d / "output"
    show_research(research_dir=d, output_dir=out)
    content = (out / "research.html").read_text()
    assert "Empty test" in content
    # Graph section should be hidden
    assert 'display: none' in content

def test_multiple_failures_dont_corrupt(d):
    """Multiple failed claims should all appear in attempts without corrupting state."""
    from core.research import init_research, read_state
    from core.verify import process_result
    init_research("Goal", d)
    for i in range(5):
        process_result(f"C{i}", "failed", f"wrong claim {i}", [], d)
    state = read_state(d)
    for i in range(5):
        assert f"wrong claim {i}" in state


# ── Session persistence (core/session.py) ─────────────────────────

def test_session_read_before_write_is_none(d):
    from core.session import read_session
    assert read_session(d) is None

def test_session_write_read_roundtrip(d):
    from core.session import write_session, read_session
    write_session("Lorentz transforms", "formalization", research_dir=d)
    s = read_session(d)
    assert s["goal"] == "Lorentz transforms"
    assert s["phase"] == "formalization"
    assert s["mode"] == "single-agent"
    assert s["setAt"] == s["lastActive"]

def test_session_exploration_phase(d):
    from core.session import write_session, read_session
    write_session("poke at chaos", "exploration", research_dir=d)
    assert read_session(d)["phase"] == "exploration"

def test_session_invalid_phase_raises(d):
    from core.session import write_session
    try:
        write_session("goal", "bogus", research_dir=d)
    except ValueError:
        return
    raise AssertionError("expected ValueError for invalid phase")

def test_session_touch_refreshes_lastActive(d):
    import time
    from core.session import write_session, touch_session, read_session
    write_session("goal", "formalization", research_dir=d)
    first = read_session(d)["lastActive"]
    time.sleep(1.1)  # _now_iso granularity is 1 second
    touch_session(d)
    second = read_session(d)["lastActive"]
    assert second > first, f"lastActive should advance: {first} -> {second}"

def test_session_touch_no_session_is_noop(d):
    from core.session import touch_session
    assert touch_session(d) is None  # no session file -> silent None

def test_init_research_seeds_session(d):
    from core.research import init_research
    from core.session import read_session
    init_research("derive something", d)
    s = read_session(d)
    assert s is not None
    assert s["goal"] == "derive something"
    assert s["phase"] == "formalization"

def test_add_established_touches_session(d):
    import time
    from core.research import init_research, add_established
    from core.session import read_session
    init_research("g", d)
    first = read_session(d)["lastActive"]
    time.sleep(1.1)
    add_established("R1", "proven thing", [], d)
    second = read_session(d)["lastActive"]
    assert second > first

def test_clear_session_removes_file(d):
    from core.session import write_session, clear_session, read_session
    write_session("g", "exploration", research_dir=d)
    assert read_session(d) is not None
    clear_session(d)
    assert read_session(d) is None


# ── Dashboard queue (core/dashboard_queue.py) ─────────────────────

def test_dashboard_queue_empty_initial(d):
    from core.dashboard_queue import pending_count, drain_requests
    assert pending_count(d) == 0
    assert drain_requests(d) == []

def test_dashboard_queue_roundtrip(d):
    from core.dashboard_queue import request_display, drain_requests, mark_done, pending_count
    id1 = request_display("training-curve", "workspace/files/runs/", research_dir=d)
    id2 = request_display("architecture graph", research_dir=d)
    assert pending_count(d) == 2
    reqs = drain_requests(d)
    assert len(reqs) == 2
    assert reqs[0]["id"] == id1
    assert reqs[0]["intent"] == "training-curve"
    assert reqs[0]["data_path"] == "workspace/files/runs/"
    assert reqs[1]["id"] == id2
    assert pending_count(d) == 0  # drain empties pending
    mark_done(id1, "workspace/output/training-curve.html", research_dir=d)
    import json
    data = json.loads((d / "dashboard-queue.json").read_text())
    assert len(data["completed"]) == 1
    assert data["completed"][0]["id"] == id1


if __name__ == "__main__":
    print("\n=== Research State Tests (Task 1.1) ===\n")
    for name, fn in [
        ("init_creates_state", test_init_creates_state),
        ("init_creates_deps", test_init_creates_deps),
        ("init_has_all_sections", test_init_has_all_sections),
        ("read_state", test_read_state),
        ("read_state_nonexistent", test_read_state_nonexistent),
        ("update_state_goal", test_update_state_goal),
        ("update_preserves_other", test_update_preserves_other_sections),
        ("update_each_section", test_update_each_section),
        ("add_attempt", test_add_attempt),
        ("add_attempt_appends", test_add_attempt_appends),
        ("add_established", test_add_established),
        ("add_established_with_deps", test_add_established_with_deps),
        ("add_observed", test_add_observed),
        ("add_observed_coexists_with_established", test_add_observed_coexists_with_established),
    ]:
        run_test(name, fn)

    print("\n=== Dependency Graph Tests (Task 1.2) ===\n")
    for name, fn in [
        ("add_node", test_add_node),
        ("add_edge", test_add_edge),
        ("invalidate_propagates", test_invalidate_propagates),
        ("invalidate_no_upstream", test_invalidate_no_upstream),
        ("get_downstream", test_get_downstream),
        ("get_downstream_empty", test_get_downstream_empty),
        ("circular_dependency", test_circular_dependency),
        ("get_graph_full", test_get_graph_full),
    ]:
        run_test(name, fn)

    print("\n=== Research Display Tests (Task 1.3) ===\n")
    for name, fn in [
        ("show_research_produces_html", test_show_research_produces_html),
        ("show_research_has_graph", test_show_research_has_graph_with_nodes),
        ("show_research_status_colors", test_show_research_status_colors),
        ("show_research_no_state", test_show_research_no_state),
    ]:
        run_test(name, fn)

    print("\n=== Verification System Tests (Task 2.1) ===\n")
    for name, fn in [
        ("emit_claim", test_emit_claim),
        ("emit_claim_appends", test_emit_claim_appends),
        ("emit_claim_with_depends", test_emit_claim_with_depends),
        ("write_result", test_write_result),
        ("write_flag", test_write_flag),
        ("read_verification_results_unread", test_read_verification_results_unread),
        ("clear_results", test_clear_results),
        ("clear_then_new_results", test_clear_then_new_results),
        ("jsonl_format", test_jsonl_format),
        ("read_log_empty", test_read_log_empty),
    ]:
        run_test(name, fn)

    print("\n=== Verification -> Research State Tests (Task 2.4) ===\n")
    for name, fn in [
        ("verified_claim_flows_to_state", test_verified_claim_flows_to_state),
        ("failed_claim_goes_to_attempts", test_failed_claim_goes_to_attempts),
        ("uncertain_claim_to_threads", test_uncertain_claim_to_threads),
    ]:
        run_test(name, fn)

    print("\n=== Watcher System Tests (Task 3) ===\n")
    for name, fn in [
        ("log_watcher", test_log_watcher),
        ("log_watcher_appends", test_log_watcher_appends),
        ("read_watcher_log_empty", test_read_watcher_log_empty),
        ("watcher_transition_triggers_init", test_watcher_transition_triggers_init),
        ("watcher_log_jsonl_format", test_watcher_log_jsonl_format),
    ]:
        run_test(name, fn)

    print("\n=== Edge Case Tests (Task 5.1) ===\n")
    for name, fn in [
        ("assumption_invalidation_propagates", test_assumption_invalidation_end_to_end),
        ("process_result_no_state_file", test_process_result_no_state_file),
        ("read_state_before_init", test_read_state_before_init),
        ("read_log_before_init", test_read_log_before_init),
        ("emit_claim_creates_dir", test_emit_claim_creates_dir),
        ("show_research_empty_graph", test_show_research_empty_graph),
        ("multiple_failures_dont_corrupt", test_multiple_failures_dont_corrupt),
    ]:
        run_test(name, fn)

    print("\n=== Session persistence Tests ===\n")
    for name, fn in [
        ("session_read_before_write_is_none", test_session_read_before_write_is_none),
        ("session_write_read_roundtrip", test_session_write_read_roundtrip),
        ("session_exploration_phase", test_session_exploration_phase),
        ("session_invalid_phase_raises", test_session_invalid_phase_raises),
        ("session_touch_refreshes_lastActive", test_session_touch_refreshes_lastActive),
        ("session_touch_no_session_is_noop", test_session_touch_no_session_is_noop),
        ("init_research_seeds_session", test_init_research_seeds_session),
        ("add_established_touches_session", test_add_established_touches_session),
        ("clear_session_removes_file", test_clear_session_removes_file),
    ]:
        run_test(name, fn)

    print("\n=== Dashboard queue Tests ===\n")
    for name, fn in [
        ("dashboard_queue_empty_initial", test_dashboard_queue_empty_initial),
        ("dashboard_queue_roundtrip", test_dashboard_queue_roundtrip),
    ]:
        run_test(name, fn)

    print(f"\n{'='*50}")
    print(f"Results: {PASSED} passed, {FAILED} failed")
    if ERRORS:
        print("\nFailures:")
        for name, err in ERRORS:
            print(f"\n  {name}:")
            traceback.print_exception(type(err), err, err.__traceback__)
    print()
    sys.exit(1 if FAILED else 0)
