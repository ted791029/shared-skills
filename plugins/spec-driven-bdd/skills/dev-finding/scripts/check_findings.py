# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""列出 plan 的開發發現並檢查寫法：features/acceptance/ 中標 @開發發現 的驗收案例（AC 編號、所在的 feature 與 Rule、發現的 skill、依據、Example 原文與 review 的確認狀態）與 技術項.md 的每一行（問題、發現的 skill、依據與修正的擁有者）；檢查每個標記的驗收案例都有「# 開發發現：」註解、AC 編號且自成一條 Rule，AC 編號在整個 plan 不重複，技術項的每一行都寫了「修正：<擁有者>」且是已知的擁有者，並輸出下一個可用的 AC 編號（接續現存的 AC 與 truth-changes.md 引用過的 AC 中最大的編號）。
--confirm 在 review 後把使用者保留或改寫後的 AC 連同它的內容摘要與取代的對象記進 plan 資料夾的 .dev-finding.json；之後的 review 依此判定 AC 是已確認、內容已改或未確認。"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

KEYWORD_PATTERN = re.compile(
    r"^\s*(Feature|功能|Rule|規則|Background|背景|Example|Scenario Outline|Scenario Template|Scenario|例子|場景大綱|場景|劇本大綱|劇本)\s*[:：]\s*(.*?)\s*$"
)
FEATURE_KEYWORDS = ("Feature", "功能")
RULE_KEYWORDS = ("Rule", "規則")
BACKGROUND_KEYWORDS = ("Background", "背景")
AC_ID_PATTERN = re.compile(r"^(AC-(\d+))(?!\d)")
TAG_PATTERN = re.compile(r"@[^\s@]+")
NOTE_PATTERN = re.compile(r"^#\s*開發發現\s*[：:]\s*(.*)$")
NOTE_PARTS_PATTERN = re.compile(r"^(.+?)\s*[；;]\s*(.+)$")
TECH_ITEM_PATTERN = re.compile(r"^- (.+)（([^（）；;]+)[；;](.+)[；;]\s*修正\s*[：:]\s*([^（）；;：:]*?)\s*）$")
LEGACY_ITEM_PATTERN = re.compile(r"^- (.+)（([^（）；;]+)[；;](.+)）$")
BARE_FIX_PATTERN = re.compile(r"^[；;]?\s*修正\s*[：:]\s*([^（）；;：:]*?)\s*$")
TECH_ITEM_FORMAT = "- 問題（發現的 skill；依據；修正：擁有者）"
FIX_OWNERS = (
    "clarify-over-specs", "spec-by-example", "technical-research", "system-analysis",
    "ui-ux-plan", "api-plan", "data-plan", "storage-plan", "dsl-refine", "dev-finding", "task",
)
PLANNER_NAME_PATTERN = re.compile(r"^[a-z]+-plan$")
SKILLS_DIR = Path(__file__).resolve().parents[2]
FINDING_TAG = "@開發發現"
ACCEPTANCE_PARTS = ("features", "acceptance")
TECH_ITEMS_FILE = "技術項.md"
TRUTH_CHANGES_FILE = "truth-changes.md"
CITED_AC_PATTERN = re.compile(r"(?<![A-Za-z0-9])AC-(\d+)(?!\d)")
NOTE_FORMAT = "# 開發發現：<發現的 skill>；<依據>"
RECORD_FILE = ".dev-finding.json"
CONFIRM_PATTERN = re.compile(r"^(AC-\d+)(?:\s*=\s*(.+))?$")
REPLACED_PATTERN = re.compile(r"^(?:AC|FR|NFR|SC)-\d+$")
CONFIRMED, CHANGED, UNCONFIRMED = "已確認", "內容已改", "未確認"


class Abort(Exception):
    """無法繼續執行的環境或輸入錯誤。"""


def header_start(lines: list[str], index: int) -> int:
    """回傳關鍵字行上方連續的註解與標籤行的第一行位置。"""
    start = index
    while start > 0 and lines[start - 1].strip().startswith(("#", "@")):
        start -= 1
    return start


