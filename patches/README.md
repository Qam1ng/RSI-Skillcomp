# ASPIRE 本地补丁（ucla 克隆，上游不动）

| 补丁 | 内容 | 上游状态 |
|---|---|---|
| 0001 | libero adapter 数组真值判断修复 | 已提 issue #27 |
| 0002 | gpu_runtime 增加 sm_86 架构 | 已提 issue #28 |
| 0003 | **vla_act：π0.5 作为技能**——OSC_POSE 集放行（几何运动 API 禁用门）、vla_native_step 运行时步进、api.vla_act + 注册 + 允许清单、CAP_LIBERO_CONTROLLER 环境开关、vla_client.py（策略服务端客户端，观测拼法照抄 openpi）；终止语义遵守 "terminated 不得自称 ok" 契约 | 待整理成 PR 提案 |

0003 由 `git diff fa00f0e..HEAD -- src/`（ASPIRE 克隆内 7 次提交合并）导出；
0001/0002 的改动若已被该区间包含则以 0003 为准。
复现：v1.0 检出后 `git apply patches/0003-vla-act-skill.patch`，
再按 doc/active/substrate_contract_openpi.md 装 openpi-client 进 .venv-libero。
