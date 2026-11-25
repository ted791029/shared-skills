# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""把 /bdd 的範疇（端點資料夾、feature、以行號或 Rule 名稱定位的 Rule、Example）展開為端點資料夾、用語表與 Example 行號清單。"""

import argparse
import json
import re
import sys
from pathlib import Path

FEATURE_KEYWORDS = ("Feature", "Business Need", "Ability", "功能")
RULE_KEYWORDS = ("Rule", "規則")
BACKGROUND_KEYWORDS = ("Background", "背景")
OUTLINE_KEYWORDS = ("Scenario Outline", "Scenario Template", "場景大綱", "劇本大綱")
SCENARIO_KEYWORDS = ("Scenario", "Example", "場景", "劇本")
EXAMPLES_KEYWORDS = ("Examples", "Scenarios", "例子")
RULE_NAME_SEPARATOR = "＞"  # 以 Rule 名稱定位：<feature 路徑> ＞ Rule「A」、Rule「B」
RULE_NAME_OPEN = "Rule「"
SCOPE_FORMS = (
    "端點資料夾（specs/truth/features/backend）、feature 路徑（specs/truth/features/backend/改答案.feature）、"
    "feature 路徑:行號[:行號…]（specs/truth/features/backend/改答案.feature:10），"
    "或 feature 路徑 ＞ Rule「名稱」[、Rule「名稱」…]（specs/truth/features/backend/改答案.feature ＞ Rule「確認改答案後，新答案必須生效」）"
)


def keyword_of(line: str, keywords: tuple[str, ...]) -> str | None:
    stripped = line.strip()
    for keyword in sorted(keywords, key=len, reverse=True):
        if re.match(rf"^{re.escape(keyword)}\s*[:：]", stripped):
            return keyword
    return None


def title_of(line: str) -> str:
    return re.split(r"[:：]", line.strip(), maxsplit=1)[1].strip()


def parse_feature(feature: Path) -> dict:
    """回傳 feature 的 Rule 區段與 Example 清單，Example 含行號、標題、種類與所屬 Rule 行號。"""
    lines = feature.read_text(encoding="utf-8").splitlines()
    rules: list[dict] = []
    examples: list[dict] = []
    feature_line = None
    current_rule = None
    current_outline = None
    in_examples = False
    header_seen = False
    in_docstring = None
    for number, raw in enumerate(lines, start=1):
        stripped = raw.strip()
        if in_docstring:
            if stripped.startswith(in_docstring):
                in_docstring = None
            continue
        if stripped.startswith('"""') or stripped.startswith("```"):
            in_docstring = stripped[:3]
            continue
        if stripped.startswith("|"):
            # 場景大綱 Examples 表：第一列是表頭，其後每列是一個例子（Playwright --list 每個例子列顯示為一個測試）
            if in_examples and current_outline is not None:
                if header_seen:
                    current_outline["example_rows"] += 1
                else:
                    header_seen = True
            continue
        if not stripped or stripped.startswith("#") or stripped.startswith("@"):
            continue
        if keyword_of(raw, FEATURE_KEYWORDS):
            feature_line = number
        elif keyword_of(raw, RULE_KEYWORDS):
            current_rule = {"line": number, "title": title_of(raw)}
            rules.append(current_rule)
        elif keyword_of(raw, EXAMPLES_KEYWORDS):
            in_examples = current_outline is not None
            header_seen = False
        elif keyword_of(raw, BACKGROUND_KEYWORDS):
            current_outline = None
            in_examples = False
        elif keyword_of(raw, OUTLINE_KEYWORDS):
            current_outline = {"line": number, "title": title_of(raw), "kind": "outline", "rule_line": current_rule["line"] if current_rule else None, "example_rows": 0}
            in_examples = False
            examples.append(current_outline)
        elif keyword_of(raw, SCENARIO_KEYWORDS):
            current_outline = None
            in_examples = False
            examples.append({"line": number, "title": title_of(raw), "kind": "scenario", "rule_line": current_rule["line"] if current_rule else None})
    return {"feature_line": feature_line, "rules": rules, "examples": examples}