def parse_feature(path: Path, plan_dir: Path) -> tuple[list[dict], list[dict]]:
    """回傳一份 feature 的所有 Example（含標籤、註解與原文）與寫法問題。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    file = path.relative_to(plan_dir).as_posix()
    keywords = [(index, match.group(1), match.group(2)) for index, line in enumerate(lines) if (match := KEYWORD_PATTERN.match(line))]
    starts = [header_start(lines, index) for index, _, _ in keywords]
    examples, problems = [], []
    feature = rule = None
    for position, (index, keyword, title) in enumerate(keywords):
        header = [line.strip() for line in lines[starts[position]:index]]
        tags = [tag for line in header if line.startswith("@") for tag in TAG_PATTERN.findall(line)]
        if keyword in FEATURE_KEYWORDS:
            feature = title
        elif keyword in RULE_KEYWORDS:
            rule = title
        if keyword in FEATURE_KEYWORDS or keyword in RULE_KEYWORDS or keyword in BACKGROUND_KEYWORDS:
            if FINDING_TAG in tags:
                problems.append({"kind": "標籤", "file": file, "line": index + 1, "detail": f"{FINDING_TAG} 只能放在 Example 上，不能放在 {keyword}；請移到開發發現的那個 Example 上方"})
            continue
        end = starts[position + 1] if position + 1 < len(keywords) else len(lines)
        block = lines[starts[position]:end]
        while block and not block[-1].strip():
            block.pop()
        note = next((match.group(1).strip() for line in header if (match := NOTE_PATTERN.match(line))), None)
        ac = AC_ID_PATTERN.match(title)
        examples.append({
            "file": file, "line": index + 1, "feature": feature, "rule": rule, "title": title,
            "ac": ac.group(1) if ac else None, "number": int(ac.group(2)) if ac else None,
            "tagged": FINDING_TAG in tags, "note": note, "example": "\n".join(block),
        })
    return examples, problems


def finding_digest(item: dict) -> str:
    """AC 的內容摘要：所在 Rule 的名稱與 Example 的標題、標籤、步驟與表格；註解（含「# 開發發現：」的依據）、空白與縮排不算。"""
    lines = [re.sub(r"\s+", " ", line.strip()) for line in item["example"].splitlines()]
    body = [line for line in lines if line and not line.startswith("#")]
    return hashlib.sha256("\n".join([item.get("rule") or ""] + body).encode("utf-8")).hexdigest()[:16]


def load_confirmations(plan_dir: Path) -> tuple[dict, str | None]:
    """讀取 .dev-finding.json 的確認紀錄（AC → 摘要、取代的對象與確認時間）；不存在時為空，格式不符時回傳警告並視為空。"""
    path = plan_dir / RECORD_FILE
    if not path.is_file():
        return {}, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        confirmed = data["confirmed"]
        if not isinstance(confirmed, dict):
            raise TypeError("confirmed 不是物件")
        return confirmed, None
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        return {}, f"{RECORD_FILE} 格式不符（{error}），全部的開發發現都視為未確認；review 後以 --confirm 重新記錄。"


def confirmation_state(finding: dict, confirmed: dict) -> dict:
    record = confirmed.get(finding["ac"] or "")
    if not isinstance(record, dict):
        return {"status": UNCONFIRMED, "replaces": [], "confirmed_at": None}
    status = CONFIRMED if record.get("digest") == finding["digest"] else CHANGED
    return {"status": status, "replaces": list(record.get("replaces") or []), "confirmed_at": record.get("confirmed_at")}


def parse_confirm(values: list[str]) -> tuple[dict[str, list[str]], list[str]]:
    """--confirm 的值：AC-08，或 AC-08=AC-02,FR-005（保留並取代的對象）。回傳（AC → 取代的對象、寫法錯誤）。"""
    wanted: dict[str, list[str]] = {}
    errors = []
    for value in values:
        matched = CONFIRM_PATTERN.match(value.strip())
        if not matched:
            errors.append(f"--confirm {value} 的寫法不符，請寫成 AC-08，或 AC-08=AC-02,FR-005（等號後是保留並取代的 AC、FR、NFR 或 SC 編號）")
            continue
        replaced = [item.strip() for item in re.split(r"[,、]", matched.group(2) or "") if item.strip()]
        wrong = [item for item in replaced if not REPLACED_PATTERN.match(item)]
        if wrong:
            errors.append(f"--confirm {value} 的取代對象 {'、'.join(wrong)} 不是 AC、FR、NFR 或 SC 編號，請改寫，例如 AC-08=AC-02,FR-005")
            continue
        wanted[matched.group(1)] = replaced
    return wanted, errors


