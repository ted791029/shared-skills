# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""解析 plan 的 truth-changes.md 並與 git 的實際差異比對：query 輸出各 truth owner 已記錄的列與基準以來實際異動的 truth 檔案（可只看一個 owner、只列原因含某個開發發現 AC 的列，或改列異動的 feature 中新增、修改、刪除的 Rule）；check 核對表格與實際異動是否一致，列出改了沒記、記了沒改、異動類型不符、沒有 owner 與格式問題。"""

import argparse
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

SECTION_PATTERN = re.compile(r"^##\s+(.+?)\s*[（(]\s*(.+?)\s*[）)]\s*$")
CELL_SPLIT_PATTERN = re.compile(r"(?<!\\)\|")
SEPARATOR_PATTERN = re.compile(r"^:?-{3,}:?$")
CODE_SPAN_PATTERN = re.compile(r"`([^`]+)`")
ID_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:FR|NFR|AC)-\d+(?!\d)")
ID_REASON_PATTERN = re.compile(r"^(?:FR|NFR|AC)-\d+(?:\s*[、,，]\s*(?:FR|NFR|AC)-\d+)*$")
REQUIREMENT_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:FR|NFR)-\d+(?!\d)")
TECH_REASON_PATTERN = re.compile(r"^技術[：:]\s*\S")
AC_PATTERN = re.compile(r"^AC-\d+$")
EXAMPLE_AC_PATTERN = re.compile(
    r"^\s*(?:Example|Scenario Outline|Scenario Template|Scenario|例子|場景大綱|場景|劇本大綱|劇本)\s*[:：]\s*(AC-\d+)(?!\d)"
)
FINDING_TAG = "@開發發現"
RULE_PATTERN = re.compile(r"^\s*(?:Rule|規則)\s*[:：]\s*(.+?)\s*$")
FEATURE_PATTERN = re.compile(r"^\s*(?:Feature|功能)\s*[:：]\s*(.+?)\s*$")
HEADER = ["異動", "對象", "改動摘要", "原因"]
MARKED_TARGET_PATTERN = re.compile(r"(?:dsl\.md|用語表\.md)`\s*＞|\.feature`\s*＞\s*Background")
CHANGE_MARKS = ("只改說明：", "改測試寫法：")
TYPES = ("ADD", "MOD", "DEL")
NO_CHANGE = "無異動"
GIT_STATUS = {"A": "ADD", "D": "DEL"}
STATUS_TEXT = {"ADD": "新增", "DEL": "刪除"}
IN_PROGRESS = "進行中"


class Abort(Exception):
    """無法繼續執行的環境或輸入錯誤。"""


def git(root: Path, *args: str) -> str:
    try:
        result = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=root, capture_output=True)
    except FileNotFoundError:
        raise Abort("找不到 git 指令。truth 的異動以 git 的差異為準，請先安裝 git。")
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise Abort(f"git {' '.join(args[:2])} 執行失敗：{detail}")
    return result.stdout.decode("utf-8", errors="replace")


def normalize_path(token: str, truth_rel: str) -> str:
    path = token.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if path.startswith(truth_rel + "/"):
        path = path[len(truth_rel) + 1:]
    return path


def covers(token: str, file: str) -> bool:
    return file.startswith(token) if token.endswith("/") else file == token


def under_paths(path: str, owner_paths: list[str]) -> bool:
    return any(path == owner or (owner.endswith("/") and path.startswith(owner)) for owner in owner_paths)


def owner_path(raw: str, truth_dir: Path, truth_rel: str) -> str:
    path = normalize_path(raw.strip("` "), truth_rel)
    if path.endswith("/"):
        return path
    is_dir = (truth_dir / path).is_dir() or "." not in path.rsplit("/", 1)[-1]
    return path + "/" if is_dir else path


def split_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return [cell.strip() for cell in CELL_SPLIT_PATTERN.split(text)]


