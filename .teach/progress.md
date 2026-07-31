# Learning Progress

## 当前状态

- 当前阶段：mapped（本轮学习结束，2026-07-29）
- 当前模块：暂停
- 下一步建议：`/teach resume` → 精读 compile/world/actions，或明日 `.env` 跑通 `owb run`
- 当前代码版本：`1fb187f`

## 模块掌握情况

| 模块 | 优先级 | 掌握度 | 面试追问 | 修改练习 | 验证状态 |
|---|---|---:|---|---|---|
| project_map | 必须掌握 | 1 | 未开始 | 未完成 | 静态 |
| compile_pipeline | 必须掌握 | 0 | 未开始 | 未完成 | 未验证 |
| world_and_actions | 必须掌握 | 0 | 未开始 | 未完成 | 未验证 |
| observe_partial | 必须掌握 | 0 | 未开始 | 未完成 | 未验证 |
| goal_dsl_verify | 必须掌握 | 0 | 未开始 | 未完成 | 未验证 |
| agent_runner | 必须掌握 | 0 | 未开始 | 未完成 | 未验证 |
| data_json_spec | 必须掌握 | 0 | 未开始 | 未完成 | 未验证 |
| synth_legacy | 了解即可 | 0 | 未开始 | 未完成 | 未验证 |

掌握度：0 不了解 → 4 能修改并分析影响。

## 已掌握

- 知道项目是配置驱动的具身 reasoning benchmark，主链为 compile→env→run→verify→report。
- Goal DSL = 判卷标准（对 DB 快照求值）；walkthrough = 出题验题用的参考动作序列。
- compile 时 walkthrough 成功但 goal 不满足 → 不写 `.db`。
- 无模型链路与真实 `owb run` 的边界（后者依赖环境变量/`.env`）。

## 薄弱点

- 尚未亲手跑通真实 LLM `owb run`。
- `world` / `actions` / `observe` 未精读。
- 最小修改练习未做。

## 回答错误记录

| 日期 | 模块 | 问题 | 原回答问题 | 正确认识 |
|---|---|---|---|---|
|  |  |  |  |  |

## 待复习

- [ ] 主评测调用链各文件职责
- [ ] 最小复现：compile umbrella_move
