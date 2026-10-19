#!/usr/bin/env bash
# 口1 注入运行包装：把宏实现拼到程序头部，再原样调 cap-harness run。
# 用法: run_injected.sh <program.py> [cap-harness run 的其余参数...]
# 宏目录由 MACRO_DIR 指定（默认脚本同目录下的 macros/）。
set -euo pipefail
PROG="$1"; shift
MACRO_DIR="${MACRO_DIR:-$(dirname "$0")/macros}"
INJ="$(mktemp --suffix=_injected.py)"
cat "$MACRO_DIR"/*.py > "$INJ"
printf '\n\n' >> "$INJ"
cat "$PROG" >> "$INJ"
exec "${CAP_HARNESS:-cap-harness}" run --program "$INJ" "$@"
