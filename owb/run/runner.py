"""Task runner: single-task and batch execution with trajectory recording.

The runner:
1. Loads compiled SQLite snapshot
2. Starts the environment server
3. Runs the agent against it
4. Records trajectory + final state snapshot
5. Shuts down the server
"""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from owb.tools import (
    tools_jsonl_load,
    tools_json_save,
    get_random_available_port,
    async_wait_for_server,
    resolve_llm_config,
)
from owb.env.world import WorldState, save_snapshot


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class RunnerConfig:
    # Path to the compiled task DB (or directory of them)
    db_path: str
    # Task instruction (overrides any embedded task)
    task: str | None = None
    # LLM overrides
    api_url: str | None = None
    model: str | None = None
    # Agent settings (None → use the task's max_steps from the sidecar meta)
    max_iterations: int | None = None
    temperature: float = 1.0
    max_tokens: int = 2048
    # Output
    output_dir: str = "outputs/runs"
    # Server
    host: str = "127.0.0.1"
    port: int | None = None
    # Batch mode
    batch: bool = False


# ---------------------------------------------------------------------------
# Run a single task
# ---------------------------------------------------------------------------

async def run_single_task(config: RunnerConfig) -> dict[str, Any]:
    """Run one task end-to-end.

    Returns
    -------
    dict
        Run report with keys: task, model, trajectory, final_db, etc.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(config.output_dir, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    # Load sidecar task meta written by the compiler (<task_id>.meta.json)
    task_meta: dict[str, Any] = {}
    meta_path = Path(config.db_path).with_suffix(".meta.json")
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            task_meta = json.load(f)
        shutil.copy2(meta_path, os.path.join(output_dir, "task.meta.json"))

    task_instruction = config.task or task_meta.get("instruction")
    if not task_instruction:
        raise ValueError(
            "No task instruction: provide --task or compile the task so that "
            f"a sidecar meta file exists next to {config.db_path}"
        )
    max_iterations = config.max_iterations or task_meta.get("max_steps") or 30

    # Copy initial DB
    initial_db = os.path.join(output_dir, "initial.db")
    shutil.copy2(config.db_path, initial_db)

    # Working DB
    working_db = os.path.join(output_dir, "working.db")
    shutil.copy2(config.db_path, working_db)

    # Start server
    port = config.port or get_random_available_port()
    server_proc = _start_server(working_db, config.host, port, output_dir)

    try:
        if not await async_wait_for_server(port, timeout=60):
            raise RuntimeError(f"Server failed to start on port {port}")

        mcp_url = f"http://{config.host}:{port}/mcp"

        # Run agent
        from owb.run.agent import AgentConfig, run_agent

        agent_config = AgentConfig(
            task=task_instruction,
            mcp_url=mcp_url,
            api_url=config.api_url,
            model=config.model,
            max_iterations=max_iterations,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            output_dir=output_dir,
            verbose=True,
            task_id=task_meta.get("task_id"),
            scenario_id=task_meta.get("scenario_id"),
        )

        trajectory = await run_agent(agent_config)

        # Save final DB snapshot
        final_db = os.path.join(output_dir, "final.db")
        shutil.copy2(working_db, final_db)

        report = {
            "task": task_instruction,
            "task_id": task_meta.get("task_id"),
            "scenario_id": task_meta.get("scenario_id"),
            "model": config.model,
            "output_dir": output_dir,
            "initial_db": initial_db,
            "final_db": final_db,
            "trajectory": trajectory,
            "timestamp": timestamp,
        }

        tools_json_save(report, os.path.join(output_dir, "report.json"))
        return report

    finally:
        if server_proc and server_proc.poll() is None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait()


def _start_server(db_path: str, host: str, port: int, output_dir: str) -> subprocess.Popen:
    """Start environment server as a subprocess."""
    cmd = [
        sys.executable, "-m", "owb.env.server",
        db_path, str(port),
    ]
    log_path = os.path.join(output_dir, "server.log")
    log_f = open(log_path, "w")
    logger.info(f"Starting server: {' '.join(cmd)}")
    return subprocess.Popen(cmd, stdout=log_f, stderr=subprocess.STDOUT)


# ---------------------------------------------------------------------------
# CLI entry
# ---------------------------------------------------------------------------

def run(config: RunnerConfig) -> None:
    if config.batch:
        _run_batch(config)
    else:
        asyncio.run(run_single_task(config))


def _run_batch(config: RunnerConfig) -> None:
    """Run all .db files in a directory."""
    db_dir = Path(config.db_path)
    if db_dir.is_dir():
        db_files = sorted(db_dir.glob("*.db"))
    else:
        db_files = [db_dir]

    results = []
    for db_file in db_files:
        logger.info(f"Running task: {db_file.name}")
        cfg = RunnerConfig(
            db_path=str(db_file),
            task=config.task,
            api_url=config.api_url,
            model=config.model,
            max_iterations=config.max_iterations,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            output_dir=config.output_dir,
            host=config.host,
            port=config.port,
        )
        try:
            report = asyncio.run(run_single_task(cfg))
            results.append({"db": str(db_file), "status": "ok", "report": report})
        except Exception as e:
            logger.error(f"Failed {db_file.name}: {e}")
            results.append({"db": str(db_file), "status": "error", "error": str(e)})

    tools_json_save(results, os.path.join(config.output_dir, "batch_results.json"))


if __name__ == "__main__":
    from simpleArgParser import parse_args
    cfg: RunnerConfig = parse_args(RunnerConfig)
    run(cfg)