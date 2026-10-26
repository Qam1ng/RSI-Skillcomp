#!/bin/bash
# 内循环生产线：任务卡 → planner 写程序 → OSC 集执行 → trace 落盘。
# 用法（在 ucla 上）：GEMINI_API_KEY=... ./produce_vla.sh <tasks.tsv> <out_root> [max_rounds]
# tasks.tsv 每行 "task_id<TAB>task_language"（由 cap-harness manifest 导出，别手抄）。
set -euo pipefail
TASKS="$1"; OUT="$2"; ROUNDS="${3:-2}"
cd "$(dirname "$0")"
# 注意 || [ -n "$TID" ]：吞掉末行无换行符的坑（task 9 教训，2026-10-26）
while IFS=$'\t' read -r TID LANG || [ -n "${TID:-}" ]; do
  [ -z "${TID:-}" ] && continue
  echo "=== task $TID: $LANG"
  python3 aspire_gemini_driver.py --aspire-root /data/qyan/skillcomp_work/ASPIRE \
    --suite libero_goal_task --task-id "$TID" --seed 51 \
    --task-language "$LANG" --osc --extra-doc vla_act_card.md \
    --max-rounds "$ROUNDS" --out "$OUT/task$TID"
done < "$TASKS"
echo VLA_PROD_DONE
