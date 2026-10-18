# 2026-10-18 闸 1+2 完成：ASPIRE 在 ucla 复现跑通，适配器对表落地

## 结果（全程零 API 消耗）

- 闸 1：bootstrap（uv，7.4G，~4min）→ doctor 10/11 绿（services 项预期红）→ smoke 1/1 passed。
- 闸 2：三件套服务（sam3/pyroki/curobo）就绪；示例程序单集录制成功：
  `libero_object_swap/task0 seed1 → task_success=True, termination=task_succeeded, wall 35.1s`。
- 工件拖回本机（去视频），`span→Step` 映射对表核定，适配器实现 + 真实工件夹具 + 测试 11/11 过。

## 两个上游补丁（存 /data/qyan/skillcomp_work/patches/，待批后提 issue）

1. `0001`：`libero/adapter.py:438` 对 numpy 数组取真值崩溃 → `len(...)==0`（v1.0 仍在）。
2. `0002`：GPU 架构白名单只有 sm_89/sm_120（Ada/Blackwell）→ 合法新增 sm_86（Ampere A6000），
   配套 ucla-a6000 profile（三服务全钉 GPU 2，避开被占的 0 号卡）。

## 工件格式核定（适配器依据）

- 步级 = `trace/events.jsonl` 顶层 program span（parent_id 空）；`ok`/`duration_s` 在 span_end；
- 参数 = `trace/calls/call-NNNNNN-*/input.json`（与 span 同号）；
- 大模型回合 = `trace/model/turns.jsonl` 行数（录制程序为 0）；
- run.json: benchmark/suite/task_id/task_name/seed/status；只消费 status=finalized。

## 发现

- **任务成功 ≠ 每步成功**：这份成功工件里松爪与收尾撤离两步 ok=false。
  挖掘的"窗口内全成"过滤器对真实数据是必要的，不是多虑。
- 服务就绪端点是 `/openapi.json` 不是 `/health`（探针为此误报过一轮）。
- pkill -f 自匹配教训在 pkill 上重演一次（退出码 144）；方括号规矩同样适用。

## 待批事项

1. 闸 2.5（零 API）：用 run-batch 对同任务扫 seed 51–65（≈15 集 × 35s），
   得到第一份"重复协议"真实轨迹集 → 喂挖掘，看 ASPIRE 轨迹是否自发变短（预期：否，即 motivation 图）。
2. 闸 3（首笔 API）：Gemini flash 驱动 agent 环跑一个任务，跑完即停带成本账。
3. 两个补丁给 NVlabs/ASPIRE 提 issue（对外动作）。