def parse_sections(text: str, truth_dir: Path, truth_rel: str) -> tuple[list[dict], list[str]]:
    """每個「## owner（路徑）」一節，節內第一張表格的每一列為一筆紀錄。"""
    sections: list[dict] = []
    issues: list[str] = []
    current = None
    table = "before"
    for number, line in enumerate(text.splitlines(), 1):
        if line.startswith("## "):
            match = SECTION_PATTERN.match(line)
            if not match:
                issues.append(f"第 {number} 行的標題「{line[3:].strip()}」不是「owner（路徑）」的格式，例如「api-plan（contracts/）」")
                current = None
                continue
            paths = [owner_path(part, truth_dir, truth_rel) for part in re.split(r"[、,，]", match.group(2)) if part.strip()]
            current = {"owner": match.group(1).strip("` "), "paths": paths, "rows": [], "issues": []}
            if any(section["owner"] == current["owner"] for section in sections):
                issues.append(f"第 {number} 行的 owner「{current['owner']}」重複出現，同一個 owner 只能有一節")
            sections.append(current)
            table = "before"
            continue
        if current is None:
            continue
        if not line.lstrip().startswith("|"):
            if table == "in":
                table = "after"
            continue
        if table == "after":
            current["issues"].append(f"第 {number} 行：一個 owner 只能有一張表格，其他內容請移到 plan 的其他檔案")
            table = "extra"
            continue
        if table == "extra":
            continue
        cells = split_row(line)
        if table == "before":
            table = "in"
            if cells != HEADER:
                current["issues"].append(f"第 {number} 行：表頭必須是「{'｜'.join(HEADER)}」，目前是「{'｜'.join(cells)}」")
            continue
        if all(SEPARATOR_PATTERN.match(cell) for cell in cells):
            continue
        if len(cells) != len(HEADER):
            current["issues"].append(f"第 {number} 行：每一列必須有 {len(HEADER)} 欄，目前是 {len(cells)} 欄")
            continue
        tokens = [normalize_path(token, truth_rel) for token in CODE_SPAN_PATTERN.findall(cells[1])]
        current["rows"].append({
            "line": number,
            "type": cells[0],
            "target": cells[1],
            "summary": cells[2],
            "reason": cells[3],
            "files": [token for token in tokens if under_paths(token, paths)],
        })
    return sections, issues


def load_ignore(truth_dir: Path) -> list[str]:
    ignore_file = truth_dir / ".truthignore"
    if not ignore_file.is_file():
        return []
    lines = ignore_file.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def is_ignored(path: str, patterns: list[str]) -> bool:
    parts = path.split("/")
    if any(part.startswith(".") for part in parts):
        return True
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(parts[-1], pattern) for pattern in patterns)


def changed_files(root: Path, base: str, truth_rel: str, patterns: list[str]) -> dict[str, str]:
    """基準 commit 到目前工作區之間，truth 底下異動的檔案（含尚未加入 git 的新檔）。"""
    changes: dict[str, str] = {}
    parts = git(root, "diff", "--name-status", "--no-renames", "-z", base, "--", truth_rel).split("\0")
    for index in range(0, len(parts) - 1, 2):
        changes[parts[index + 1]] = GIT_STATUS.get(parts[index][:1], "MOD")
    for path in git(root, "ls-files", "--others", "--exclude-standard", "-z", "--", truth_rel).split("\0"):
        if path:
            changes.setdefault(path, "ADD")
    result = {}
    for path in sorted(changes):
        relative = path[len(truth_rel) + 1:]
        if not is_ignored(relative, patterns):
            result[relative] = changes[path]
    return result


