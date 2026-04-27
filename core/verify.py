import json
import time
from pathlib import Path

from core.paths import RESEARCH_DIR as DEFAULT_DIR

_claim_counter = 0


def emit_claim(claim, context, depends=None, research_dir=None):
    global _claim_counter
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    d.mkdir(parents=True, exist_ok=True)
    _claim_counter += 1
    claim_id = f"C{_claim_counter}"
    entry = {
        "type": "claim",
        "id": claim_id,
        "claim": claim,
        "context": context,
        "depends": depends or [],
        "timestamp": time.time(),
    }
    with open(d / "verification.log", "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Signal to the UserPromptSubmit hook that the verifier loop should be
    # running. The hook inject-verifier-hint.mjs compares this ts against
    # .verifier-informed and nudges the agent once per new-claim burst.
    # Python cannot start a Claude loop directly, so the hook layer is the
    # right place — this file is just the trigger.
    _write_atomic(d / "verifier-wanted",
                  json.dumps({"ts": entry["timestamp"], "claimId": claim_id}))
    return claim_id


def _write_atomic(path, text):
    """Write text atomically via .tmp + os.replace (Windows-safe)."""
    import os
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def write_result(claim_id, status, method, detail, research_dir=None):
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    entry = {
        "type": "result",
        "claimId": claim_id,
        "status": status,
        "method": method,
        "detail": detail,
        "timestamp": time.time(),
    }
    with open(d / "verification.log", "a") as f:
        f.write(json.dumps(entry) + "\n")


def write_flag(kind, detail, research_dir=None):
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    entry = {
        "type": "flag",
        "kind": kind,
        "detail": detail,
        "timestamp": time.time(),
    }
    with open(d / "verification.log", "a") as f:
        f.write(json.dumps(entry) + "\n")


def read_log(research_dir=None):
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    log = d / "verification.log"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().strip().split("\n") if line]


def read_verification_results(research_dir=None):
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    read_marker = d / ".last_read"
    last_read = float(read_marker.read_text().strip()) if read_marker.exists() else 0
    return [e for e in read_log(d)
            if e["type"] in ("result", "flag") and e["timestamp"] > last_read]


def clear_results(research_dir=None):
    d = Path(research_dir) if research_dir else DEFAULT_DIR
    (d / ".last_read").write_text(str(time.time()))


def process_result(claim_id, status, claim_text, depends, research_dir=None):
    from core.research import add_established, add_attempt, add_thread

    d = Path(research_dir) if research_dir else DEFAULT_DIR

    if status == "verified":
        add_established(claim_id, claim_text, depends, d)
    elif status == "failed":
        add_attempt(claim_text, "failed", "Verification failed", d)
    elif status == "uncertain":
        add_thread(claim_id, claim_text, depends, d)
