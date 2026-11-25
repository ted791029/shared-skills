# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""解析 Feature 維度的 tasks.md：輸出每個任務的完成狀態、所屬 Phase 與類型（含「修正 <端點>/<檔名>」的修正 Phase）、標記（紅燈、綠燈、重構、重跑、驗證）、範疇、逐任務的 NFR 約束與必讀，以及每個 Phase 標頭的驗收 AC、NFR 約束、預計修改（展開為完整路徑）與必讀；檢查範疇是否為 specs/truth/features/ 底下的整份 feature、端點資料夾、以「feature 路徑:行號」或「feature 路徑 ＞ Rule「名稱」」指定的 Rule，以及所有必讀錨點的檔案是否存在於 plan 資料夾、specs/truth/ 或專案根目錄；任務依 tasks.md 順序執行，之前的任務全部完成才可執行；--summary 只輸出下一個任務（含所屬 Phase 標頭）、範圍進度、問題清單、各 Phase 進度、驗證任務狀態、已完成任務涵蓋的範疇與檔案。"""

import argparse
import json
import re
import sys
from pathlib import Path

PHASE_PATTERN = re.compile(r"^## Phase (\d+)：(.+?)\s*$")
TASK_PATTERN = re.compile(r"^- \[([ xX])\] (T\d{3})\b\s*(.*)$")
HEADER_PATTERN = re.compile(r"^\*\*(.+?)\*\*[：:]\s*(.*)$")
HEADER_ITEM_PATTERN = re.compile(r"^- (.+)$")
TASK_ANCHOR_PATTERN = re.compile(r"^\s+- 📎 必讀[：:]\s*`([^`]+)`(?:\s*—\s*(.*))?$")
TASK_NFR_PATTERN = re.compile(r"^\s+- NFR 約束[：:]\s*(.+)$")
ANCHOR_ITEM_PATTERN = re.compile(r"^`([^`]+)`(?:\s*—\s*(.*))?$")
STAGE_PATTERN = re.compile(r"\[(紅燈|綠燈|重構|重跑|驗證)\]")
SCOPE_PATTERN = re.compile(r"範疇[：:]\s*`([^`]+)`")
SCOPE_LINES_PATTERN = re.compile(r"^(.*?\.feature)((?::\d+)+)$")
RULE_LINE_PATTERN = re.compile(r"^\s*(?:Rule|規則)\s*[:：]")
RULE_NAME_SEPARATOR = "＞"  # 以 Rule 名稱定位：<feature 路徑> ＞ Rule「A」、Rule「B」
RULE_NAME_OPEN = "Rule「"
FIX_PHASE_PATTERN = re.compile(r"^修正 ([\w.-]+/[^/]+\.feature)$")
TRUTH_DIR = ("specs", "truth")
TRUTH_FEATURES = ("specs", "truth", "features")
NFR_ID_PATTERN = re.compile(r"NFR-\d+")
AC_ID_PATTERN = re.compile(r"AC-\d+")
CODE_SPAN_PATTERN = re.compile(r"`([^`\s]+)`")
FEATURE_PHASE_PATTERN = re.compile(r"^[\w.-]+/[^/]+\.feature$")
EXTENSIONLESS_FILES = (
    "Makefile", "GNUmakefile", "Dockerfile", "Containerfile", "Gemfile", "Rakefile", "Procfile",
    "Jenkinsfile", "Vagrantfile", "Brewfile", "Justfile", "Pipfile", "LICENSE",
)
FILE_PATTERN = re.compile(
    r"^(?:[\w.-]+/)*(?:\.[\w-][\w.-]*|[\w-][\w.-]*\.(?:[a-z][a-z0-9]*|[A-Z])|" + "|".join(EXTENSIONLESS_FILES) + r")$"
)
PHASE_KINDS = {"Setup": "setup", "Foundational": "foundational", "重跑": "rerun", "NFR 重構": "nfr-refactor", "Polish": "polish", "Verify": "verify"}
HEADER_KEYS = {"驗收 AC": "acceptance", "NFR 約束": "nfr", "預計修改": "planned", "📎 必讀": "anchors", "不另列任務": "no_task"}


def phase_kind(name: str) -> str:
    if name in PHASE_KINDS:
        return PHASE_KINDS[name]
    if FIX_PHASE_PATTERN.match(name):
        return "feature-fix"
    return "feature" if FEATURE_PHASE_PATTERN.match(name) else "other"