def find_endpoint_dir(target: Path) -> Path | None:
    start = target if target.is_dir() else target.parent
    for candidate in (start, *start.parents):
        if (candidate / "dsl.md").is_file():
            return candidate
    return None


def find_glossary(endpoint_dir: Path) -> Path | None:
    for candidate in (endpoint_dir, *endpoint_dir.parents):
        if (candidate / "用語表.md").is_file():
            return candidate / "用語表.md"
    return None


def select_examples(feature: Path, parsed: dict, line: int) -> list[dict]:
    if line == parsed["feature_line"] or line == 1:
        return parsed["examples"]
    rule_lines = {rule["line"] for rule in parsed["rules"]}
    if line in rule_lines:
        return [example for example in parsed["examples"] if example["rule_line"] == line]
    matched = [example for example in parsed["examples"] if example["line"] == line]
    if matched:
        return matched
    raise ValueError(
        f"{feature.as_posix()}:{line} 不是 Feature、Rule、Example（場景）或場景大綱的標題行。"
        "請改用這些標題行的行號；場景大綱請指定大綱標題行，不要指定例子表格的列。"
    )


def parse_rule_names(text: str) -> list[str]:
    """解析「Rule「A」、Rule「B」」。名稱可含成對的「」與頓號，只有括號外的「、」是分隔。"""
    names: list[str] = []
    index = 0
    text = text.strip()
    while True:
        if not text.startswith(RULE_NAME_OPEN, index):
            raise ValueError(f"「{RULE_NAME_SEPARATOR}」之後必須是 Rule「名稱」，多條 Rule 以「、」接續，收到：{text[index:] or '（空白）'}")
        index += len(RULE_NAME_OPEN)
        start, depth = index, 1
        while index < len(text) and depth:
            depth += {"「": 1, "」": -1}.get(text[index], 0)
            index += 1
        if depth:
            raise ValueError(f"Rule 名稱缺少收尾的括號「」」：Rule「{text[start:]}；請確認名稱的括號成對。")
        name = text[start:index - 1].strip()
        if not name:
            raise ValueError("Rule「」中的 Rule 名稱是空的，請照 feature 的「Rule:」行寫出完整名稱。")
        names.append(name)
        rest = text[index:].lstrip()
        if not rest:
            return names
        if not rest.startswith("、"):
            raise ValueError(f"Rule「{name}」之後只能接「、Rule「…」」，收到：{rest}")
        index = len(text) - len(rest) + 1
        while index < len(text) and text[index].isspace():
            index += 1


def parse_scope(scope: str) -> tuple[Path, list[int], list[str]]:
    """範疇原文 → （路徑、行號清單、Rule 名稱清單）；三種寫法同時只會有一種非空。"""
    if RULE_NAME_SEPARATOR in scope:
        path_text, _, rules_text = scope.partition(RULE_NAME_SEPARATOR)
        path_text = path_text.strip()
        if not path_text.endswith(".feature"):
            raise ValueError(f"以 Rule 名稱定位時，「{RULE_NAME_SEPARATOR}」之前必須是 .feature 路徑（不可帶行號），收到：{path_text}")
        return Path(path_text), [], parse_rule_names(rules_text)
    match = re.match(r"^(.*?\.feature)((?::\d+)+)$", scope)
    if match:
        return Path(match.group(1)), [int(n) for n in match.group(2).strip(":").split(":")], []
    return Path(scope), [], []