def write_confirmations(plan_dir: Path, findings: list[dict], confirmed: dict, wanted: dict[str, list[str]]) -> dict:
    """記下這次確認的 AC，保留其他仍存在的 AC 的紀錄，移除已不存在的 AC 的紀錄。"""
    current = {finding["ac"]: finding for finding in findings if finding["ac"]}
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    kept = {ac: record for ac, record in confirmed.items() if ac in current and ac not in wanted}
    removed = sorted(ac for ac in confirmed if ac not in current)
    for ac, replaced in wanted.items():
        kept[ac] = {"digest": current[ac]["digest"], "replaces": replaced, "confirmed_at": now}
    path = plan_dir / RECORD_FILE
    ordered = dict(sorted(kept.items(), key=lambda pair: int(pair[0].split("-")[1])))
    path.write_text(json.dumps({"confirmed": ordered}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return {"record": path.as_posix(), "confirmed": sorted(wanted, key=lambda ac: int(ac.split("-")[1])), "removed": removed}


def check_examples(examples: list[dict]) -> tuple[list[dict], list[dict]]:
    findings, problems = [], []
    seen: dict[str, dict] = {}
    for item in examples:
        where = {"file": item["file"], "line": item["line"]}
        if item["ac"]:
            if item["ac"] in seen:
                first = seen[item["ac"]]
                problems.append({"kind": "編號", **where, "detail": f"{item['ac']} 已用於 {first['file']} 第 {first['line']} 行；AC 編號在整個 plan 不可重複，請改用下一個可用的編號"})
            seen.setdefault(item["ac"], item)
        if not item["tagged"]:
            if item["note"] is not None:
                problems.append({"kind": "標籤", **where, "detail": f"這個 Example 有「# 開發發現：」註解卻沒有 {FINDING_TAG} 標籤；請在註解下一行加上標籤"})
            continue
        finder = basis = ""
        if item["note"] is None:
            problems.append({"kind": "註解", **where, "detail": f"標 {FINDING_TAG} 的 Example 上方缺少註解；請在標籤上一行加上「{NOTE_FORMAT}」"})
        else:
            parts = NOTE_PARTS_PATTERN.match(item["note"])
            if not parts:
                problems.append({"kind": "註解", **where, "detail": f"註解必須是「{NOTE_FORMAT}」，以「；」分開發現的 skill 與依據，目前是「# 開發發現：{item['note']}」"})
            else:
                finder, basis = parts.group(1).strip(), parts.group(2).strip()
        if not item["ac"]:
            problems.append({"kind": "編號", **where, "detail": "標題必須以 AC 編號開頭，例如「Example: AC-08 …」；請用下一個可用的編號"})
        if item["rule"] is None:
            problems.append({"kind": "位置", **where, "detail": "開發發現的 Example 必須放在自己的 Rule 之下；請在 feature 最後新增一條 Rule"})
        findings.append({
            "ac": item["ac"], "title": item["title"], "file": item["file"], "feature": item["feature"], "rule": item["rule"],
            "finder": finder, "basis": basis, "example": item["example"], "digest": finding_digest(item),
        })
    for item in examples:
        if not item["tagged"] or item["rule"] is None:
            continue
        mixed = [other for other in examples if other["file"] == item["file"] and other["rule"] == item["rule"] and not other["tagged"]]
        if mixed:
            problems.append({"kind": "位置", "file": item["file"], "line": item["line"], "detail": f"Rule「{item['rule']}」同時有 PM 提出的 Example 與開發發現的 Example；開發發現必須自成一條 Rule"})
    return findings, problems


def known_owner(name: str) -> bool:
    """修正的擁有者是相依表的擁有者，或已建立的其他端點 Planner（<介面 ID 前綴小寫>-plan）。"""
    if name in FIX_OWNERS:
        return True
    return bool(PLANNER_NAME_PATTERN.match(name)) and (SKILLS_DIR / name / "SKILL.md").is_file()


def parse_tech_items(path: Path) -> tuple[list[dict], list[dict]]:
    """回傳 技術項.md 的每一行（含修正的擁有者）與寫法問題；缺少擁有者的行仍列出，fix_owner 為 null。"""
    if not path.is_file():
        return [], []
    items, problems = [], []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        text = line.strip()
        if not text.startswith("- "):
            continue
        where = {"kind": "技術項", "file": path.name, "line": line_no}
        match = TECH_ITEM_PATTERN.match(text)
        if match:
            problem, finder, basis, fix_owner = (part.strip() for part in match.groups())
        elif legacy := LEGACY_ITEM_PATTERN.match(text):
            problem, finder, basis = (part.strip() for part in legacy.groups())
            fix_owner = ""
            if bare := BARE_FIX_PATTERN.match(basis):
                problems.append({**where, "detail": f"缺少依據；每一行必須是「{TECH_ITEM_FORMAT}」，請在發現的 skill 與「修正：」之間補上現象在哪裡被觀察到、規格哪裡沒有寫"})
                basis, fix_owner = "", bare.group(1).strip()
        else:
            problems.append({**where, "detail": f"每一行必須是「{TECH_ITEM_FORMAT}」，括號為全形，以「；」分開；請補上發現的 skill、依據與修正的擁有者"})
            continue
        if not fix_owner:
            problems.append({**where, "detail": f"缺少修正的擁有者；請在依據後面補上「；修正：<出錯那份資料的擁有者>」，寫法為「{TECH_ITEM_FORMAT}」"})
        elif not known_owner(fix_owner):
            problems.append({**where, "detail": f"「修正：{fix_owner}」不是已知的擁有者；一行只寫一個擁有者，請改為 {'、'.join(FIX_OWNERS)} 之一，或已建立的其他端點 Planner（<介面 ID 前綴小寫>-plan）"})
        items.append({"problem": problem, "finder": finder, "basis": basis, "fix_owner": fix_owner or None, "line": line_no})
    return items, problems


def cited_numbers(plan_dir: Path) -> list[int]:
    """回傳 plan 資料夾中任何檔案提過的 AC 編號（truth-changes.md、涵蓋表、tasks.md，以及 .plan-trace.json、.dsl-refine.json 等紀錄）；被刪除的 AC 只要曾被記下，編號就不可重用。"""
    numbers: list[int] = []
    for path in sorted(plan_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in (".md", ".json", ".feature"):
            numbers += [int(number) for number in CITED_AC_PATTERN.findall(path.read_text(encoding="utf-8", errors="ignore"))]
    return numbers


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="列出 plan 中標 @開發發現 的驗收案例（含 review 的確認狀態）與技術項（含修正的擁有者），並檢查它們的寫法；--confirm 記下 review 中使用者保留或改寫後的 AC。")
    parser.add_argument("plan_dir", help="plan 資料夾，例如 specs/plans/004-ranking")
    parser.add_argument("--confirm", action="append", default=[], metavar="AC-xx[=取代的編號,…]",
                        help=f"review 後使用：把使用者保留或改寫後的 AC 連同目前的內容摘要記進 {RECORD_FILE}；保留並取代時在等號後寫被取代的 AC、FR、NFR 或 SC 編號，例如 AC-08=AC-02,FR-005；可重複。寫法有問題時不寫入")
    return parser.parse_args()


def run(plan_dir: Path, confirm: list[str]) -> int:
    if not plan_dir.is_dir():
        raise Abort(f"找不到資料夾 {plan_dir}。請傳入 plan 資料夾，例如 specs/plans/004-ranking")
    acceptance = plan_dir.joinpath(*ACCEPTANCE_PARTS)
    examples, problems = [], []
    if acceptance.is_dir():
        for path in sorted(acceptance.glob("*.feature")):
            parsed, issues = parse_feature(path, plan_dir)
            examples += parsed
            problems += issues
    findings, issues = check_examples(examples)
    problems += issues
    tech_items, issues = parse_tech_items(plan_dir / TECH_ITEMS_FILE)
    problems += issues
    confirmed, warning = load_confirmations(plan_dir)
    if warning:
        print(f"警告：{warning}", file=sys.stderr)
    if confirm:
        wanted, errors = parse_confirm(confirm)
        known = {finding["ac"] for finding in findings if finding["ac"]}
        errors += [f"--confirm 的 {ac} 不是這個 plan 標 {FINDING_TAG} 的 AC（現有：{'、'.join(sorted(known)) or '無'}），請確認編號" for ac in wanted if ac not in known]
        if problems or errors:
            print(json.dumps({"problems": problems, "errors": errors}, ensure_ascii=False, indent=2))
            print(f"錯誤：還有 {len(problems)} 個寫法問題、{len(errors)} 個 --confirm 錯誤，沒有寫入 {RECORD_FILE}；請先修正後再以 --confirm 記錄。", file=sys.stderr)
            return 1
        written = write_confirmations(plan_dir, findings, confirmed, wanted)
        print(f"已在 {RECORD_FILE} 記下 {len(written['confirmed'])} 個 AC 的確認", file=sys.stderr)
        print(json.dumps(written, ensure_ascii=False, indent=2))
        return 0
    for finding in findings:
        finding["confirmation"] = confirmation_state(finding, confirmed)
    numbers = [item["number"] for item in examples if item["number"] is not None] + cited_numbers(plan_dir)
    counts = {status: sum(1 for finding in findings if finding["confirmation"]["status"] == status) for status in (CONFIRMED, CHANGED, UNCONFIRMED)}
    result = {
        "plan": plan_dir.name, "findings": findings, "confirmation_counts": counts, "tech_items": tech_items,
        "next_ac": f"AC-{max(numbers, default=0) + 1:02d}", "problems": problems, "ok": not problems,
    }
    print(f"開發發現 {len(findings)} 個（已確認 {counts[CONFIRMED]}、內容已改 {counts[CHANGED]}、未確認 {counts[UNCONFIRMED]}），技術項 {len(tech_items)} 個，問題 {len(problems)} 個", file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not problems else 1


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        return run(Path(args.plan_dir).resolve(), args.confirm)
    except Abort as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