def phase_feature(phase: dict) -> str | None:
    """Feature Phase 與修正 Phase 標題中的「<端點>/<檔名>.feature」，其他 Phase 為 None。"""
    if phase["kind"] == "feature":
        return phase["name"]
    if phase["kind"] == "feature-fix":
        return FIX_PHASE_PATTERN.match(phase["name"]).group(1)
    return None


def parse_rule_names(text: str) -> list[str] | None:
    """解析「Rule「A」、Rule「B」」，名稱可含成對的「」與頓號；寫法不符時回傳 None。"""
    names: list[str] = []
    index = 0
    text = text.strip()
    while True:
        if not text.startswith(RULE_NAME_OPEN, index):
            return None
        index += len(RULE_NAME_OPEN)
        start, depth = index, 1
        while index < len(text) and depth:
            depth += {"「": 1, "」": -1}.get(text[index], 0)
            index += 1
        name = text[start:index - 1].strip()
        if depth or not name:
            return None
        names.append(name)
        rest = text[index:].lstrip()
        if not rest:
            return names
        if not rest.startswith("、"):
            return None
        index = len(text) - len(rest) + 1
        while index < len(text) and text[index].isspace():
            index += 1


def expand_planned(text: str, root: Path) -> list[str]:
    """展開 Phase 標頭「預計修改」：以「，」分組，組內第一個完整路徑決定基準目錄，之後只寫檔名或子目錄的項目接在基準目錄之後；開頭段落存在於專案根目錄（或與基準同一個頂層目錄）的項目視為完整路徑並更新基準。"""
    files = []
    for group in re.split(r"[，,]", text):
        base = ""
        for span in CODE_SPAN_PATTERN.findall(group):
            if not FILE_PATTERN.match(span):
                continue
            top = span.split("/", 1)[0]
            if "/" in span and (not base or (root / top).exists() or base.split("/", 1)[0] == top):
                base = span.rsplit("/", 1)[0] + "/"
                files.append(span)
            else:
                files.append(base + span)
    return files


def mentioned_files(text: str) -> list[str]:
    """任務描述中的檔案照原文列出；只寫檔名的項目不推測目錄，比對時以檔名比對。"""
    return [span for span in CODE_SPAN_PATTERN.findall(text) if FILE_PATTERN.match(span)]


def expand_refs(text: str) -> list[str]:
    refs = []
    for start, end in re.findall(r"(T\d{3})(?:～(T\d{3}))?", text):
        if not end:
            refs.append(start)
            continue
        first, last = int(start[1:]), int(end[1:])
        refs.extend(f"T{number:03d}" for number in range(first, max(first, last) + 1))
    return refs


def parse_scope(text: str, known: set[str]) -> list[str]:
    """範圍字串如 T005～T013,T029，區間可用 ～、~ 或 -，回傳展開後的任務編號。"""
    refs = expand_refs(re.sub(r"[~-]", "～", text).replace(",", "、"))
    unknown = [ref for ref in refs if ref not in known]
    if unknown:
        raise ValueError(f"範圍中的任務 {'、'.join(unknown)} 不在 tasks.md 內。請確認 --scope 的任務編號。")
    return refs


def project_root(feature_dir: Path) -> Path:
    """tasks.md 位於 <專案根目錄>/specs/plans/<plan 資料夾>/，範疇以專案根目錄為基準；不在這個位置時以目前目錄為專案根目錄。"""
    resolved = feature_dir.resolve()
    if resolved.parent.name == "plans" and resolved.parent.parent.name == "specs":
        return resolved.parent.parent.parent
    return Path.cwd().resolve()


