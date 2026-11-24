# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""統計 rules/ 下每份 RuleFile 的 Rule 數量。"""

import argparse
import sys
import json
import re
from pathlib import Path


def count_rules(rule_file: Path) -> int:
    content = rule_file.read_text(encoding="utf-8")
    return len(re.findall(r"^## Rule \d+ -- ", content, flags=re.MULTILINE))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="統計 rules/ 下每份 RuleFile 的 Rule 數量。")
    parser.add_argument("rules_dir", help="RuleFile 所在的 rules/ 目錄")
    parser.add_argument("--min", type=int, default=0, help="只列出 Rule 數量大於等於此值的檔案")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    rules_dir = Path(args.rules_dir)
    if not rules_dir.is_dir():
        print(
            f"錯誤：找不到目錄 {rules_dir}。請傳入 skill 的 rules/ 目錄，"
            "例如 .claude/skills/skill-form-rule/rules",
            file=sys.stderr,
        )
        return 1
    rule_files = sorted(rules_dir.glob("*.md"))
    print(f"讀取 {len(rule_files)} 份 RuleFile", file=sys.stderr)
    result = [{"file": f.name, "rule_count": count_rules(f)} for f in rule_files]
    result = [item for item in result if item["rule_count"] >= args.min]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
