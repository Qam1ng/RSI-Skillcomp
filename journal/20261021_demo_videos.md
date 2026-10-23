# 2026-10-21：补录仿真 demo 视频（纯宏 5/5 重放）

## 为什么此前没有视频
- ASPIRE 默认每集录 agentview / robot0_eye_in_hand 两路 MP4（20 fps，800×512）。
- `tools/aspire_gemini_driver.py` 的 run_episode 写死 `--no-videos`，10/18 冒烟之后所有批量
  （收割、verify_macro*、verify_pure*、port1）都走这条路，run.json 里 `capture.profile = no_videos`。
- 10/18 冒烟跑（object_swap/0 seed 1）有录像，但本地同步时没拷 mp4。

## 本次做了什么（零 API）
- ucla GPU2，用 `pure_macro3.py` 原程序、同任务同种子重放，去掉 `--no-videos`：
  `cap-harness run --benchmark libero-pro --suite libero_goal_task --task-id 2 --seed {56..60}
   --program pure_macro3.py --output-root /data/qyan/skillcomp_work/demo_pure3 --flat-run-dir`
- 结果 5/5 task_succeeded（steps_executed 238/214/223/224/233），与 10/19 verify_pure3 一致。
- 拉回本地：`~/skillcomp_data/demo_pure3/`（完整运行目录）+ `videos/`（扁平命名的 10 路 mp4、
  5 集顺序拼接 `pure_macro_5seeds_sequence.mp4` 56.9s、5 集并排 `pure_macro_5seeds_grid.mp4`）。
- 冒烟跑的两路 mp4 拉到 `~/skillcomp_data/smoke_video/`（固定示例程序，非宏，仅作素材）。

## 勘误
- 此前 journal 把 goal_task/2 写成"酒瓶入碗"，任务目录真名是
  `02-put-the-wine-bottle-on-top-of-the-cabinet`（把酒瓶放到柜子上）。以目录名为准。

## 待办
- 以后要出视频的批次，驱动里把 `--no-videos` 做成开关而不是写死。
