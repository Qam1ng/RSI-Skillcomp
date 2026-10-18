# 轨迹格式 v0（协议）

状态：v0 定稿 2026-10-18。改动需过讨论。
一式三用：harness 适配器的输出规范 / 测量打点格式 / 合成器输入。

## Trace（一次任务执行）

| 字段 | 类型 | 说明 |
|---|---|---|
| task | str | 任务标识（用 benchmark 官方命名，不自造） |
| steps | list[Step] | 按执行顺序 |
| success | bool | 任务级成败（按 benchmark 官方判定） |
| meta | dict | 必填：harness 名、episode 编号、seed；选填：模型名、总耗时 |

## Step（一次技能调用）

| 字段 | 类型 | 说明 |
|---|---|---|
| skill | str | 技能名（harness 侧原名，不翻译） |
| args | list[str] | 接地参数 |
| pre_snapshot | list[str] | 调用前为真的谓词集合；拿不到就留空（触发 observed 模式） |
| post_snapshot | list[str] | 调用后为真的谓词集合 |
| success | bool | 这一步的成败（按 harness 自己的判定；judge 来源记入 meta） |
| duration_s | float | 墙钟 |
| llm_calls | int | 这一步消耗的大模型调用数（测"决策点"的原料） |

## 谓词书写

接地字符串，形如 `drawer_open`、`in_drawer(cup)`。参数名用场景内一致的物体标识。
谓词从哪来（仿真器状态 / 感知估计 / 人工标注）必须写进 Trace.meta["predicate_source"]。

## 存储

JSONL，一行一条 Trace。读写见 `skillcomp/trace.py`。