def check_scope(scope: str, feature_dir: Path, phase: dict) -> str | None:
    """範疇必須是 specs/truth/features/ 底下的整份 feature、端點資料夾，或以「feature 路徑:行號」、「feature 路徑 ＞ Rule「名稱」」指定的 Rule；Feature Phase 與修正 Phase 的範疇必須與 Phase 標題一致。"""
    rule_names = None
    if RULE_NAME_SEPARATOR in scope:
        path_text, _, names_text = scope.partition(RULE_NAME_SEPARATOR)
        scope = path_text.strip()
        rule_names = parse_rule_names(names_text)
        if rule_names is None or not scope.endswith(".feature"):
            return "以 Rule 名稱定位的範疇必須寫成「specs/truth/features/<端點>/<檔名>.feature ＞ Rule「<Rule 名稱>」」，多條 Rule 以「、」接續，名稱的括號成對；請以 task 修正 tasks.md"
    with_lines = SCOPE_LINES_PATTERN.match(scope)
    root = project_root(feature_dir)
    target = (root / (with_lines.group(1) if with_lines else scope)).resolve()
    features_dir = root.joinpath(*TRUTH_FEATURES).resolve()
    if features_dir not in target.parents:
        return f"範疇不在 {features_dir.as_posix()} 底下；bdd 只執行 specs/truth/features/ 的端點資料夾"
    if not target.exists():
        return "範疇路徑不存在"
    if target.is_dir():
        if target.parent != features_dir:
            return "範疇資料夾不是端點資料夾（必須是 specs/truth/features/<端點>/）"
        if not any(target.rglob("*.feature")):
            return "範疇資料夾底下沒有任何 .feature 檔"
        return None
    if target.suffix != ".feature":
        return "範疇不是 .feature 檔或端點資料夾"
    expected = phase_feature(phase)
    if expected is not None and target.relative_to(features_dir).as_posix() != expected:
        return f"範疇與 Phase 標題「{phase['name']}」不一致"
    lines = target.read_text(encoding="utf-8").splitlines()
    if with_lines:
        for number in (int(part) for part in with_lines.group(2).split(":") if part):
            if number < 1 or number > len(lines) or not RULE_LINE_PATTERN.match(lines[number - 1]):
                return f"範疇的行號 {number} 不是 Rule 的標題行；以 Rule 為範疇時每個行號都必須指向「Rule:」那一行，請以 task 修正 tasks.md"
    if rule_names:
        titles = [re.split(r"[:：]", line.strip(), maxsplit=1)[1].strip() for line in lines if RULE_LINE_PATTERN.match(line)]
        for name in rule_names:
            if titles.count(name) != 1:
                found = "找不到" if name not in titles else f"有 {titles.count(name)} 條同名的"
                return f"範疇的 Rule「{name}」在 feature 中{found} Rule；名稱必須與「Rule:」行逐字相同且只出現一次，請以 task 修正 tasks.md"
    return None


def anchor_record(anchor: str, reason: str | None, feature_dir: Path) -> dict:
    """必讀的檔案在 plan 資料夾、specs/truth/ 或專案根目錄任一處找得到就算存在。"""
    anchor_file = anchor.split(" › ")[0].strip()
    root = project_root(feature_dir)
    bases = (feature_dir, root.joinpath(*TRUTH_DIR), root)
    return {"anchor": anchor, "reason": (reason or "").strip(), "file": anchor_file, "exists": any((base / anchor_file).is_file() for base in bases)}


def read_tasks(lines: list[str], feature_dir: Path) -> tuple[list[dict], list[dict]]:
    phases, tasks = [], []
    phase = None
    header_key = None
    current = None
    for line_no, line in enumerate(lines, start=1):
        matched_phase = PHASE_PATTERN.match(line)
        if matched_phase:
            name = matched_phase.group(2)
            phase = {
                "number": int(matched_phase.group(1)), "name": name, "kind": phase_kind(name),
                "acceptance": [], "nfr": [], "planned_text": "", "planned_files": [], "anchors": [], "no_task": [],
            }
            phases.append(phase)
            header_key, current = None, None
            continue
        if phase is None:
            continue
        matched_task = TASK_PATTERN.match(line)
        if matched_task:
            body = matched_task.group(3)
            stage = STAGE_PATTERN.search(body)
            scopes = SCOPE_PATTERN.findall(body)
            current = {
                "id": matched_task.group(2), "line": line_no, "done": matched_task.group(1) != " ",
                "phase": phase["number"], "phase_name": phase["name"], "phase_kind": phase["kind"],
                "stage": stage.group(1) if stage else None,
                "scopes": scopes, "description": body,
                "mentioned_files": mentioned_files(SCOPE_PATTERN.sub("", body)),
                "task_nfr": [], "task_anchors": [],
            }
            tasks.append(current)
            header_key = None
            continue
        matched_header = HEADER_PATTERN.match(line)
        if matched_header and current is None:
            header_key = HEADER_KEYS.get(matched_header.group(1).strip())
            value = matched_header.group(2)
            if header_key == "acceptance":
                phase["acceptance"] = AC_ID_PATTERN.findall(value)
            elif header_key == "nfr":
                phase["nfr"] = NFR_ID_PATTERN.findall(value)
            elif header_key == "planned":
                phase["planned_text"] = value
                phase["planned_files"] = expand_planned(value, project_root(feature_dir))
            continue
        if current is not None:
            matched_anchor = TASK_ANCHOR_PATTERN.match(line)
            if matched_anchor:
                current["task_anchors"].append(anchor_record(matched_anchor.group(1), matched_anchor.group(2), feature_dir))
                continue
            matched_nfr = TASK_NFR_PATTERN.match(line)
            if matched_nfr:
                current["task_nfr"].extend(NFR_ID_PATTERN.findall(matched_nfr.group(1)))
            continue
        matched_item = HEADER_ITEM_PATTERN.match(line)
        if matched_item and header_key == "anchors":
            matched_anchor = ANCHOR_ITEM_PATTERN.match(matched_item.group(1).strip())
            if matched_anchor:
                phase["anchors"].append(anchor_record(matched_anchor.group(1), matched_anchor.group(2), feature_dir))
        elif matched_item and header_key == "no_task":
            phase["no_task"].append(matched_item.group(1).strip())
    by_number = {item["number"]: item for item in phases}
    for task in tasks:
        scopes = task.pop("scopes")
        task["scope"] = scopes[0] if len(scopes) == 1 else None
        task["scope_problem"] = None
        if task["stage"] == "驗證":
            if scopes:
                task["scope_problem"] = "[驗證] 任務不得有範疇，verify 一律執行所有端點"
        elif task["stage"] is not None:
            if not scopes:
                task["scope_problem"] = "階段任務沒有「範疇：`specs/truth/features/<端點>/<檔名>.feature`」、端點資料夾或以行號、Rule 名稱指定的 Rule"
            elif len(scopes) > 1:
                task["scope_problem"] = f"階段任務有 {len(scopes)} 個範疇（{'、'.join(scopes)}），只能有一個"
            else:
                task["scope_problem"] = check_scope(scopes[0], feature_dir, by_number[task["phase"]])
    return phases, tasks


