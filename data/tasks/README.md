# 任务包 JSON 规范 v0

## 文件约定

- 任务包位于 `data/tasks/<scenario_id>/<task_id>.json`
- 一条任务绑定一个场景，通过 `scenario_id` 关联
- 任务包不复制场景数据，通过 `initial_state_patch` 做增量覆盖

## 顶层结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `task_id` | string | ✅ | 任务唯一标识 |
| `spec_version` | string | ✅ | 规范版本，当前 `0.1` |
| `scenario_id` | string | ✅ | 关联的场景 ID |
| `name` | string | ✅ | 任务中文名 |
| `instruction` | string | ✅ | 自然语言任务指令（给模型） |
| `task_type` | string | ✅ | 任务类型：`direct` / `composite` |
| `capability_tags` | string[] | ✅ | 能力标签（见下方枚举） |
| `max_steps` | int | ✅ | 最大交互步数 |
| `initial_state_patch` | object | ❌ | 初始状态覆盖（见下方说明） |
| `goal` | GoalCondition | ✅ | 目标 DSL 条件 |
| `subgoals` | Subgoal[] | ❌ | 子目标列表 |
| `walkthroughs` | Walkthrough[] | ✅ | 参考动作序列（编译时回放校验） |

## initial_state_patch

不复制整个场景，只覆盖需要修改的字段。引用实体时使用**实体 ID 路径**：

```json
{
  "initial_state_patch": {
    "entities": {
      "laundry_basket_01": { "states": { "condition": "damaged" } }
    },
    "robot": {
      "location": "bedroom"
    },
    "area_adjacency": [
      { "from": "living_room", "to": "balcony", "passable": false }
    ]
  }
}
```

覆盖规则：
- 未列出的实体保持场景默认值
- 覆盖是浅合并：`states` 整体替换，不递归合并
- entity 路径中的 ID 必须在场景中存在
- `area_adjacency` 按 `(from, to)` 无向匹配覆盖对应边的 `passable`，用于表达通道封闭类扰动
- 与场景默认值相同的 patch 属于冗余，采集时应避免（校验器将给出警告）

## GoalCondition

DSL 条件支持以下操作符：

| 操作符 | 参数 | 说明 |
|--------|------|------|
| `eq` | `{entity, field, value}` | 实体字段等于某值 |
| `in` | `{entity, field, value}` | 实体字段值在集合中 |
| `all_of` | `Condition[]` | 所有条件必须满足 |
| `any_of` | `Condition[]` | 任一条件满足 |
| `count` | `{entity_class, where, cmp, value}` | 统计满足 `where` 条件的某类实体数量并比较 |

`count` 示例——"洗衣机内至少有 2 件衣物"：

```json
{
  "op": "count",
  "entity_class": "clothing",
  "where": { "field": "container_id", "op": "eq", "value": "washing_machine_01" },
  "cmp": "gte",
  "value": 2
}
```

`field` 支持：
- `container_id` — 实体所在容器 ID，**仅对应 `in` 关系**；放在表面上（`on`）不计入，防止"放在洗衣机顶上"被误判为"放进洗衣机"
- `on` — 实体所在表面 ID
- `area_id` — 实体所在区域 ID（沿 `in` / `on` / `held_by` 链向上解析至区域，用于"把 X 放到卧室"类目标）
- `held_by` — 被谁持有（`left_hand` / `right_hand` / `null`）
- `states.<key>` — 状态值
- `device_state` / `open_state` — 设备/容器状态

## Subgoal

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 子目标标识 |
| `description` | string | ✅ | 子目标中文描述 |
| `cond` | GoalCondition | ✅ | 子目标 DSL 条件 |

### 子目标评估语义（锁存）

- 子目标在**每步动作执行后**求值一次；
- 任一步骤满足后即**锁存为已达成**，后续状态变化不撤销（如"衣物曾被拾取"在放下后仍视为达成）；
- 子目标条件应描述**过程中某一时刻可观察到的状态**，不得要求多个瞬态条件同时成立——例如不要用 `all_of` 要求两件衣物同时被持有，逐件搬运时该条件永远不会为真，应拆成每件衣物一个子目标；
- 最终目标 `goal` 与子目标不同：仅在任务结束时基于最终数据库状态判定一次，不锁存。

## Walkthrough

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `description` | string | ✅ | 方案描述（如"常规方案"、"替代方案"） |
| `actions` | Action[] | ✅ | 参考动作序列 |

每个 Action 使用与 17 个动作接口一致的格式：

```json
{
  "action": "pick_object",
  "params": { "entity_id": "clothes_01" }
}
```

## 能力标签枚举

| 标签 | 说明 |
|------|------|
| `navigation` | 空间导航（移动至不同区域） |
| `pick_and_place` | 基本取放 |
| `container_open_close` | 容器开合 |
| `device_operation` | 设备操作（启动/停止） |
| `multi_step` | 多步序列 |
| `tool_use` | 工具使用 |
| `state_awareness` | 状态感知（检查洁净度、损坏等） |
| `hand_management` | 双手管理 |
| `search` | 搜索（在区域内查找物体） |
| `error_recovery` | 错误恢复（应对失败并尝试替代方案） |

## 任务可解性校验（compile 时执行）

1. 加载初始快照（场景 + `initial_state_patch` 合并）
2. 对每条 `walkthrough` 逐步回放：
   - 调用 `actions.py` 执行每步动作
   - 每步必须返回 `success`
   - 失败即报错，定位到具体步骤
3. 回放结束后运行目标 DSL，必须判定为 `completed`
4. 反向检查：初始快照直接跑目标 DSL 必须为 `not_completed`
5. 回放步数必须小于 `max_steps`
6. 校验通过后写入 `solvable: true` 与步数基线