#!/usr/bin/env python3

import json
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("grill_state.py")
MAXIMA = {
    "objective_target": 15,
    "evidence_denominator": 20,
    "mechanism": 15,
    "measurement": 15,
    "execution": 15,
    "risks": 10,
    "clarity": 10,
}


def dimensions(score):
    remaining = score
    result = {}
    for key, maximum in MAXIMA.items():
        value = min(remaining, maximum)
        result[key] = value
        remaining -= value
    return result


def packet(score=70, route="JUDGE", decision="ACCEPT", material=True, confidence=0.95):
    return {
        "question": "What is the highest-impact unresolved issue?",
        "route": route,
        "recommendation": "Use the narrower reversible option.",
        "decision": decision,
        "rationale": "The evidence supports this bounded choice.",
        "impact": "Clarifies the decision boundary.",
        "confidence": confidence,
        "evidence": [{"source": "/tmp/source.md:1", "fact": "A test fact"}],
        "score": score,
        "dimension_scores": dimensions(score),
        "vetoes": [],
        "high_impact_open": [],
        "material_new_issue": material,
    }


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class GrillStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "plan.md"
        self.source.write_text("# Original plan\n", encoding="utf-8")
        self.run_dir = self.root / ".grill-loop"

    def tearDown(self):
        self.temp.cleanup()

    def run_cli(self, *args, expect=0):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expect, msg=result.stderr or result.stdout)
        return result

    def init(self, mode="supervised"):
        result = self.run_cli(
            "init", "--source", self.source, "--mode", mode, "--run-dir", self.run_dir
        )
        return json.loads(result.stdout)

    def record(self, value, *extra, expect=0):
        candidate = None
        if "--candidate" in extra:
            candidate = extra[extra.index("--candidate") + 1]
        if "artifact_sha256" not in value:
            artifact = Path(candidate) if candidate else self.run_dir / self.load_state()["current_draft"]
            value["artifact_sha256"] = file_hash(artifact)
        packet_path = self.root / "packet.json"
        packet_path.write_text(json.dumps(value), encoding="utf-8")
        return self.run_cli(
            "record", "--run-dir", self.run_dir, "--input", packet_path, *extra, expect=expect
        )

    def load_state(self):
        return json.loads((self.run_dir / "state.json").read_text(encoding="utf-8"))

    def test_init_preserves_original_and_creates_baseline(self):
        summary = self.init()
        self.assertEqual(summary["status"], "active")
        self.assertEqual(self.source.read_text(encoding="utf-8"), "# Original plan\n")
        self.assertEqual(
            (self.run_dir / "drafts" / "000-baseline.md").read_text(encoding="utf-8"),
            "# Original plan\n",
        )

    def test_fast_pass_validation_does_not_mutate_state_on_failure(self):
        self.init()
        result = self.record(packet(route="FAST_PASS", confidence=0.80), expect=2)
        self.assertIn("FAST_PASS requires confidence", result.stderr)
        self.assertEqual(self.load_state()["iteration"], 0)

    def test_supervised_escalation_pauses_and_resume_continues(self):
        self.init("supervised")
        paused = packet(route="ESCALATE", decision="USER_REQUIRED", score=40)
        result = self.record(paused)
        self.assertEqual(json.loads(result.stdout)["status"], "paused")
        self.record(packet(score=50), expect=2)
        resumed = self.record(packet(score=60, material=False), "--resume")
        self.assertEqual(json.loads(resumed.stdout)["status"], "active")
        self.assertEqual(self.load_state()["escalations"][0]["status"], "resolved")

    def test_autonomous_escalation_can_end_in_conditional_pass(self):
        self.init("autonomous")
        candidate = self.root / "conservative.md"
        candidate.write_text("# Conservative plan\n", encoding="utf-8")
        escalated = packet(route="ESCALATE", decision="CONSERVATIVE", score=84, material=True)
        escalated["high_impact_open"] = ["Business owner must set the threshold"]
        self.record(escalated, "--candidate", candidate)
        self.record(packet(score=85, material=False))
        result = self.record(packet(score=86, material=False))
        self.assertEqual(json.loads(result.stdout)["status"], "conditional_pass")

    def test_quality_threshold_passes_after_two_stable_iterations(self):
        self.init()
        self.record(packet(score=85, material=False))
        result = self.record(packet(score=86, material=False))
        self.assertEqual(json.loads(result.stdout)["status"], "passed")
        finalized = self.run_cli("finalize", "--run-dir", self.run_dir)
        self.assertEqual(json.loads(finalized.stdout)["final_path"], "final.md")
        self.assertTrue((self.run_dir / "final.md").is_file())

    def test_stagnation_stops_after_two_intervals_under_delta(self):
        self.init()
        self.record(packet(score=50, decision="REJECT", material=True))
        self.record(packet(score=51, decision="REJECT", material=True))
        result = self.record(packet(score=52, decision="REJECT", material=True))
        summary = json.loads(result.stdout)
        self.assertEqual(summary["status"], "stopped")
        self.assertEqual(summary["stop_reason"], "stagnation")

    def test_candidate_snapshot_never_overwrites_original(self):
        self.init()
        candidate = self.root / "candidate.md"
        candidate.write_text("# Revised plan\n", encoding="utf-8")
        result = self.record(packet(score=75), "--candidate", candidate)
        summary = json.loads(result.stdout)
        self.assertEqual(self.source.read_text(encoding="utf-8"), "# Original plan\n")
        self.assertEqual(
            (self.run_dir / summary["current_draft"]).read_text(encoding="utf-8"),
            "# Revised plan\n",
        )
        decisions = (self.run_dir / "decisions.md").read_text(encoding="utf-8")
        self.assertIn("Iteration 1", decisions)

    def test_rejects_score_bound_to_pre_revision_artifact(self):
        self.init()
        candidate = self.root / "candidate.md"
        candidate.write_text("# Revised plan\n", encoding="utf-8")
        stale = packet(score=75)
        stale["artifact_sha256"] = file_hash(self.run_dir / "drafts" / "000-baseline.md")
        result = self.record(stale, "--candidate", candidate, expect=2)
        self.assertIn("rescore the candidate", result.stderr)
        self.assertEqual(self.load_state()["iteration"], 0)

    def test_accepting_candidate_requires_material_new_issue(self):
        self.init()
        candidate = self.root / "candidate.md"
        candidate.write_text("# Revised plan\n", encoding="utf-8")
        result = self.record(packet(score=75, material=False), "--candidate", candidate, expect=2)
        self.assertIn("material_new_issue=true", result.stderr)
        self.assertEqual(self.load_state()["iteration"], 0)

    def test_fast_pass_cannot_include_candidate(self):
        self.init()
        candidate = self.root / "candidate.md"
        candidate.write_text("# Revised plan\n", encoding="utf-8")
        value = packet(score=70, route="FAST_PASS", decision="ACCEPT", material=False, confidence=0.95)
        result = self.record(value, "--candidate", candidate, expect=2)
        self.assertIn("FAST_PASS cannot include a candidate", result.stderr)
        self.assertEqual(self.load_state()["iteration"], 0)

    def test_autonomous_escalation_without_safe_branch_stops(self):
        self.init("autonomous")
        value = packet(route="ESCALATE", decision="USER_REQUIRED", score=20, material=True)
        value["high_impact_open"] = ["Irreversible authority decision"]
        result = self.record(value)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["status"], "stopped")
        self.assertEqual(summary["stop_reason"], "no_safe_conservative_branch")

    def test_abort_marks_active_run_stopped(self):
        self.init("autonomous")
        result = self.run_cli(
            "abort",
            "--run-dir",
            self.run_dir,
            "--reason",
            "subagent_failure",
            "--detail",
            "judge failed twice",
        )
        summary = json.loads(result.stdout)
        self.assertEqual(summary["status"], "stopped")
        self.assertEqual(summary["stop_reason"], "subagent_failure")
        self.assertEqual(self.load_state()["abort_detail"], "judge failed twice")


if __name__ == "__main__":
    unittest.main()