def mark_ready(tasks: list[dict]) -> None:
    """Phase 依編號、Phase 內依列出順序：tasks.md 中排在前面的任務全部完成才可執行。"""
    unfinished = []
    for task in sorted(tasks, key=lambda item: item["line"]):
        if not task["done"]:
            task["unfinished_earlier_tasks"] = list(unfinished)
            task["ready"] = not unfinished
            unfinished.append(task["id"])


def applicable_anchors(task: dict, phase: dict) -> list[dict]:
    """任務適用的必讀：逐任務必讀，加上所屬 Phase 標頭的必讀。"""
    return task["task_anchors"] + phase["anchors"]


def done_coverage(tasks: list[dict], by_number: dict) -> dict:
    """已勾選任務涵蓋的範疇與檔案：階段任務的範疇與所屬 Phase 的預計修改，以及無標記任務描述中的路徑。"""
    scopes, files = [], []
    for task in tasks:
        if not task["done"]:
            continue
        if task["stage"] in ("紅燈", "綠燈", "重構"):
            if task["scope"] and task["scope"] not in scopes:
                scopes.append(task["scope"])
            candidates = by_number[task["phase"]]["planned_files"] + task["mentioned_files"]
        elif task["stage"] is None:
            candidates = task["mentioned_files"]
        else:
            candidates = []
        files.extend(path for path in candidates if path not in files)
    return {"scopes": scopes, "files": files}


def summarize_phases(phases: list[dict], tasks: list[dict]) -> list[dict]:
    result = []
    for phase in phases:
        members = [task for task in tasks if task["phase"] == phase["number"]]
        remaining = [task["id"] for task in members if not task["done"]]
        result.append({
            "number": phase["number"], "name": phase["name"], "kind": phase["kind"],
            "task_count": len(members), "done_count": len(members) - len(remaining),
            "complete": bool(members) and not remaining, "remaining": remaining,
            "last_task": members[-1]["id"] if members else None,
        })
    return result


