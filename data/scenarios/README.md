# 场景包 JSON 规范 v0

## 文件约定

- 场景包位于 `data/scenarios/<scenario_id>.json`
- 任务包位于 `data/tasks/<scenario_id>/<task_id>.json`
- 所有 ID 使用 `snake_case`，实体 ID 使用 `<class>_<序号>` 格式

## 顶层结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `scenario_id` | string | ✅ | 场景唯一标识，如 `home_01` |
| `spec_version` | string | ✅ | 规范版本，当前 `0.1` |
| `name` | string | ✅ | 场景中文名 |
| `description` | string | ❌ | 场景描述 |
| `areas` | Area[] | ✅ | 全部可见区域列表 |
| `area_adjacency` | Adjacency[] | ✅ | 区域连通关系 |
| `area_tables` | {area_id: Entity[]} | ✅ | 每个区域一张实体表 |
| `robot` | Robot | ✅ | 机器人初始状态 |

## Area

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 区域唯一 ID |
| `name` | string | ✅ | 区域中文名 |

## Adjacency

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `from` | string | ✅ | 源区域 ID，必须在 `areas` 中存在 |
| `to` | string | ✅ | 目标区域 ID，必须在 `areas` 中存在 |
| `passable` | bool | ✅ | 是否可通行 |

约束：连通关系为**无向**，即 `{from: A, to: B}` 等价于 `{from: B, to: A}`。

## Entity

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `id` | string | ✅ | 实体唯一 ID，全局唯一 |
| `class` | string | ✅ | 实体类别（见下方枚举） |
| `name` | string | ✅ | 实体中文名 |
| `pickable` | bool | ✅ | 是否可拾取 |
| `on` | string | ❌ | 放置于某实体上（表面），引用同区域实体 ID |
| `in` | string | ❌ | 放置于某容器内，引用同区域实体 ID |
| `is_device` | bool | ❌ | 是否可作为设备（默认 false） |
| `open_state` | string | ❌ | 可开合实体的开闭状态：`open` / `closed`；不填视为常开（内部始终可见，如无盖衣筐） |
| `device_state` | string | ❌ | 设备运行状态：`off` / `running` |
| `properties` | string[] | ❌ | 物理属性列表（见下方枚举） |
| `states` | object | ❌ | 自定义状态键值对 |

约束：
- `on` 和 `in` 互斥，不能同时存在
- `on` 引用的实体必须 `properties` 包含 `can_support`（表面）
- `in` 引用的实体必须 `properties` 包含 `can_contain`（容器）
- 引用关系不能形成环

注意区分表面与容器：沙发、床、鞋架只标 `can_support`（东西放在上面）；收纳箱、衣柜只标 `can_contain`（东西放进里面）；洗衣机顶部可放物、内桶可容物，两者都标。

### 实体类别（class 枚举）

| 值 | 说明 |
|----|------|
| `furniture` | 家具（床、沙发、桌子等） |
| `container` | 容器（收纳箱、衣筐、衣柜等） |
| `device` | 设备（洗衣机、电视、灯等） |
| `clothing` | 衣物 |
| `item` | 一般物品（杂志、枕头、毛巾等） |
| `consumable` | 消耗品（洗衣液、肥皂等，使用后会减少） |
| `tool` | 工具（遥控器、衣架、雨伞等） |
| `fixture` | 固定设施（洗手池、马桶、镜子等） |

### 物理属性（properties 枚举）

命名约定：**接收方能力用 `can_*`**（能对别的物品做什么），**物品自身特性用 `*able`**（自身可以被怎样）。两者方向不可混用，例如洗衣机是 `can_wash`（能洗东西），衣物是 `washable`（可被洗）。

| 值 | 方向 | 说明 |
|----|------|------|
| `can_support` | 接收方 | 可在其上放置物品（床、茶几、鞋架等表面） |
| `can_contain` | 接收方 | 可容纳物品（收纳箱、衣柜、洗衣机内桶等容器） |
| `can_hang` | 接收方 | 可供悬挂物品（晾衣架等） |
| `can_wash` | 接收方 | 可洗涤放入的物品（洗衣机等） |
| `hangable_inside` | 接收方 | 内部可悬挂（衣柜等） |
| `has_water` | 接收方 | 有水源（洗手池等） |
| `portable` | 物品 | 可整体搬运（容器本身可被拾取） |
| `absorbent` | 物品 | 可吸水（毛巾、衣物、门垫等） |
| `soft` | 物品 | 柔软 |
| `waterproof` | 物品 | 防水 |
| `hangable` | 物品 | 自身可被悬挂（衣架、衣物等） |
| `washable` | 物品 | 自身可被洗涤（衣物、毛巾等） |

### 设备状态转移

`device_state` 仅两个值：`off`（待机/关闭）与 `running`（运行中）。

- `start_device`：`off` → `running`；若设备有 `open_state`，须为 `closed` 才能启动（如洗衣机门未关不能启动）
- `stop_device`：`running` → `off`

## Robot

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `location` | string | ✅ | 初始所在区域 ID |
| `left_hand` | string\|null | ✅ | 左手持有实体 ID（null 为空） |
| `right_hand` | string\|null | ✅ | 右手持有实体 ID（null 为空） |

## 校验规则（compile 阶段执行）

### S1. 实体 ID 全局唯一
遍历所有 `area_tables` 中的实体，收集所有 `id`，不得有重复。

### S2. 实体 ID 引用有效
所有 `on`、`in`、`robot.left_hand`、`robot.right_hand` 引用的实体 ID 必须在某个 `area_tables` 中存在。

### S3. 放置关系闭合
- `on` 引用的实体必须 `properties` 含 `can_support`
- `in` 引用的实体必须 `properties` 含 `can_contain`
- 引用链不能形成环（A→B→C→A）

### S4. 邻接图连通
以 `areas` 为节点、`area_adjacency` 中 `passable: true` 的边构建无向图，必须全连通（从任意节点可达任意其他节点）。

### S5. 机器人初始位置合法
`robot.location` 必须在 `areas` 中存在。

### S6. 区域 ID 引用有效
`area_adjacency` 中所有 `from`、`to` 必须在 `areas` 中存在。

### S7. 实体状态字段合法
`states` 中的键值必须为 JSON 基本类型（string/number/boolean/null），不得嵌套对象。

## 观测约定（观测生成器执行，非编译期校验）

- `open_state` 为 `open` 或无 `open_state` 的容器，其内部实体（`in` 引用）在观测中可见
- `open_state` 为 `closed` 的容器，其内部实体在观测中不可见（直到 `open_container` 动作执行）