def finding_acs(plan_dir: Path) -> set[str]:
    """回傳 plan 的 features/acceptance/ 中標 @開發發現 的驗收案例的 AC 編號。"""
    found: set[str] = set()
    acceptance = plan_dir / "features" / "acceptance"
    if not acceptance.is_dir():
        return found
    for path in sorted(acceptance.glob("*.feature")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            match = EXAMPLE_AC_PATTERN.match(line)
            above = index
            while match and above > 0 and lines[above - 1].strip().startswith(("#", "@")):
                above -= 1
                if FINDING_TAG in lines[above].split():
                    found.add(match.group(1))
    return found


def load_context(plan_arg: str) -> dict:
    plan_dir = Path(plan_arg)
    if not plan_dir.is_dir():
        raise Abort(f"找不到 plan 資料夾 {plan_dir}。請傳入 plan 的路徑，例如 specs/plans/004-ranking")
    plan_dir = plan_dir.resolve()
    plan_file = plan_dir / ".plan.json"
    if not plan_file.is_file():
        raise Abort(f"{plan_dir.name} 沒有 .plan.json，無法得知基準 commit。plan 必須由 plan-package 的 open 開立。")
    try:
        plan = json.loads(plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise Abort(f"{plan_file.name} 不是合法的 JSON（{error}）。請以 plan-package 重新產生。")
    record = plan_dir / "truth-changes.md"
    if not record.is_file():
        raise Abort(f"{plan_dir.name} 沒有 truth-changes.md。請依 truth-changes 的樣板建立每個 truth owner 一節的空表格。")
    truth_dir = plan_dir.parent.parent / "truth"
    if not truth_dir.is_dir():
        raise Abort(f"找不到 truth 資料夾 {truth_dir}。plan 必須位於 <specs>/plans/ 底下，且 <specs>/truth/ 存在。")
    root = Path(git(plan_dir, "rev-parse", "--show-toplevel").strip())
    prefix = git(plan_dir, "rev-parse", "--show-prefix").strip().strip("/")
    truth_rel = "/".join(prefix.split("/")[:-2] + ["truth"])
    sections, issues = parse_sections(record.read_text(encoding="utf-8"), truth_dir, truth_rel)
    base = str(plan.get("base") or "")
    status = str(plan.get("status") or "")
    changes = None
    if status == IN_PROGRESS:
        if not base:
            raise Abort(f"{plan_dir.name} 的 .plan.json 沒有基準 commit（base）。請以 plan-package 重新開立 plan。")
        git(root, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
        changes = changed_files(root, base, truth_rel, load_ignore(truth_dir))
        print(f"基準 {base[:7]}，truth 底下實際異動 {len(changes)} 個檔案", file=sys.stderr)
    else:
        print(f"{plan_dir.name} 的狀態是「{status or '未知'}」，只輸出已記錄的列，不比對 git 差異", file=sys.stderr)
    spec = plan_dir / "spec.md"
    known_ids = None
    if spec.is_file():
        known_ids = set(REQUIREMENT_PATTERN.findall(spec.read_text(encoding="utf-8"))) | finding_acs(plan_dir)
    return {
        "plan": plan_dir.name, "status": status, "base": base, "root": root, "truth_dir": truth_dir,
        "truth_rel": truth_rel, "sections": sections, "issues": issues, "changes": changes, "known_ids": known_ids,
    }


def select_sections(context: dict, owner: str | None) -> list[dict]:
    if owner is None:
        return context["sections"]
    selected = [section for section in context["sections"] if section["owner"] == owner]
    if not selected:
        names = "、".join(section["owner"] for section in context["sections"]) or "（沒有任何一節）"
        raise Abort(
            f"truth-changes.md 沒有 owner「{owner}」這一節，目前有：{names}。"
            f"請加上「## {owner}（它寫入的 truth 路徑）」一節與空表格後再執行。"
        )
    return selected


def public_row(row: dict) -> dict:
    return {key: row[key] for key in ("type", "target", "summary", "reason", "files")}


def owner_changes(section: dict, changes: dict[str, str]) -> dict[str, str]:
    return {file: status for file, status in changes.items() if under_paths(file, section["paths"])}


def unowned_changes(context: dict) -> list[dict]:
    all_paths = [path for section in context["sections"] for path in section["paths"]]
    return [
        {"status": status, "file": file}
        for file, status in (context["changes"] or {}).items() if not under_paths(file, all_paths)
    ]


def check_section(section: dict, changes: dict[str, str], known_ids: set[str] | None, require_rows: bool) -> list[dict]:
    problems = [{"kind": "格式", "detail": issue} for issue in section["issues"]]
    rows = section["rows"]
    change_rows = [row for row in rows if row["type"] in TYPES]
    no_change_rows = [row for row in rows if row["type"] == NO_CHANGE]
    for row in rows:
        where = f"第 {row['line']} 行"
        if row["type"] not in TYPES and row["type"] != NO_CHANGE:
            problems.append({"kind": "格式", "detail": f"{where}：異動欄只能是 ADD、MOD、DEL 或「{NO_CHANGE}」，目前是「{row['type']}」"})
            continue
        reason = row["reason"]
        if not reason or reason in ("—", "-"):
            problems.append({"kind": "格式", "detail": f"{where}：原因欄不可空白"})
        elif row["type"] != NO_CHANGE:
            if ID_REASON_PATTERN.match(reason):
                missing = [item for item in ID_PATTERN.findall(reason) if known_ids is not None and item not in known_ids]
                if missing:
                    problems.append({"kind": "格式", "detail": f"{where}：原因 {'、'.join(missing)} 不存在；FR、NFR 必須是 spec.md 中的編號，AC 必須是這個 plan 的 acceptance 中標 {FINDING_TAG} 的驗收案例"})
            elif not TECH_REASON_PATTERN.match(reason):
                problems.append({"kind": "格式", "detail": f"{where}：原因只能是 FR、NFR 編號、開發發現的 AC 編號（以「、」分隔）或「技術：…」，目前是「{reason}」"})
        if row["type"] in TYPES and not row["files"]:
            paths = "、".join(section["paths"])
            problems.append({"kind": "格式", "detail": f"{where}：對象欄沒有以反引號標出 {paths} 底下的檔案或目錄（路徑相對於 truth 資料夾）"})
        if row["type"] == "MOD" and MARKED_TARGET_PATTERN.search(row["target"]) and not row["summary"].startswith(CHANGE_MARKS):
            problems.append({"kind": "格式", "detail": f"{where}：修改既有句型、參數對照、用語表的節或 Background 時，改動摘要必須以「{CHANGE_MARKS[0]}」或「{CHANGE_MARKS[1]}」開頭，task 依它決定排 [重跑] 或紅燈"})
    if no_change_rows and (change_rows or len(no_change_rows) > 1):
        problems.append({"kind": "格式", "detail": f"「{NO_CHANGE}」只能單獨一列，不可與其他列並存"})
    if not rows and require_rows:
        problems.append({"kind": "格式", "detail": f"表格沒有任何列；這次沒有異動時寫一列「{NO_CHANGE}」並在原因欄說明"})
    mine = owner_changes(section, changes)
    for file, status in mine.items():
        covering = [(row, token) for row in change_rows for token in row["files"] if covers(token, file)]
        if not covering:
            problems.append({"kind": "改了沒記", "file": file, "detail": f"實際異動為 {status}，表格沒有對應的列"})
            continue
        if status not in STATUS_TEXT:
            continue
        all_types = {row["type"] for row, _ in covering}
        exact_types = {row["type"] for row, token in covering if not token.endswith("/")}
        if status not in all_types or exact_types - {status}:
            recorded = "、".join(sorted(all_types))
            problems.append({"kind": "異動類型不符", "file": file, "detail": f"檔案是這次{STATUS_TEXT[status]}的，對應的列應記為 {status}，目前記為 {recorded}"})
    for row in change_rows:
        for token in row["files"]:
            if not any(covers(token, file) for file in mine):
                problems.append({"kind": "記了沒改", "file": token, "detail": f"第 {row['line']} 行記為 {row['type']}，但基準以來沒有實際異動"})
    return problems


def run_check(context: dict, owner: str | None) -> int:
    if context["changes"] is None:
        raise Abort(f"{context['plan']} 不是進行中的 plan，已交付的 plan 唯讀，不核對異動紀錄。")
    sections = select_sections(context, owner)
    owners = []
    for section in sections:
        problems = check_section(section, context["changes"], context["known_ids"], require_rows=owner is not None)
        owners.append({
            "owner": section["owner"], "paths": section["paths"], "recorded_rows": len(section["rows"]),
            "changed_files": len(owner_changes(section, context["changes"])), "ok": not problems, "problems": problems,
        })
    result = {"plan": context["plan"], "base": context["base"], "owners": owners}
    result["problems"] = [{"kind": "格式", "detail": issue} for issue in context["issues"]]
    if owner is None:
        result["problems"] += [
            {"kind": "沒有 owner", "file": item["file"], "detail": f"實際異動為 {item['status']}，不在任何 owner 的路徑下；請為寫入它的 skill 加上一節並記錄"}
            for item in unowned_changes(context)
        ]
    result["ok"] = not result["problems"] and all(item["ok"] for item in owners)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    for item in owners:
        for problem in item["problems"]:
            print(f"{problem['kind']}：{problem.get('file') or problem['detail']}（{item['owner']}）", file=sys.stderr)
    for problem in result["problems"]:
        print(f"{problem['kind']}：{problem.get('file') or problem['detail']}", file=sys.stderr)
    print("核對通過" if result["ok"] else "核對未通過", file=sys.stderr)
    return 0 if result["ok"] else 1


def parse_feature(text: str) -> tuple[str, list[str], dict[str, list[str]]]:
    """回傳 Feature 標題、第一條 Rule 之前的內容與每條 Rule 的內容；空白行與縮排不算差異。"""
    title = ""
    preamble: list[str] = []
    rules: dict[str, list[str]] = {}
    block = preamble
    pending: list[str] = []
    for line in text.splitlines():
        compact = re.sub(r"\s+", " ", line.strip())
        if not compact:
            continue
        if compact.startswith("@"):
            pending.append(compact)
            continue
        rule = RULE_PATTERN.match(line)
        if rule:
            block = rules.setdefault(re.sub(r"\s+", " ", rule.group(1)), [])
        elif block is preamble and not title:
            feature = FEATURE_PATTERN.match(line)
            if feature:
                title = feature.group(1)
        block.extend(pending)
        pending = []
        if not rule:
            block.append(compact)
    block.extend(pending)
    return title, preamble, rules


def run_rules(context: dict, owner: str | None) -> int:
    if context["changes"] is None:
        raise Abort(f"{context['plan']} 不是進行中的 plan，無法由 git 差異列出異動的 Rule。")
    sections = select_sections(context, owner)
    features = []
    for file, status in context["changes"].items():
        if not file.endswith(".feature"):
            continue
        if owner is not None and not under_paths(file, sections[0]["paths"]):
            continue
        repo_path = f"{context['truth_rel']}/{file}"
        before = parse_feature(git(context["root"], "show", f"{context['base']}:{repo_path}")) if status != "ADD" else ("", [], {})
        after = parse_feature((context["truth_dir"] / file).read_text(encoding="utf-8")) if status != "DEL" else ("", [], {})
        features.append({
            "file": file,
            "status": status,
            "feature": after[0] or before[0],
            "whole_feature": status != "MOD",
            "preamble_changed": status == "MOD" and before[1] != after[1],
            "rules": {
                "added": [title for title in after[2] if title not in before[2]],
                "modified": [title for title in after[2] if title in before[2] and after[2][title] != before[2][title]],
                "deleted": [title for title in before[2] if title not in after[2]],
            },
        })
    print(json.dumps({"plan": context["plan"], "base": context["base"], "features": features}, ensure_ascii=False, indent=2))
    return 0


def run_query(context: dict, owner: str | None, ac: str | None) -> int:
    sections = select_sections(context, owner)
    if ac is not None:
        if not AC_PATTERN.match(ac):
            raise Abort(f"--ac 只接受 AC 編號，收到 {ac}。用法：truth_changes.py query <plan 資料夾> --ac AC-08")
        rows = [
            {"owner": section["owner"], **public_row(row)}
            for section in sections for row in section["rows"] if ac in ID_PATTERN.findall(row["reason"])
        ]
        print(json.dumps({"plan": context["plan"], "ac": ac, "rows": rows}, ensure_ascii=False, indent=2))
        return 0
    owners = []
    for section in sections:
        changed = None
        if context["changes"] is not None:
            changed = [{"status": status, "file": file} for file, status in owner_changes(section, context["changes"]).items()]
        owners.append({
            "owner": section["owner"], "paths": section["paths"],
            "rows": [public_row(row) for row in section["rows"]], "changed": changed,
        })
    result = {"plan": context["plan"], "status": context["status"], "base": context["base"], "owners": owners}
    if owner is None:
        result["unowned"] = unowned_changes(context)
    result["format_issues"] = context["issues"] + [issue for section in sections for issue in section["issues"]]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="解析 plan 的 truth-changes.md 並與 git 的實際差異比對。")
    commands = parser.add_subparsers(dest="command", required=True)
    query = commands.add_parser("query", help="輸出各 truth owner 已記錄的列與基準以來實際異動的 truth 檔案")
    query.add_argument("plan_dir", help="plan 資料夾，例如 specs/plans/004-ranking")
    query.add_argument("--owner", help="只看這個 truth owner（truth-changes.md 中的節名，例如 api-plan）")
    mode = query.add_mutually_exclusive_group()
    mode.add_argument("--ac", help="只列原因含這個開發發現 AC 編號的列，例如 AC-08")
    mode.add_argument("--rules", action="store_true", help="改為列出異動的 feature 中新增、修改、刪除的 Rule 標題")
    check = commands.add_parser("check", help="核對表格與基準以來的實際異動是否一致，不一致時 exit code 為 1")
    check.add_argument("plan_dir", help="plan 資料夾，例如 specs/plans/004-ranking")
    check.add_argument("--owner", help="只核對這個 truth owner；省略時核對所有 owner 與不屬於任何 owner 的異動")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        context = load_context(args.plan_dir)
        if args.command == "check":
            return run_check(context, args.owner)
        if args.rules:
            return run_rules(context, args.owner)
        return run_query(context, args.owner, args.ac)
    except Abort as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