def phase_header(phase: dict) -> dict:
    return {key: phase[key] for key in ("acceptance", "nfr", "planned_text", "planned_files", "anchors")}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="解析 Feature 維度的 tasks.md，輸出任務狀態、標記（紅燈、綠燈、重構、重跑、驗證）、範疇與範疇問題、Phase 標頭（驗收 AC、NFR 約束、預計修改、必讀）、必讀錨點檔案是否存在、依 tasks.md 順序的可執行任務、各 Phase 進度、驗證任務狀態、已完成任務涵蓋的範疇與檔案。"
        "階段任務（含重跑）的範疇寫法為「範疇：`specs/truth/features/<端點>/<檔名>.feature`」、端點資料夾「`specs/truth/features/<端點>/`」、"
        "以行號指定 Rule「`specs/truth/features/<端點>/<檔名>.feature:行號[:行號…]`」（行號是 Rule 的標題行），"
        "或以名稱指定 Rule「`specs/truth/features/<端點>/<檔名>.feature ＞ Rule「<Rule 名稱>」、Rule「<Rule 名稱>」`」（名稱與「Rule:」行逐字相同），路徑以專案根目錄為基準；"
        "Phase 標題為「<端點>/<檔名>.feature」或「修正 <端點>/<檔名>.feature」時，範疇必須是同一份 feature。"
    )
    parser.add_argument("tasks_file", help="tasks.md 路徑，例如 specs/plans/<plan 資料夾>/tasks.md")
    parser.add_argument(
        "--scope",
        help="範圍內的任務編號，例如 T005～T013,T029（區間可用 ～、~ 或 -）；指定後輸出 scope_ready、scope_remaining、scope_blocked 與 next，未指定時範圍為所有任務",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="只輸出摘要（next、next_task（含任務適用的必讀與所屬 Phase 標頭）、scope_remaining_count、scope_blocked、scope_problems、missing_anchors、各 Phase 進度、verify_task、done_coverage）；未指定時輸出完整 JSON",
    )
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    tasks_file = Path(args.tasks_file)
    if not tasks_file.is_file():
        print(f"錯誤：找不到 {tasks_file}。請確認 plan 資料夾，或先執行 /task 產出 tasks.md。", file=sys.stderr)
        return 1
    feature_dir = tasks_file.parent
    phases, tasks = read_tasks(tasks_file.read_text(encoding="utf-8").splitlines(), feature_dir)
    if not tasks:
        print(f"錯誤：{tasks_file} 中沒有任何「## Phase N：…」底下「- [ ] T001 …」格式的任務。請先執行 /task 重新產出 tasks.md。", file=sys.stderr)
        return 1
    mark_ready(tasks)
    by_number = {phase["number"]: phase for phase in phases}
    known = {task["id"] for task in tasks}
    try:
        scope_ids = set(parse_scope(args.scope, known)) if args.scope else known
    except ValueError as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1
    ordered = sorted(tasks, key=lambda item: item["line"])
    scope_remaining = [task["id"] for task in ordered if not task["done"] and task["id"] in scope_ids]
    scope_ready = [task["id"] for task in ordered if task.get("ready") and task["id"] in scope_ids]
    next_id = scope_ready[0] if scope_ready else None
    next_task = next((task for task in tasks if task["id"] == next_id), None)
    verify_tasks = [task for task in tasks if task["stage"] == "驗證"]
    missing = []
    for task in tasks:
        for anchor in applicable_anchors(task, by_number[task["phase"]]):
            if not anchor["exists"] and not any(item["anchor"] == anchor["anchor"] for item in missing):
                missing.append({"anchor": anchor["anchor"], "file": anchor["file"], "first_task": task["id"]})
    result = {
        "next": next_id,
        "next_task": None if next_task is None else {
            **{key: next_task[key] for key in ("id", "line", "phase", "phase_name", "phase_kind", "stage", "scope", "scope_problem", "description", "task_nfr", "mentioned_files")},
            "applicable_anchors": applicable_anchors(next_task, by_number[next_task["phase"]]),
            "phase_header": phase_header(by_number[next_task["phase"]]),
        },
        "scope_remaining_count": len(scope_remaining),
        "scope_ready_count": len(scope_ready),
        "scope_blocked": [
            {"task": task["id"], "unfinished_earlier_tasks": task["unfinished_earlier_tasks"]}
            for task in ordered if task["id"] in scope_remaining and not task.get("ready")
        ],
        "scope_problems": [
            {"task": task["id"], "scope": task["scope"], "problem": task["scope_problem"]}
            for task in tasks if task["scope_problem"] and not task["done"]
        ],
        "missing_anchors": missing,
        "phases": summarize_phases(phases, tasks),
        "verify_task": {
            "ids": [task["id"] for task in verify_tasks],
            "done": [task["id"] for task in verify_tasks if task["done"]],
            "in_scope": [task["id"] for task in verify_tasks if task["id"] in scope_ids],
        },
        "done_coverage": done_coverage(tasks, by_number),
    }
    if not args.summary:
        result["scope_remaining"] = scope_remaining
        result["scope_ready"] = scope_ready
        result["phase_headers"] = [{"number": phase["number"], **phase_header(phase), "no_task": phase["no_task"]} for phase in phases]
        result["tasks"] = tasks
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
