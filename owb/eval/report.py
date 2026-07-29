"""Capability-tag aggregation report.

Aggregates verification results across multiple runs and produces
per-capability-tag success/failure statistics.
"""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger


@dataclass
class ReportConfig:
    input_dir: str                     # directory containing multiple run subdirectories
    tasks_dir: str = "data/tasks"      # base directory for task JSONs

    def pre_process(self) -> None:
        if not Path(self.input_dir).is_dir():
            raise FileNotFoundError(f"Input directory not found: {self.input_dir}")


def generate_report(config: ReportConfig) -> dict[str, Any]:
    """Scan all run subdirectories and aggregate results by capability tag."""
    input_dir = Path(config.input_dir)
    tasks_dir = Path(config.tasks_dir)

    # Load all task definitions for capability tags
    task_tags: dict[str, list[str]] = {}
    for task_file in tasks_dir.rglob("*.json"):
        if task_file.name == "README.md":
            continue
        try:
            with open(task_file) as f:
                data = json.load(f)
            task_tags[data["task_id"]] = data.get("capability_tags", [])
        except Exception:
            pass

    # Collect results
    per_tag: dict[str, dict[str, int]] = defaultdict(lambda: {"complete": 0, "partial": 0, "incomplete": 0, "error": 0, "exceeded": 0, "abandoned": 0, "total": 0})
    overall = {"complete": 0, "partial": 0, "incomplete": 0, "error": 0, "exceeded": 0, "abandoned": 0, "total": 0}

    for run_dir in sorted(input_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        verify_file = run_dir / "verify.json"
        if not verify_file.exists():
            continue

        try:
            with open(verify_file) as f:
                verify = json.load(f)
        except Exception:
            continue

        result = verify.get("result", "incomplete")
        task_id = verify.get("details", {}).get("task_id", "unknown")

        overall[result] = overall.get(result, 0) + 1
        overall["total"] += 1

        tags = task_tags.get(task_id, ["unknown"])
        for tag in tags:
            per_tag[tag][result] = per_tag[tag].get(result, 0) + 1
            per_tag[tag]["total"] += 1

    # Compute success rates
    tag_summary = {}
    for tag, counts in sorted(per_tag.items()):
        total = counts["total"]
        tag_summary[tag] = {
            **counts,
            "success_rate": counts["complete"] / total if total > 0 else 0.0,
        }

    overall_total = overall["total"]
    report = {
        "overall": {
            **overall,
            "success_rate": overall["complete"] / overall_total if overall_total > 0 else 0.0,
        },
        "by_capability": tag_summary,
    }

    return report


def run(config: ReportConfig) -> None:
    config.pre_process()
    report = generate_report(config)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    from simpleArgParser import parse_args
    cfg: ReportConfig = parse_args(ReportConfig)
    run(cfg)