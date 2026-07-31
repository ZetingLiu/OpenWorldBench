# Project Map — OpenWorldBench

## 1. 项目一句话说明

- 项目解决的问题：评测 VLM/Agent 作为「具身大脑」时，能否在部分可观测环境中通过多轮高层语义工具调用完成真实业务任务（家庭/商超）。
- 主要输入：场景 JSON（区域/实体/邻接）+ 任务 JSON（指令、goal DSL、walkthrough）。
- 主要输出：编译后的 SQLite 初始快照、agent 轨迹、DSL 验证结果、按 capability tag 聚合的报告。
- 核心技术路线：配置驱动世界 → SQLite 单源状态 → 17 固定语义动作（MCP/HTTP）→ 原生 function calling → 程序化 goal DSL 评测（非 LLM judge）。

## 2. 顶层目录

| 路径 | 职责 | 学习优先级 | 原因 |
|---|---|---|---|
| `owb/cli.py` | CLI 入口 | 【必须掌握】 | 所有命令分发 |
| `owb/schema/` | 场景/任务模型 + goal DSL | 【必须掌握】 | 数据契约与判定逻辑 |
| `owb/env/` | 世界状态、动作、观测、编译、服务 | 【必须掌握】 | 环境引擎核心 |
| `owb/run/` | Agent 循环与任务运行器 | 【必须掌握】 | 复现评测闭环必需 |
| `owb/eval/` | verify / diagnose / report | 【必须掌握】 | 评分与诊断 |
| `data/scenarios/`、`data/tasks/` | 场景与任务包 | 【必须掌握】 | 复现与扩展内容入口 |
| `owb/tools.py`、`owb/llm.py` | 通用工具与 LLM 客户端 | 【了解即可】 | 支撑层 |
| `owb/synth/` | 旧 AWM LLM 合成流水线 | 【暂时跳过】 | 不在主评测链上 |
| `figures/` | Logo 资源 | 【暂时跳过】 | 文档装饰 |
| `mcp-adapted-bench/` | 子模块/外部 bench | 【暂时跳过】 | 非主线 |
| `external/` | 本地参考（未入仓） | 【暂时跳过】 | 非运行依赖 |

## 3. 启动入口

| 场景 | 命令 | 入口文件 | 关键配置 |
|---|---|---|---|
| 编译 | `owb compile` | `owb/env/compile.py` | 场景/任务 JSON |
| 环境服务 | `owb env start` | `owb/env/server.py` | 编译产物 `.db` |
| Agent 跑任务 | `owb run` | `owb/run/runner.py` + `agent.py` | LLM API / meta.json |
| 验证 | `owb verify` | `owb/eval/verify.py` | run 目录 `trajectory.json` |
| 报告 | `owb report` | `owb/eval/report.py` | 多个 run 的 `verify.json` |
| 合成（旁路） | `owb synth ...` | `owb/synth/*` | 暂不优先 |

## 4. 核心模块

| 模块 | 核心文件/类 | 上游 | 下游 | 类别 |
|---|---|---|---|---|
| Schema | `scenario.py` / `task.py` | JSON 数据 | compile / DSL | 【必须掌握】 |
| Goal DSL | `goal_dsl.py` | Task.goal / subgoals | compile 回放、verify | 【必须掌握】 |
| World | `WorldState` | compile / actions | snapshot / DB | 【必须掌握】 |
| Actions | `execute_action` 17 动作 | server / walkthrough | world 状态转移 | 【必须掌握】 |
| Observe | `generate_observation` | server / agent | 部分可观测文本 | 【必须掌握】 |
| Compile | `compile_scenario_task` | CLI | `.db` + `.meta.json` | 【必须掌握】 |
| Server | FastAPI + MCP | runner | HTTP 动作端点 | 【必须掌握】 |
| Runner/Agent | `run_single_task` / `run_agent` | CLI | trajectory / final.db | 【必须掌握】 |
| Verify/Report | `verify_run` / `generate_report` | CLI | verify.json / 聚合 | 【必须掌握】 |
| Synth | `owb/synth/*` | CLI synth | 旧合成 | 【了解即可】 |

## 5. 外部依赖与边界

- 第三方框架：FastAPI、fastapi-mcp、OpenAI SDK、Pydantic、simpleArgParser、SQLite。
- 子模块：`mcp-adapted-bench`（可选，主线不依赖）。
- 外部数据：`data/` 手工场景/任务；无训练权重依赖。
- 硬件依赖：CPU 即可跑 compile/env/verify；`owb run` 需要可访问的 LLM API。

## 6. 可暂时跳过

- `owb/synth/`：旧 agent-world-model 合成管线，与主评测链解耦。
- `mcp-adapted-bench/`、`external/`：外部参考，非复现最小路径。
- `owb/env/events.py`：phase ③ 事件占位。
- `figures/`：品牌资源。
