# Scoreboard

已确立的数字（带出处）。玩具环境的数字不入此表。

| 日期 | 数字 | 条件 | 出处 |
|---|---|---|---|
| 2026-10-18 | ASPIRE 复现：doctor 10/11、smoke 1/1、单集 task_succeeded (35.1s) | ucla A6000(GPU2)，v1.0+两补丁，零 API | journal/20261018_gates12_aspire.md；工件 ~/skillcomp_data/aspire_runs |
| 2026-10-18 | 批量 15/15 成功，164s | libero_object_swap/0，seeds 51–65，seeded，录制示例程序 | ucla batch_summary.json；本地 aspire_batch/ |
| 2026-10-18 | 决策点恒 27（15 集 min=max），零压缩 | 同上（固定程序，平凡基线，正式版等 agent 驱动轨迹） | journal/20261018_gates25_3.md |
| 2026-10-18 | Gemini flash 修复环 3 轮全 program_error；17,871+4,611 tok，321s，约≤2美分（估算） | libero_goal_swap/0 seed51，api-doc-only 接地 | gate3/meter.json（ucla）；journal 同上 |
| 2026-10-19 | b 档战役：3 任务 2 成（spatial2 一发即中 6.3k+2.1k tok；goal2 两轮收敛 13.9k+2.8k tok；抽屉 5 轮未成 ~30k tok） | 驱动 v3（样例接地），seed 51，gemini-flash-latest | 各 meter.json（ucla gate3v3/c_spatial2/c_goal2）|
| 2026-10-19 | 收割 10/10（两获胜程序 × seeds51–55，seeded 布局） | 零 API | harvest_*/summary.json；本地 harvest_* |
| 2026-10-19 | 跨 3 任务 25 集：技能名层连续段（localize→state→move 等）覆盖 25/25；接地层跨任务命中 0 | 1 人写 + 2 agent 写程序 | journal/20261019_campaign.md |
| 2026-10-19 | 宏 pick_object 过执行门 5/5（EFF 口径，未见过的 seeds 56–60） | libero_goal_task/2，seeded；flash 两轮证据回流收敛 | verify_macro3/summary.json（ucla）；journal/20261019_macros.md |
| 2026-10-19 | 纯宏整任务 0/5 两次（flash 整体重生成）：place v2 代码退化成注释返回 None；pick v4 重抽几何回归 | 同上口径，verify_pure/verify_pure2 | journal/20261019_macros.md |
| 2026-10-19 | **纯宏整任务 5/5**：程序正文 = 2 次宏调用（pick_object + place_into，传递 below_grasp_m），任务判定来自基准检查器；每集 17 次原子调用在宏内执行 | libero_goal_task/2，未见过的 seeds 56–60，seeded；合成 gemini-pro-latest 各 1 次调用（pick 为"最小差分编辑"5.7k+0.9k tok，place 一发 4.3k+0.9k tok） | verify_pure3/summary.json（ucla）；macros/*.provenance.json |
| 2026-10-19 | 口1 试点（配对，双失败但次级信号强）：A 对照 5 轮 0 成（程序 54–58 调用/轮，输出 2.1–2.3k tok/轮，973s）；B 目录臂 5 轮 0 成，但 3/5 轮主动采用宏（6–14 调用、输出 193–249 tok，约 10 倍短），轮间在"宏↔裸API"间振荡，总墙钟 260s（3.7 倍快） | libero_goal_task/1"Put the plate on the stove"（预注册规则选取），seed 51，flash，≤5 轮，环内无人 | port1/arm{A,B}/meter.json（ucla）；doc/active/exp_port1_catalog_injection.md |
| 2026-10-21 | 纯宏整任务重放 5/5（带录像），steps 214–238 | libero_goal_task/2，seeds 56–60，seeded，零 API，ucla GPU2 | ~/skillcomp_data/demo_pure3/（视频在 videos/）；journal/20261021_demo_videos.md |
| 2026-10-25 | 带条件核查的纯宏整任务 5/5：PRE 事前核查 + EFF 事后核查在沙箱内运行期执行，裕度为连续量（抓取深度 0.114 m、松开裕度 0.586） | libero_goal_task/2，冻结种子 56–60，经执行模块 exec_aspire 发批（首次无手敲 ssh），零 API | verify_checked2/batch-results.jsonl（ucla）；journal/20261025_fill_gaps.md |
| 2026-10-25 | 新契约规则：沙箱禁止下划线开头的名字（整程序被拒），实测一轮即定位 | verify_checked1 全批 program_error → 修名后 5/5 | macros/substrate_contract_aspire.md 第 13 条 |
| 2026-10-25 | π0.5 载体点火：pi05_libero（12.4 GB）服务端起监听，客户端按 websocket 协议收到 (10,7) 动作块 | ucla GPU1，openpi 官方环境；坑两枚实测（系统 gsutil 是同名假货→匿名 gcsfs；fsspec 递归下载嵌套一层目录） | pi05_serve2.log、journal/20261025_fill_gaps.md |
| 2026-10-26 | **Gate 1 首片通过：π0.5（pi05_libero）亲自执行 29/30=96.7%**，官方口径 98.0%（n=30 抽样期望 29.4/30，口径吻合）；逐集视频存证，唯一失败（开中层抽屉）成为 VLA 病历第一条候选 | libero_goal × 每任务 3 回合，seed 7，openpi 官方评测客户端，服务端 GPU1 + 仿真 GPU2，零 API | vla_eval1.log 与 videos/（ucla）；data/ledger.jsonl 首条 VLA 台账 |