def select_scope_examples(feature: Path, parsed: dict, lines: list[int], rule_names: list[str]) -> list[dict]:
    """依行號或 Rule 名稱選出 Example；兩者皆空時為整份 feature。結果依行號排序、不重複。"""
    if not lines and not rule_names:
        return list(parsed["examples"])
    chosen: dict[int, dict] = {}
    for line in lines:
        for example in select_examples(feature, parsed, line):
            chosen[example["line"]] = example
    if rule_names:
        by_title: dict[str, list[int]] = {}
        for rule in parsed["rules"]:
            by_title.setdefault(rule["title"], []).append(rule["line"])
        for name in rule_names:
            rule_lines = by_title.get(name)
            if not rule_lines:
                titles = "；".join(rule["title"] for rule in parsed["rules"]) or "（這份 feature 沒有 Rule）"
                raise ValueError(f"{feature.as_posix()} 沒有名稱為「{name}」的 Rule；名稱必須與「Rule:」行逐字相同。這份 feature 的 Rule：{titles}")
            if len(rule_lines) > 1:
                raise ValueError(f"{feature.as_posix()} 有 {len(rule_lines)} 條名稱為「{name}」的 Rule（第 {'、'.join(map(str, rule_lines))} 行），無法以名稱定位，請改用行號。")
            for example in parsed["examples"]:
                if example["rule_line"] == rule_lines[0]:
                    chosen[example["line"]] = example
    return [chosen[number] for number in sorted(chosen)]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把 /bdd 的範疇展開為端點資料夾、用語表與 Example 行號清單（每份 feature 附 run_targets：每個元素是一個 feature:行號，behave 1.3.3 不接受 feature:行1:行2，必須各自成為獨立參數；另附 Playwright --list 預檢應列出的測試數）。"
        "step 目錄與執行指令不在輸出中，由專案測試設定判定。"
    )
    parser.add_argument("scope", help=f"範疇，整段以引號包成一個參數：{SCOPE_FORMS}；行號為 Rule、Example 或場景大綱的標題行，Rule 名稱與 feature 的「Rule:」行逐字相同")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        target, line_numbers, rule_names = parse_scope(args.scope)
    except ValueError as error:
        print(f"錯誤：{error}\n範疇的寫法：{SCOPE_FORMS}", file=sys.stderr)
        return 1
    if not target.exists():
        print(
            f"錯誤：找不到範疇 {target.as_posix()}。範疇的寫法：{SCOPE_FORMS}",
            file=sys.stderr,
        )
        return 1
    endpoint_dir = find_endpoint_dir(target)
    if endpoint_dir is None:
        print(
            f"錯誤：{target.as_posix()} 與其上層資料夾都沒有 dsl.md，無法判定端點資料夾。"
            "請確認範疇位於 dsl-refine 產出的端點資料夾（含 dsl.md）底下。",
            file=sys.stderr,
        )
        return 1
    if target.is_dir():
        features = sorted(target.rglob("*.feature"))
        if not features:
            print(f"錯誤：{target.as_posix()} 底下沒有任何 .feature 檔，請確認範疇路徑。", file=sys.stderr)
            return 1
        selections = [(feature, parse_feature(feature)["examples"]) for feature in features]
    else:
        try:
            selections = [(target, select_scope_examples(target, parse_feature(target), line_numbers, rule_names))]
        except ValueError as error:
            print(f"錯誤：{error}", file=sys.stderr)
            return 1
    result_features = []
    total = 0
    total_tests = 0
    for feature, examples in selections:
        if not examples:
            continue
        total += len(examples)
        # Playwright --list 預檢：每個場景一個測試，場景大綱每個例子列一個測試
        listed_tests = sum(e["example_rows"] if e["kind"] == "outline" and e["example_rows"] else 1 for e in examples)
        total_tests += listed_tests
        result_features.append({
            "feature": feature.as_posix(),
            "run_targets": [f"{feature.as_posix()}:{e['line']}" for e in examples],
            "playwright_list_count": listed_tests,
            "examples": [
                {"line": e["line"], "title": e["title"], "kind": e["kind"], "rule_line": e["rule_line"],
                 **({"example_rows": e["example_rows"]} if e["kind"] == "outline" else {})}
                for e in examples
            ],
        })
    if total == 0:
        print(f"錯誤：範疇 {args.scope} 內沒有任何 Example，請確認行號、Rule 名稱或路徑。", file=sys.stderr)
        return 1
    print(f"範疇內共 {total} 個 Example，分布於 {len(result_features)} 份 feature", file=sys.stderr)
    glossary = find_glossary(endpoint_dir)
    print(json.dumps({
        "endpoint_dir": endpoint_dir.as_posix(),
        "glossary": glossary.as_posix() if glossary else None,
        "example_count": total,
        "playwright_list_count": total_tests,
        "features": result_features,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
