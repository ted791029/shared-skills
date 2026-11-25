# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""檢查 plan 的 spec.md：表頭的 Plan 與資料夾是否一致、是否位於已開立的 plan 資料夾、「受影響的既有功能」的格式與名稱、FR／NFR／SC／使用者故事編號是否重複、交叉引用是否存在、是否殘留樣板佔位符，並輸出各項條數與新增項目可用的下一個編號。
編號是需求的身分：新增或刪除後不重新編號，所以允許空號、也不要求依出現順序；下一個編號算入 spec.md（含釐清紀錄）與 plan 中其他檔案提過的編號，刪除後仍被提到的編號不會被重用。
釐清紀錄是過程紀錄，歷史場次提到已刪除的編號不算引用錯誤，交叉引用只檢查釐清紀錄以外的章節。"""

import argparse
import json
import re
import sys
from pathlib import Path

ID_PREFIXES = ("FR", "NFR", "SC")
SECTION_AFFECTED = "受影響的既有功能"
SECTION_RECORD = "釐清紀錄"
NONE_TEXT = "無"
PLAN_FILE = ".plan.json"
GLOSSARY_PARTS = ("truth", "features", "用語表.md")
GLOSSARY_SECTION = "模組"

DEFINITION_PATTERN = re.compile(r"^- \*\*(FR|NFR|SC)-(\d{3})\*\*")
REFERENCE_PATTERN = re.compile(r"(?<![A-Z])(FR|NFR|SC)-(\d{3})")
STORY_PATTERN = re.compile(r"^### 使用者故事 (\d+) - ")
STORY_REFERENCE_PATTERNS = (re.compile(r"(?<![A-Za-z])US(\d+)(?!\d)"), re.compile(r"使用者故事\s*(\d+)"))
OTHER_PLAN_REFERENCE = re.compile(r"(?<!\d)\d{3}(?:/|\s*(?:的\s*)?(?:規格\s*)?(?:的\s*)?)(?:(?:FR|NFR|SC)-\d+|US\d+|使用者故事\s*\d+)")
TEXT_SUFFIXES = {".md", ".feature", ".yaml", ".yml", ".json", ".txt", ".html"}
LEFTOVER_PATTERN = re.compile(r"\{\{[^}]*\}\}|<!-- 重複(開始|結束)")
SECTION_PATTERN = re.compile(r"^## (.+?)\s*$")
PLAN_HEADER_PATTERN = re.compile(r"^\*\*Plan\*\*：\s*`?([^`]*?)`?\s*$")
AFFECTED_ITEM_PATTERN = re.compile(r"^- (.+?)：(.+)$")
TECHNICAL_PATTERN = re.compile(r"`|[A-Za-z0-9_\-]+/[A-Za-z0-9_\-{}.]+")


def problem(kind: str, line: int, message: str) -> dict:
    return {"type": kind, "line": line, "message": message}


def check_unique(names: list[tuple[int, str]]) -> list[dict]:
    """編號是需求的身分，不得重複；空號與不依出現順序都不算問題。"""
    problems, seen = [], {}
    for line_no, name in names:
        if name in seen:
            problems.append(problem("numbering", line_no, f"{name} 與第 {seen[name]} 行重複；編號是需求的身分，不得重複，新增的項目請使用輸出的 next_ids。"))
        seen.setdefault(name, line_no)
    return problems


def cited_numbers(spec_path: Path) -> dict[str, set[int]]:
    """plan 中 spec.md 以外的檔案引用過的編號；被刪除的項目若仍被引用，它的編號不可重用。"""
    cited = {prefix: set() for prefix in ID_PREFIXES} | {"使用者故事": set()}
    for path in sorted(spec_path.parent.rglob("*")):
        if not path.is_file() or path == spec_path or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for prefix, number in REFERENCE_PATTERN.findall(text):
            cited[prefix].add(int(number))
        for pattern in STORY_REFERENCE_PATTERNS:
            cited["使用者故事"].update(int(number) for number in pattern.findall(text))
    return cited


def next_ids(definitions: dict[str, list[tuple[int, int]]], stories: list[tuple[int, int]], spec_path: Path, record_text: str) -> dict:
    """每一類的下一個編號：spec.md 的定義、釐清紀錄中提過（後來可能被刪除）的本 plan 編號，與 plan 中其他檔案用過的最大編號加一。"""
    cited = cited_numbers(spec_path)
    own_record = OTHER_PLAN_REFERENCE.sub("", record_text)
    for prefix, number in REFERENCE_PATTERN.findall(own_record):
        cited[prefix].add(int(number))
    for pattern in STORY_REFERENCE_PATTERNS:
        cited["使用者故事"].update(int(number) for number in pattern.findall(own_record))
    result = {}
    for prefix in ID_PREFIXES:
        used = {number for _, number in definitions[prefix]} | cited[prefix]
        result[prefix] = f"{prefix}-{max(used, default=0) + 1:03d}"
    used = {number for _, number in stories} | cited["使用者故事"]
    result["使用者故事"] = max(used, default=0) + 1
    return result


def find_sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """回傳每個二級標題的內文範圍（不含標題行），鍵為去掉「*（必填）*」後的標題。"""
    starts = []
    for index, line in enumerate(lines):
        match = SECTION_PATTERN.match(line)
        if match:
            starts.append((re.sub(r"\s*\*（.*?）\*$", "", match.group(1)).strip(), index))
    sections = {}
    for position, (title, index) in enumerate(starts):
        end = starts[position + 1][1] if position + 1 < len(starts) else len(lines)
        sections.setdefault(title, (index + 1, end))
    return sections


def load_functions(spec_path: Path) -> list[str] | None:
    """讀取 truth 用語表「模組」表的第一欄；找不到用語表或模組表時回傳 None。"""
    glossary = spec_path.parent.parent.parent.joinpath(*GLOSSARY_PARTS)
    if not glossary.is_file():
        return None
    lines = glossary.read_text(encoding="utf-8").splitlines()
    sections = find_sections(lines)
    if GLOSSARY_SECTION not in sections:
        return None
    start, end = sections[GLOSSARY_SECTION]
    rows = []
    for line in lines[start:end]:
        text = line.strip()
        if text.startswith("|") and not re.fullmatch(r"\|[\s:\-|]+\|?", text):
            rows.append(text.strip("|").split("|")[0].strip())
    return [name for name in rows[1:] if name]


def check_header(lines: list[str], spec_path: Path) -> tuple[list[dict], str]:
    plan_dir = spec_path.parent
    problems = []
    header = next(((line_no, match.group(1).strip()) for line_no, line in enumerate(lines, start=1) if (match := PLAN_HEADER_PATTERN.match(line))), None)
    if header is None or not header[1]:
        problems.append(problem("header", 1, f"表頭缺少「**Plan**：`{plan_dir.name}`」，請依樣板補上 plan 資料夾的名稱。"))
    elif header[1] != plan_dir.name:
        problems.append(problem("header", header[0], f"表頭的 Plan 是 {header[1]}，但 spec.md 位於 {plan_dir.name}；請改為資料夾的名稱。"))
    if not (plan_dir / PLAN_FILE).is_file():
        problems.append(problem("plan", 1, f"{plan_dir.name} 沒有 {PLAN_FILE}；spec.md 必須寫在 plan-package 的 open 開立的 plan 資料夾，不得自行建立資料夾。"))
    return problems, plan_dir.name


def check_affected(lines: list[str], spec_path: Path) -> tuple[list[dict], int]:
    sections = find_sections(lines)
    if SECTION_AFFECTED not in sections:
        return [problem("section", 1, f"缺少「## {SECTION_AFFECTED}」一節；沒有受影響的既有功能時，這一節只寫「{NONE_TEXT}」。")], 0
    start, end = sections[SECTION_AFFECTED]
    content = [(index + 1, lines[index].strip()) for index in range(start, end) if lines[index].strip() and not LEFTOVER_PATTERN.search(lines[index])]
    if not content:
        return [problem("affected", start, f"「{SECTION_AFFECTED}」是空的；沒有受影響的既有功能時寫「{NONE_TEXT}」。")], 0
    if len(content) == 1 and content[0][1] == NONE_TEXT:
        return [], 0
    problems = []
    functions = load_functions(spec_path)
    seen: dict[str, int] = {}
    for line_no, text in content:
        match = AFFECTED_ITEM_PATTERN.match(text)
        if not match:
            problems.append(problem("affected", line_no, f"這一行不是「- 既有功能名稱：一句影響」的格式；每個受影響的既有功能一行，沒有時整節只寫「{NONE_TEXT}」。"))
            continue
        name = match.group(1).strip()
        if name in seen:
            problems.append(problem("affected", line_no, f"既有功能「{name}」已在第 {seen[name]} 行列過；同一個功能的影響請合併成一行。"))
        seen.setdefault(name, line_no)
        if functions is None:
            problems.append(problem("affected", line_no, f"找不到既有功能清單（specs/truth/features/用語表.md 的「{GLOSSARY_SECTION}」表），無法確認「{name}」是既有功能；系統還沒有既有功能時，這一節只寫「{NONE_TEXT}」。"))
        elif name not in functions:
            problems.append(problem("affected", line_no, f"「{name}」不在既有功能清單中（{'、'.join(functions)}）；請改用清單中的名稱，這次新增的功能不列在這一節。"))
        if TECHNICAL_PATTERN.search(match.group(2)):
            problems.append(problem("affected", line_no, "影響只寫使用者看得到的結果，不得出現檔名、路徑、API、資料表或程式碼；要改哪些檔案由下游各自盤點。"))
    return problems, len(seen)


def check_spec(lines: list[str], spec_path: Path) -> tuple[list[dict], dict]:
    problems, plan_name = check_header(lines, spec_path)
    definitions = {prefix: [] for prefix in ID_PREFIXES}
    stories = []
    for line_no, line in enumerate(lines, start=1):
        definition = DEFINITION_PATTERN.match(line)
        if definition:
            definitions[definition.group(1)].append((line_no, int(definition.group(2))))
        story = STORY_PATTERN.match(line)
        if story:
            stories.append((line_no, int(story.group(1))))
        leftover = LEFTOVER_PATTERN.search(line)
        if leftover:
            problems.append(problem("leftover", line_no, f"殘留樣板內容 {leftover.group(0)}，請填入實際內容或刪除該行。"))
    for prefix in ID_PREFIXES:
        problems += check_unique([(line_no, f"{prefix}-{number:03d}") for line_no, number in definitions[prefix]])
    problems += check_unique([(line_no, f"使用者故事 {number}") for line_no, number in stories])
    defined = {f"{prefix}-{number:03d}" for prefix in ID_PREFIXES for _, number in definitions[prefix]}
    record_start, record_end = find_sections(lines).get(SECTION_RECORD, (0, 0))
    for line_no, line in enumerate(lines, start=1):
        if record_start <= line_no - 1 < record_end:
            continue
        definition = DEFINITION_PATTERN.match(line)
        body = OTHER_PLAN_REFERENCE.sub("", line[definition.end():] if definition else line)
        for prefix, number in REFERENCE_PATTERN.findall(body):
            if f"{prefix}-{number}" not in defined:
                problems.append(problem("reference", line_no, f"引用的 {prefix}-{number} 不存在，請改為已定義的編號或補上該條需求。"))
    affected_problems, affected_count = check_affected(lines, spec_path)
    problems += affected_problems
    summary = {
        "plan": plan_name,
        "stories": len(stories),
        "fr": len(definitions["FR"]),
        "nfr": len(definitions["NFR"]),
        "sc": len(definitions["SC"]),
        "affected_functions": affected_count,
        "next_ids": next_ids(definitions, stories, spec_path, "\n".join(lines[record_start:record_end])),
    }
    return sorted(problems, key=lambda item: item["line"]), summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查 plan 的 spec.md：表頭、受影響的既有功能、編號不重複、交叉引用與殘留佔位符，並輸出各項條數與新增項目可用的下一個編號（summary.next_ids）。")
    parser.add_argument("spec_path", help="要檢查的 spec.md 路徑，例如 specs/plans/<plan 資料夾>/spec.md")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    spec_path = Path(args.spec_path).resolve()
    if not spec_path.is_file():
        print(
            f"錯誤：找不到檔案 {spec_path}。請傳入 spec.md 的路徑，"
            "例如 specs/plans/<plan 資料夾>/spec.md",
            file=sys.stderr,
        )
        return 1
    problems, summary = check_spec(spec_path.read_text(encoding="utf-8").splitlines(), spec_path)
    print(f"發現 {len(problems)} 個問題", file=sys.stderr)
    print(json.dumps({"ok": not problems, "summary": summary, "problems": problems}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
