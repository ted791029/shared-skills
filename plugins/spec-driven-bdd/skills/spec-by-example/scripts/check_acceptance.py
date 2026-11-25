# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""檢查 plan 資料夾 features/acceptance/ 底下驗收 feature 的 AC 編號（不得重複）、每份 PM 提出的 Example 數（2 至 3 個）、澄清標籤數量（合計至多 10 個，澄清後必須為 0）與格式、涵蓋的需求編號、起點句與 Background、殘留填位符號；
標 @開發發現 的 Example 以 `# 開發發現：` 註解取代涵蓋註解，不計入 Example 數；輸出新增 AC 應使用的下一個編號，以及沒有被任何 AC 涵蓋的使用者故事、FR 與 NFR。"""

import argparse
import json
import re
import sys
from pathlib import Path

EXAMPLE_PATTERN = re.compile(r"^\s*(Example|Scenario|Scenario Outline):\s*(.*)$")
AC_TITLE_PATTERN = re.compile(r"^AC-(\d{2,})\s+\S")
COVER_PATTERN = re.compile(r"^\s*# 涵蓋：(.+)$")
FINDING_NOTE_PATTERN = re.compile(r"^\s*#\s*開發發現\s*[：:]")
FINDING_TAG = "@開發發現"
CITED_AC_PATTERN = re.compile(r"(?<![A-Za-z0-9])AC-(\d+)(?!\d)")
CLARIFY_TAG = "[NEED CLARIFICATION]"
CLARIFY_PATTERN = re.compile(r"^\s*# \[NEED CLARIFICATION\] .+？暫以「.+」撰寫$")
START_STEP_PATTERN = re.compile(r'^\s*Given 系統處於 "[^"]+"$')
RULE_PATTERN = re.compile(r"^\s*Rule:\s*(.+)$")
STEP_OR_TABLE_PATTERN = re.compile(r"^\s*(Given|When|Then|And|But|\|)")
SECTION_PATTERN = re.compile(r"^\s*(Rule|Example|Scenario|Scenario Outline|Feature):")
MIN_EXAMPLES, MAX_EXAMPLES = 2, 3
MAX_CLARIFY = 10
TRUTH_CHANGES = "truth-changes.md"
ID_ORDER = {"US": 0, "FR": 1, "NFR": 2}


def spec_ids(spec_text: str) -> tuple[set[str], set[str]]:
    stories = {f"US{n}" for n in re.findall(r"^###\s*使用者故事\s*(\d+)", spec_text, flags=re.MULTILINE)}
    requirements = set(re.findall(r"\*\*((?:NFR|FR)-\d{3})\*\*", spec_text))
    return stories, requirements


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def header_lines(lines: list[str], index: int) -> list[tuple[int, str]]:
    """Example 上方緊接的註解與標籤行（由近到遠），遇到空行或其他內容即停止。"""
    found = []
    for i in range(index - 1, -1, -1):
        stripped = lines[i].strip()
        if not stripped or not stripped.startswith(("#", "@")):
            break
        found.append((i, lines[i]))
    return found


def next_content_line(lines: list[str], index: int) -> tuple[int, str] | None:
    for i in range(index + 1, len(lines)):
        if lines[i].strip():
            return i, lines[i]
    return None


def first_step_after(lines: list[str], index: int) -> tuple[int, str] | None:
    for i in range(index + 1, len(lines)):
        if SECTION_PATTERN.match(lines[i]):
            return None
        stripped = lines[i].strip()
        if stripped and not stripped.startswith("#"):
            return i, lines[i]
    return None


def check_starts(lines: list[str], rel: str, issues: list[dict]) -> None:
    backgrounds = [i for i, line in enumerate(lines) if line.strip() == "Background:"]
    if len(backgrounds) > 1:
        issues.append({"file": rel, "line": backgrounds[1] + 1,
                       "message": f"Background 最多一個，目前有 {len(backgrounds)} 個"})
        return
    example_starts = [(i, first_step_after(lines, i)) for i, line in enumerate(lines) if EXAMPLE_PATTERN.match(line)]
    if backgrounds:
        steps = []
        for i in range(backgrounds[0] + 1, len(lines)):
            if SECTION_PATTERN.match(lines[i]):
                break
            stripped = lines[i].strip()
            if stripped and not stripped.startswith("#"):
                steps.append((i, lines[i]))
        if len(steps) != 1 or not START_STEP_PATTERN.match(steps[0][1]):
            line_no = steps[0][0] + 1 if steps else backgrounds[0] + 1
            issues.append({"file": rel, "line": line_no,
                           "message": 'Background 只能有一句起點句 `Given 系統處於 "<起點名稱>"`；起點內容寫在上方的 `# 預設值：` 註解，其他前提改寫成 Example 的 Given 差異句'})
        for _, step in example_starts:
            if step and START_STEP_PATTERN.match(step[1]):
                issues.append({"file": rel, "line": step[0] + 1,
                               "message": "已有 Background 時 Example 第一句不得再是起點句；起點不同時改為刪除 Background，由每個 Example 第一句各寫起點句"})
        return
    starts = []
    for example_line, step in example_starts:
        if not step or not START_STEP_PATTERN.match(step[1]):
            line_no = step[0] + 1 if step else example_line + 1
            issues.append({"file": rel, "line": line_no,
                           "message": '沒有 Background 時每個 Example 第一句必須是起點句 `Given 系統處於 "<起點名稱>"`，起點內容寫在上方的 `# 預設值：` 註解'})
        else:
            starts.append(step[1].strip())
    if len(example_starts) >= 2 and len(starts) == len(example_starts) and len(set(starts)) == 1:
        issues.append({"file": rel, "line": example_starts[0][1][0] + 1,
                       "message": f"所有 Example 都從同一個起點出發（{starts[0]}），應抽成 Background 並刪除各 Example 的起點句"})


def check_feature(path: Path, rel: str, stories: set[str], requirements: set[str], issues: list[dict]) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    check_starts(lines, rel, issues)
    examples, clarify_count, rule_names = [], 0, {}
    for i, line in enumerate(lines):
        if "{{" in line or "}}" in line:
            issues.append({"file": rel, "line": i + 1, "message": "殘留 {{}} 填位符號，請換成實際內容"})
        if rule := RULE_PATTERN.match(line):
            name = rule.group(1).strip()
            if name in rule_names:
                issues.append({"file": rel, "line": i + 1,
                               "message": f"Rule「{name}」在第 {rule_names[name]} 行已出現；同一條規則只開一個 Rule 區塊，請把 Example 移到第一個區塊"})
            rule_names.setdefault(name, i + 1)
        if CLARIFY_TAG in line:
            clarify_count += 1
            if not CLARIFY_PATTERN.match(line):
                issues.append({"file": rel, "line": i + 1,
                               "message": "澄清標籤格式必須為 `# [NEED CLARIFICATION] <問題>？暫以「<暫定假設>」撰寫`"})
            following = next_content_line(lines, i)
            if not following or not STEP_OR_TABLE_PATTERN.match(following[1]):
                issues.append({"file": rel, "line": i + 1, "message": "澄清標籤下一行必須是受影響的步驟或表格列"})
            elif indent_of(following[1]) != indent_of(line):
                issues.append({"file": rel, "line": i + 1,
                               "message": f"澄清標籤縮排 {indent_of(line)} 格，必須與下一行的步驟或表格同為 {indent_of(following[1])} 格"})
        match = EXAMPLE_PATTERN.match(line)
        if not match:
            continue
        keyword, title = match.group(1), match.group(2).strip()
        if keyword != "Example":
            issues.append({"file": rel, "line": i + 1,
                           "message": f"驗收案例只能用 `Example:`，不得用 `{keyword}:`；每個驗收案例都是一段完整旅程"})
        ac = AC_TITLE_PATTERN.match(title)
        if not ac:
            issues.append({"file": rel, "line": i + 1, "message": f"Example 標題必須為 `AC-NN <資料情境>`，收到「{title}」"})
        header = header_lines(lines, i)
        finding = any(FINDING_TAG in text for _, text in header if text.strip().startswith("@"))
        covered = []
        if finding:
            if not any(FINDING_NOTE_PATTERN.match(text) for _, text in header):
                issues.append({"file": rel, "line": i + 1,
                               "message": "標 @開發發現 的 Example 上方必須有 `# 開發發現：<發現的 skill>；<依據>` 註解；這個 AC 由 dev-finding 維護，請不要改動它，交由 dev-finding 修正"})
        else:
            cover = next(((index, found) for index, text in header if (found := COVER_PATTERN.match(text))), None)
            if cover is None:
                issues.append({"file": rel, "line": i + 1, "message": "Example 上方必須有 `# 涵蓋：US<n>、FR-<nnn>、NFR-<nnn>…`"})
            else:
                cover_index, cover_match = cover
                covered = [token.strip() for token in re.split(r"[、,，]", cover_match.group(1)) if token.strip()]
                if not any(token.startswith("US") for token in covered):
                    issues.append({"file": rel, "line": cover_index + 1, "message": "涵蓋註解至少要列出一個使用者故事（US<n>）"})
                for token in covered:
                    if re.fullmatch(r"US\d+", token):
                        if token not in stories:
                            issues.append({"file": rel, "line": cover_index + 1, "message": f"涵蓋的 {token} 不存在於 spec.md 的使用者故事"})
                    elif re.fullmatch(r"(NFR|FR)-\d{3}", token):
                        if token not in requirements:
                            kind = "非功能性需求" if token.startswith("NFR") else "功能需求"
                            issues.append({"file": rel, "line": cover_index + 1, "message": f"涵蓋的 {token} 不存在於 spec.md 的{kind}"})
                    else:
                        issues.append({"file": rel, "line": cover_index + 1,
                                       "message": f"涵蓋註解只列 US<n>、FR-<nnn> 與 NFR-<nnn>，收到「{token}」；SC 是量測指標，不列入涵蓋"})
        examples.append({"id": f"AC-{ac.group(1)}" if ac else None, "number": int(ac.group(1)) if ac else None,
                         "title": title, "line": i + 1, "covers": covered, "finding": finding})
    proposed = [example for example in examples if not example["finding"]]
    if proposed and not MIN_EXAMPLES <= len(proposed) <= MAX_EXAMPLES:
        issues.append({"file": rel, "line": 1,
                       "message": f"每份 feature 必須有 {MIN_EXAMPLES} 至 {MAX_EXAMPLES} 個 PM 提出的 Example（標 @開發發現 的不計入），目前 {len(proposed)} 個；"
                                  "超過時挑出最關鍵的旅程，只有一段旅程會走到不同結果的功能不另開 feature"})
    return {"file": rel, "examples": examples, "clarifications": clarify_count}


def check_ac_numbers(features: list[dict], issues: list[dict]) -> list[str]:
    """AC 編號在這個 plan 的所有 feature 中不得重複；開發發現的 AC 被刪除後編號不重用，所以允許空號。"""
    seen: dict[int, str] = {}
    for feature in features:
        for example in feature["examples"]:
            number = example["number"]
            if number is None:
                continue
            if number in seen:
                issues.append({"file": feature["file"], "line": example["line"],
                               "message": f"{example['id']} 與 {seen[number]} 重複；AC 編號在這個 plan 的所有 feature 中不得重複，新增的 AC 請使用輸出的 next_ac"})
            seen.setdefault(number, f"{feature['file']} 的 {example['id']}")
    return [f"AC-{n:02d}" for n in sorted(seen)]


def uncovered_ids(stories: set[str], requirements: set[str], features: list[dict]) -> list[str]:
    """spec.md 的使用者故事、FR 與 NFR 中，沒有被任何 PM 提出的 AC 涵蓋註解列出的編號；開發發現的 AC 沒有涵蓋註解，不算涵蓋。"""
    covered = {token for feature in features for example in feature["examples"] if not example["finding"] for token in example["covers"]}

    def order(item: str) -> tuple[int, int]:
        prefix = re.match(r"[A-Z]+", item).group(0)
        return ID_ORDER.get(prefix, len(ID_ORDER)), int(re.search(r"\d+", item).group(0))

    return sorted((stories | requirements) - covered, key=order)


def cited_numbers(plan_dir: Path) -> list[int]:
    """plan 資料夾中任何檔案提過的 AC 編號（truth-changes.md、涵蓋表、tasks.md，以及 .plan-trace.json、.dsl-refine.json 等紀錄）；被刪除的 AC 只要曾被記下，編號就不可重用。"""
    numbers: list[int] = []
    for path in sorted(plan_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in (".md", ".json", ".feature"):
            numbers += [int(number) for number in CITED_AC_PATTERN.findall(path.read_text(encoding="utf-8", errors="ignore"))]
    return numbers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查 plan 資料夾 features/acceptance/ 底下驗收 feature 的 AC 編號、PM 提出的 Example 數、澄清標籤（合計至多 10 個）、涵蓋的需求編號、起點句與 Background（0 或 1 個；沒有時每個 Example 第一句必須是起點句，全部相同時提示應抽成 Background），並輸出新增 AC 應使用的下一個編號與沒有被任何 AC 涵蓋的使用者故事、FR、NFR（uncovered）。")
    parser.add_argument("plan_dir", help="plan 資料夾，內含 spec.md 與 features/acceptance/，例如 specs/plans/004-ranking")
    parser.add_argument("--clarified", action="store_true",
                        help="澄清並把答案改進 feature 之後使用：不得殘留任何 [NEED CLARIFICATION]（下游的 dsl-refine 不接受殘留的澄清標籤）")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    plan_dir = Path(args.plan_dir)
    spec_path = plan_dir / "spec.md"
    acceptance = plan_dir / "features" / "acceptance"
    if not spec_path.is_file():
        print(f"錯誤：找不到 {spec_path}。請傳入含 spec.md 的 plan 資料夾，例如 specs/plans/004-ranking", file=sys.stderr)
        return 1
    feature_paths = sorted(acceptance.glob("*.feature")) if acceptance.is_dir() else []
    if not feature_paths:
        print(f"錯誤：{acceptance} 底下沒有任何 .feature。請先撰寫驗收 feature 再檢查", file=sys.stderr)
        return 1
    stories, requirements = spec_ids(spec_path.read_text(encoding="utf-8"))
    print(f"讀取 {len(feature_paths)} 份 feature；spec.md 有 {len(stories)} 個使用者故事、{len(requirements)} 條 FR 與 NFR", file=sys.stderr)
    issues: list[dict] = []
    features = [check_feature(p, p.relative_to(plan_dir).as_posix(), stories, requirements, issues) for p in feature_paths]
    ac_ids = check_ac_numbers(features, issues)
    used = [int(ac.split("-")[1]) for ac in ac_ids] + cited_numbers(plan_dir)
    next_ac = f"AC-{max(used, default=0) + 1:02d}"
    total = sum(f["clarifications"] for f in features)
    if args.clarified and total:
        issues.append({"file": "features/acceptance", "line": 0,
                       "message": f"澄清後仍有 {total} 個 [NEED CLARIFICATION]；每題答案改進步驟或表格後要刪除該題的標籤，"
                                  "還沒有答案的疑點改列回報的剩餘疑點，下游的 dsl-refine 不接受殘留的澄清標籤"})
    elif total > MAX_CLARIFY:
        issues.append({"file": "features/acceptance", "line": 0,
                       "message": f"[NEED CLARIFICATION] 全部 feature 合計至多 {MAX_CLARIFY} 個，目前 {total} 個；"
                                  f"保留影響最多旅程或最改變 Demo 結果的 {MAX_CLARIFY} 個，其餘列入回報的剩餘疑點"})
    findings = [example["id"] for feature in features for example in feature["examples"] if example["finding"]]
    uncovered = uncovered_ids(stories, requirements, features)
    print(f"沒有被任何 AC 涵蓋的使用者故事與需求 {len(uncovered)} 個", file=sys.stderr)
    print(json.dumps({"features": features, "ac_ids": ac_ids, "finding_acs": findings, "next_ac": next_ac,
                      "clarification_total": total, "uncovered": uncovered, "issues": issues}, ensure_ascii=False, indent=2))
    if issues:
        print(f"發現 {len(issues)} 個問題，請依 issues 修正後重新檢查", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
