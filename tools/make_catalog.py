#!/usr/bin/env python3
"""从 macros/*.py 生成口1 目录技能文件（给满血 coding-agent 臂读的 SKILL 形式 markdown）。

目录只含签名/PRE/EFF/NOTE/返回键——实现不进提示；执行时由 run_injected.sh 拼到程序头。
用法: python3 tools/make_catalog.py --macros macros/pick_object.py macros/place_into.py \
        --out /path/catalog_skill.md --wrapper /path/run_injected.sh
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from aspire_gemini_driver import macro_card  # noqa: E402

HEADER = """# Verified Skill Catalog (composition layer, port 1)

The runtime provides the functions below as PREDEFINED, EXECUTION-VERIFIED skills
(do NOT redefine them). Each was verified on unseen seeds of this benchmark; provenance
sits next to each macro as `<name>.provenance.json`.

Prefer calling a catalog skill over re-implementing its effect with the raw API; fall back
to the raw API only for what the catalog does not cover. Check `['ok']` of every call.

To execute a program that uses these skills, run it through the injection wrapper
(it prepends the implementations, then calls cap-harness unchanged):

    {wrapper} <program.py> [cap-harness run args...]

## Skills
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--macros", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wrapper", default="run_injected.sh")
    args = ap.parse_args()

    parts = [HEADER.format(wrapper=args.wrapper)]
    for mp in args.macros:
        p = Path(mp)
        _, card = macro_card(p.read_text())
        prov = {}
        pj = p.with_suffix("").with_suffix("")  # strip .py
        prov_path = p.parent / (p.stem + ".provenance.json")
        if prov_path.exists():
            prov = json.loads(prov_path.read_text())
        ver = prov.get("execution_verification", {})
        parts.append("```\n" + card + "\n```\n"
                     f"- verified: {ver.get('passes', prov.get('status', 'unknown'))} "
                     f"({ver.get('where', '')})\n")
    Path(args.out).write_text("\n".join(parts))
    print(f"目录已生成: {args.out} ({len(args.macros)} 个技能)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
