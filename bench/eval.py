"""
Benchmark evaluator for Triptych.

Generates problems, runs them through the pipeline, scores results.
Outputs per-problem diagnostics so the autoresearch agent can read
run.log and understand WHY things failed.

Usage:
    python bench/eval.py                    # default: seed=42, 7 solve + 3 error
    python bench/eval.py --seed 123         # different seed
    python bench/eval.py --n-solve 10       # more problems
    python bench/eval.py --dry-run          # just generate problems, don't run pipeline

IMMUTABLE — the autoresearch agent must never edit this file.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from bench.generators import generate_problems


def run_through_pipeline(problem: dict, project_root: Path) -> dict:
    """Run a single problem through the Triptych pipeline.

    This invokes Claude Code with the problem, using the project's
    CLAUDE.md, skills, and agent prompts as context. The response
    is captured and returned for scoring.

    Returns dict with:
        - "output": str (the model's response)
        - "claims": list (claims emitted, if any)
        - "verifier_output": str (what the verifier said)
        - "wall_time_s": float
    """
    try:
        import subprocess

        start = time.time()

        # Build the prompt based on problem type
        if problem["type"] == "solve":
            prompt = (
                f"Solve this problem. Show your work step by step. "
                f"Use the verification system (emit_claim, write_result) "
                f"to verify your key results.\n\n"
                f"{problem['problem']}"
            )
        else:
            prompt = (
                f"You are checking work for errors. Use the verification "
                f"system to formally check each step.\n\n"
                f"{problem['problem']}"
            )

        # Run via claude CLI in print mode (non-interactive)
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", prompt],
            capture_output=True,
            text=True,
            timeout=300,  # 5 min max per problem
            cwd=str(project_root),
        )

        wall_time = time.time() - start
        output = result.stdout or result.stderr or ""

        # Read verification log if it exists
        vlog_path = project_root / "workspace" / "research" / "verification.log"
        verifier_output = ""
        claims = []
        if vlog_path.exists():
            for line in vlog_path.read_text(encoding="utf-8").splitlines():
                try:
                    entry = json.loads(line)
                    if entry.get("type") == "claim":
                        claims.append(entry)
                    elif entry.get("type") == "result":
                        verifier_output += f"{entry.get('claimId')}: {entry.get('status')} ({entry.get('method')})\n"
                except json.JSONDecodeError:
                    pass

        return {
            "output": output,
            "claims": claims,
            "verifier_output": verifier_output,
            "wall_time_s": round(wall_time, 1),
        }

    except FileNotFoundError:
        return {
            "output": "[ERROR: claude CLI not found. Install Claude Code or run with --dry-run]",
            "claims": [],
            "verifier_output": "",
            "wall_time_s": 0,
        }
    except subprocess.TimeoutExpired:
        return {
            "output": "[ERROR: timed out after 300s]",
            "claims": [],
            "verifier_output": "",
            "wall_time_s": 300,
        }
    except Exception as e:
        return {
            "output": f"[ERROR: {e}]",
            "claims": [],
            "verifier_output": "",
            "wall_time_s": 0,
        }


def score_result(problem: dict, pipeline_result: dict) -> dict:
    """Score a pipeline result against ground truth.

    Returns dict with:
        - "passed": bool
        - "reason": str (why it passed/failed)
        - "actual": str (what the pipeline produced, truncated)
    """
    output = pipeline_result["output"]

    if output.startswith("[ERROR:"):
        return {"passed": False, "reason": output, "actual": ""}

    try:
        passed = problem["check"](output)
    except Exception as e:
        passed = False
        return {"passed": False, "reason": f"check function raised: {e}", "actual": output[:200]}

    if problem["type"] == "solve":
        reason = "correct answer found" if passed else "answer not found or incorrect"
    else:
        reason = "error identified" if passed else "error not caught"

    return {
        "passed": passed,
        "reason": reason,
        "actual": output[:500],
        "verifier_output": pipeline_result.get("verifier_output", ""),
        "claims_count": len(pipeline_result.get("claims", [])),
        "wall_time_s": pipeline_result.get("wall_time_s", 0),
    }


def run_benchmark(seed: int = 42, n_solve: int = 7, n_error: int = 3,
                  dry_run: bool = False):
    """Run the full benchmark and print results.

    In dry-run mode, just generates problems and validates generators
    (no LLM calls). Useful for testing the benchmark itself.
    """
    project_root = Path(__file__).parent.parent
    problems = generate_problems(seed, n_solve, n_error)

    print(f"=== Triptych Benchmark ===")
    print(f"seed: {seed}  problems: {len(problems)} ({n_solve} solve + {n_error} error)")
    print(f"timestamp: {datetime.now().isoformat()}")
    print()

    results = []
    for p in problems:
        if dry_run:
            # In dry-run, just validate the problem structure
            scored = {
                "passed": None,
                "reason": "dry-run: not evaluated",
                "actual": "",
            }
            print(f"--- {p['id']} ({p['type']}) ---")
            print(f"problem: {p['problem'][:120]}")
            if p['type'] == 'solve':
                print(f"expected: {p['answer']}")
            else:
                print(f"error_to_catch: {p['error_location']}")
            print(f"params: {p['params']}")
            print()
        else:
            # Clean verification log before each problem
            vlog = project_root / "workspace" / "research" / "verification.log"
            if vlog.exists():
                vlog.unlink()

            pipeline_result = run_through_pipeline(p, project_root)
            scored = score_result(p, pipeline_result)

            # Print per-problem diagnostic detail
            print(f"--- {p['id']} ({p['type']}) ---")
            print(f"problem: {p['problem'][:120]}")
            print(f"passed: {scored['passed']}")
            if not scored['passed']:
                if p['type'] == 'solve':
                    print(f"expected: {p['answer']}")
                else:
                    print(f"error_to_catch: {p['error_location']}")
                print(f"failure_reason: {scored['reason']}")
                if scored.get('actual'):
                    # Show relevant excerpt of what was produced
                    print(f"got: {scored['actual'][:200]}")
            if scored.get('verifier_output'):
                print(f"verifier: {scored['verifier_output'].strip()}")
            if scored.get('claims_count', 0) > 0:
                print(f"claims_emitted: {scored['claims_count']}")
            if scored.get('wall_time_s', 0) > 0:
                print(f"wall_time: {scored['wall_time_s']}s")
            print()

        results.append({"problem": p["id"], "type": p["type"], **scored})

    if dry_run:
        print(f"dry-run complete: {len(problems)} problems generated successfully")
        return

    # Compute final score
    correct = sum(1 for r in results if r["passed"])
    total = len(results)
    score = correct / total if total > 0 else 0

    # Breakdown by type
    solve_results = [r for r in results if r["type"] == "solve"]
    error_results = [r for r in results if r["type"] == "catch_error"]
    solve_correct = sum(1 for r in solve_results if r["passed"])
    error_correct = sum(1 for r in error_results if r["passed"])

    print(f"=== Results ===")
    print(f"accuracy: {solve_correct}/{len(solve_results)}")
    print(f"error_catch: {error_correct}/{len(error_results)}")
    print(f"score: {score:.4f}  ({correct}/{total})")

    # Append to results.tsv
    results_file = Path(__file__).parent / "results.tsv"
    header_needed = not results_file.exists()
    with open(results_file, "a", encoding="utf-8") as f:
        if header_needed:
            f.write("timestamp\tseed\tscore\taccuracy\terror_catch\ttotal\n")
        f.write(f"{datetime.now().isoformat()}\t{seed}\t{score:.4f}\t"
                f"{solve_correct}/{len(solve_results)}\t"
                f"{error_correct}/{len(error_results)}\t{total}\n")

    return score


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Triptych benchmark evaluator")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--n-solve", type=int, default=7, help="Number of solve problems")
    parser.add_argument("--n-error", type=int, default=3, help="Number of error injection problems")
    parser.add_argument("--dry-run", action="store_true", help="Generate problems only, no LLM calls")
    args = parser.parse_args()

    run_benchmark(seed=args.seed, n_solve=args.n_solve, n_error=args.n_error,
                  dry_run=args.dry_run)
