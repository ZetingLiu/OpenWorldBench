# Core Call Chains — OpenWorldBench

## 调用链 1：主评测闭环（必须掌握）

### 目标

从场景/任务 JSON 到可复现评测结果。

### 完整路径

```text
owb compile
→ load_scenario / load_task（Pydantic + S1–S8）
→ WorldState.populate_from_scenario（+ initial_state_patch）
→ walkthrough：execute_action 回放 + evaluate_goal
→ 写出 <task_id>.db + <task_id>.meta.json
→ owb env start：create_app(db) 注册 17 动作
→ owb run：复制 DB → 起 server → run_agent（function calling）
→ 写 trajectory.json / final.db
→ owb verify：evaluate_goal + SubgoalTracker 锁存回放
→ owb report：按 capability_tags 聚合
```

### 代码定位

| 顺序 | 文件 | 类/函数 | 作用 | 必须理解的状态 |
|---|---|---|---|---|
| 1 | `owb/cli.py` | `main` | 命令分发 | CompileConfig / RunnerConfig |
| 2 | `owb/env/compile.py` | `compile_scenario_task` | 校验+回放+落盘 | solvable / errors |
| 3 | `owb/env/world.py` | `WorldState` | SQLite 单源状态 | area/container/held |
| 4 | `owb/env/actions.py` | `execute_action` | 前置检查与状态转移 | ActionResult |
| 5 | `owb/env/observe.py` | `generate_observation` | 部分可观测 | closed container 隐藏 |
| 6 | `owb/env/server.py` | `create_app` | HTTP/MCP 暴露动作 | working.db |
| 7 | `owb/run/runner.py` | `run_single_task` | 起服+跑 agent | meta.json |
| 8 | `owb/run/agent.py` | `run_agent` | 多轮 tool calling | messages / trajectory |
| 9 | `owb/schema/goal_dsl.py` | `evaluate_goal` / `SubgoalTracker` | 目标与子目标 | latch |
| 10 | `owb/eval/verify.py` | `verify_run` | 结果分类 | complete/partial/... |

### 易错点

- 封闭容器内容必须对观测隐藏，否则 search 能力评测失效。
- `initial_state_patch` 必须在 robot INSERT 之后应用。
- verify 回放不得污染 `initial.db`。
- walkthrough 步数预算按**单条** walkthrough 与 `max_steps` 比较。

### 验证状态

- [ ] 已运行验证（用户侧尚未运行）
- [x] 已静态验证（代码与数据已扫描）
- [ ] 尚未验证

---

## 调用链 2：Walkthrough 可解性（编译期）

### 目标

保证任务定义可解，避免无效题。

```text
Task.walkthroughs[*].actions
→ execute_action（内存 WorldState）
→ SubgoalTracker.update
→ evaluate_goal(final)
→ solvable=True 才写 .db / .meta.json
```

### 验证状态

- [x] 已静态验证（home 两个任务此前编译为 SOLVABLE）
