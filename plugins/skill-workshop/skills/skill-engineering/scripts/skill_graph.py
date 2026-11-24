# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""解析 skills 目錄下每個 SKILL.md 的 SOP 掛載連結，列出各 Step 的掛載、跨 skill 呼叫、失效連結與孤兒檔案。"""

import argparse
import json
import re
import sys
from pathlib import Path

PHASE_PATTERN = re.compile(r"^###\s+Phase\s+(\d+)\s+---\s+(.+?)\s*$")
STEP_PATTERN = re.compile(r"^(\d+)\.\s+([A-Z]+)\s")
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
PART_DIRS = ("rules", "templates", "scripts")


def classify(target: Path, skill_dir: Path, skills_dir: Path) -> str:
    if not target.exists():
        return "broken"
    if target.is_relative_to(skill_dir):
        return "internal"
    if target.is_relative_to(skills_dir):
        return "cross_skill"
    return "external"


def analyze_skill(skill_dir: Path, skills_dir: Path) -> dict:
    skill_md = skill_dir / "SKILL.md"
    mounts = []
    mounted = set()
    phase = None
    for line_no, line in enumerate(skill_md.read_text(encoding="utf-8").splitlines(), start=1):
        phase_match = PHASE_PATTERN.match(line)
        if phase_match:
            phase = int(phase_match.group(1))
            continue
        step_match = STEP_PATTERN.match(line)
        for text, href in LINK_PATTERN.findall(line):
            if "://" in href or href.startswith("#"):
                continue
            target = (skill_dir / href).resolve()
            kind = classify(target, skill_dir, skills_dir)
            if kind == "internal":
                mounted.add(target)
            mounts.append({
                "line": line_no,
                "phase": phase,
                "step": int(step_match.group(1)) if step_match else None,
                "verb": step_match.group(2) if step_match else None,
                "text": text,
                "href": href,
                "kind": kind,
            })
    orphans = [
        path.relative_to(skill_dir).as_posix()
        for part in PART_DIRS
        for path in sorted((skill_dir / part).rglob("*"))
        if path.is_file() and path.resolve() not in mounted and "__pycache__" not in path.parts
    ]
    return {
        "skill": skill_dir.name,
        "mounts": mounts,
        "calls": sorted({m["href"] for m in mounts if m["kind"] == "cross_skill"}),
        "broken": [m for m in mounts if m["kind"] == "broken"],
        "orphans": orphans,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="解析 skills 目錄下每個 SKILL.md 的 SOP 掛載連結，列出各 Step 的掛載、跨 skill 呼叫、失效連結與孤兒檔案。")
    parser.add_argument("skills_dir", help="skills 根目錄，例如 .claude/skills")
    parser.add_argument("--skill", action="append", default=[], help="只輸出指定 skill，可重複指定")
    parser.add_argument("--issues-only", action="store_true", help="只輸出失效連結與孤兒檔案")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    skills_dir = Path(args.skills_dir).resolve()
    if not skills_dir.is_dir():
        print(f"錯誤：找不到目錄 {skills_dir}。請傳入 skills 根目錄，例如 .claude/skills", file=sys.stderr)
        return 1
    skill_dirs = sorted(p.parent for p in skills_dir.glob("*/SKILL.md"))
    if args.skill:
        names = {d.name for d in skill_dirs}
        missing = [name for name in args.skill if name not in names]
        if missing:
            print(f"錯誤：找不到 skill {', '.join(missing)}。可用的 skill：{', '.join(sorted(names))}", file=sys.stderr)
            return 1
        skill_dirs = [d for d in skill_dirs if d.name in args.skill]
    print(f"解析 {len(skill_dirs)} 個 skill", file=sys.stderr)
    result = [analyze_skill(d, skills_dir) for d in skill_dirs]
    if args.issues_only:
        result = [
            {"skill": r["skill"], "broken": r["broken"], "orphans": r["orphans"]}
            for r in result
            if r["broken"] or r["orphans"]
        ]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
