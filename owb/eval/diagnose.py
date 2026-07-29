"""Trajectory diagnostics.

Analyses agent trajectories for common failure patterns:
- invalid calls (wrong params, entity not found)
- repeated exploration (same area, same action)
- state conflicts (operating on closed containers, etc.)
- excessive steps
"""

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class DiagnoseConfig:
    input_dir: str                     # agent run directory with trajectory.json

    def pre_process(self) -> None:
        p = Path(self.input_dir) / "trajectory.json"
        if not p.exists():
            raise FileNotFoundError(f"trajectory.json not found in {self.input_dir}")


def diagnose_trajectory(config: DiagnoseConfig) -> dict[str, Any]:
    """Analyse a trajectory and return diagnostic metrics."""
    with open(Path(config.input_dir) / "trajectory.json", "r") as f:
        traj = json.load(f)

    trajectory = traj.get("trajectory", [])
    max_iterations = traj.get("max_iterations", 30)

    stats = {
        "total_iterations": traj.get("total_iterations", 0),
        "max_iterations": max_iterations,
        "tool_calls": 0,
        "failed_actions": 0,
        "invalid_calls": 0,
        "repeated_actions": Counter(),
        "area_visits": Counter(),
        "termination_type": "unknown",
    }

    seen_actions = set()
    for entry in trajectory:
        for tc in entry.get("tool_calls", []):
            stats["tool_calls"] += 1
            name = tc.get("name", "unknown")
            stats["repeated_actions"][name] += 1

            # Check for failures
            resp = entry.get("tool_response", {})
            content = resp.get("content", "")
            if content.startswith("Error:"):
                stats["failed_actions"] += 1
                if "does not exist" in content or "not in the current area" in content:
                    stats["invalid_calls"] += 1

            # Track area visits
            if name == "move_to":
                area = tc.get("arguments", {}).get("area_id", "unknown")
                stats["area_visits"][area] += 1

            # Track termination
            if name in ("finish_task", "abandon_task", "report_unable_to_continue", "report_target_absent"):
                stats["termination_type"] = name

    # Repeated identical calls
    stats["repeated_identical"] = sum(
        1 for v in stats["repeated_actions"].values() if v > 1
    )

    # Efficiency score (actions per useful outcome)
    if stats["tool_calls"] > 0:
        stats["failure_rate"] = stats["failed_actions"] / stats["tool_calls"]
    else:
        stats["failure_rate"] = 0.0

    return stats


def run(config: DiagnoseConfig) -> None:
    config.pre_process()
    stats = diagnose_trajectory(config)
    print(json.dumps(stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    from simpleArgParser import parse_args
    cfg: DiagnoseConfig = parse_args(DiagnoseConfig)
    run(cfg)