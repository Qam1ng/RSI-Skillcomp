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
