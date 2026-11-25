# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""檢查進行中的 plan 的 tasks.md：任務編號連續、殘留樣板內容與已不使用的標記、已勾選的任務是從 T001 起連續的一段且內容與上次拆解記下的相同、
Phase 結構（尚未開始的 Phase 依 Setup → Foundational → Feature 與修正 → 重跑 → 移除 → 技術項 → NFR 重構 → Polish 排列，已開始的部分之後可以重新開始一輪，Verify 唯一且在最後，追加任務時 [驗證] 要重新開放）、
每個尚未開始的 Feature Phase 與修正 Phase 恰好紅燈、綠燈、重構三個任務且範疇是 feature_summary.py 算出的整份 feature 或 Rule 名稱、紅燈的 Rule 數與 Example 數、Phase 標頭的驗收 AC、NFR 約束、預計修改路徑與必讀範圍、
每個 [重跑] 任務的範疇、改動說明與引用的異動列、非 Feature 任務的逐任務必讀、技術項.md 的每一行（修正：task 的行要有任務）、truth-changes.md 的每一列 DEL、只刪除了 Example 的 Rule 與撤回的 Rule 都落在任務或「不另列任務」、
NFR 重構 Phase 對未驗證 NFR 的分割、每個 NFR 重構 Phase 的每個端點資料夾至多一個 [重構] 任務且必讀的 NFR 都是描述的項首，以及錨點檔案與識別碼是否存在；對照的內容取自 feature_summary.py。"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from feature_summary import (  # noqa: E402
    FIX_PREFIX, NFR_ID_PATTERN, RECORD_NAME, RERUN, TECH_FIX, analyze, load_record, parse_id_list, parse_interface_overrides, phase_kind, plain, task_line_hash,
)

PHASE_PATTERN = re.compile(r"^## Phase (\d+)：(.+)$")
TASK_PATTERN = re.compile(r"^- \[([ xX])\] (T\d{3})\b(.*)$")
STAGE_PATTERN = re.compile(r"\[(紅燈|綠燈|重構|驗證|重跑)\]")
SCOPE_PATTERN = re.compile(r"^ \[(紅燈|綠燈|重構|重跑)\] 範疇：`([^`]+)`：(\S.*)$")
RED_PATTERN = re.compile(r"撰寫 (\d+) 條 Rule、(\d+) 個 Example 的 step definitions.*確認因.+而失敗")
GREEN_PATTERN = re.compile(r"讓\s*(?:feature|這些 Rule)\s*通過$")
TASK_ANCHOR_PREFIX = "  - 📎 必讀"
TASK_ANCHOR_PATTERN = re.compile(r"^  - 📎 必讀：`([^`]+)` — (\S.*)$")
HEADER_ANCHOR_PATTERN = re.compile(r"^- `([^`]+)` — (\S.*)$")
TASK_CONSTRAINT_PREFIX = "  - NFR 約束："
NO_TASK_PATTERN = re.compile(r"^- ((?:NFR-\d+)(?:、NFR-\d+)*)：(\S.*)$")
ITEM_NO_TASK_PATTERN = re.compile(r"^- (\S.*?)：(\S.*)$")
REFACTOR_ITEM_PATTERN = re.compile(r"(?:^|；)\s*(NFR-\d+(?:、NFR-\d+)*)：")
LEFTOVER_PATTERN = re.compile(r"\{\{[^}]*\}\}|<!-- 重複(開始|結束)")
FORBIDDEN = (
    (re.compile(r"依賴 T\d{3}"), "任務相依（Phase 依編號、Phase 內依列出順序執行，不寫依賴）"),
    (re.compile(r"🎯|🔴|🟡"), "🎯／🔴／🟡 標記（需求、預期失敗與可能直接通過不再逐任務列出）"),
    (re.compile(r"\[US\d+\]|\[P\]"), "[US]／[P] 標記"),
    (re.compile(r"^#{3,4} "), "### 或 #### 段落（Feature 維度不分端點段與 feature 段）"),
    (re.compile(r"首次使用"), "首次使用句型清單"),
    (re.compile(r"已知覆寫"), "已知覆寫（這個機制已作廢，truth 中的 Example 直接修改或刪除）"),
)
TOKEN_SPLIT_PATTERN = re.compile(r"[\s／～]+")
FILE_TOKEN_PATTERN = re.compile(r"^[\w.\-/\[\]]+\.\w+$")
HEADER_KEYS = ("**驗收 AC**：", "**NFR 約束**：", "**預計修改**：", "**📎 必讀**：")
NO_TASK_KEY = "**不另列任務**："
TECH_PHASE, REMOVE_PHASE, NFR_PHASE, VERIFY_PHASE = "技術項", "移除", "NFR 重構", "Verify"
FEATURE_KINDS = ("Feature", "修正")
RANK = {"Setup": 0, "Foundational": 1, "Feature": 2, "修正": 2, RERUN: 3, REMOVE_PHASE: 4, TECH_PHASE: 5, NFR_PHASE: 6, "Polish": 7}
ORDER_TEXT = "Setup → Foundational → Feature 與修正 → 重跑 → 移除 → 技術項 → NFR 重構 → Polish"
REQUIRED_PHASES = {"需求": ("Setup", "Foundational", REMOVE_PHASE, TECH_PHASE, NFR_PHASE, "Polish"), TECH_FIX: (REMOVE_PHASE, TECH_PHASE)}
EXCLUDED_PHASES = {TECH_FIX: ("Setup", "Foundational", "Feature", NFR_PHASE, "Polish")}
ANCHORED_PHASES = ("Setup", "Foundational", TECH_PHASE, REMOVE_PHASE)
TECH_FILE, CHANGES_FILE, TECHSTACK_FILE, TASKS_FILE = "技術項.md", "truth-changes.md", "techstack.md", "tasks.md"
RERUN_ENDING = "確認既有 step 不用改後重新執行"
MIN_EXCERPT = 6
FRONTEND, BACKEND = "frontend", "backend"


def problem(kind: str, line: int | None, message: str) -> dict:
    return {"type": kind, "line": line, "message": message}


def nfr_key(nfr: str) -> int:
    return int(nfr.split("-")[1])


# ---------- 讀取 tasks.md ----------

def read_tasks(lines: list[str]) -> tuple[list[dict], list[dict], list[dict]]:
    phases, tasks, problems = [], [], []
    phase = current = None
    section = None
    for line_no, line in enumerate(lines, start=1):
        matched = PHASE_PATTERN.match(line)
        if matched:
            name = matched.group(2).strip()
            kind = phase_kind(name)
            feature = name[len(FIX_PREFIX):] if kind == "修正" else (name if kind == "Feature" else None)
            phase = {"number": int(matched.group(1)), "name": name, "kind": kind, "line": line_no, "feature": feature,
                     "headers": {}, "header_order": [], "anchors": [], "no_task": [], "no_task_items": [], "tasks": []}
            phases.append(phase)
            current, section = None, None
            continue
        if phase is None:
            continue
        key = next((key for key in HEADER_KEYS + (NO_TASK_KEY,) if line.startswith(key)), None)
        if key:
            phase["headers"][key] = (line_no, line[len(key):].strip())
            phase["header_order"].append(key)
            section, current = key, None
            continue
        task = TASK_PATTERN.match(line)
        if task:
            body = task.group(3)
            stage = STAGE_PATTERN.search(body)
            current = {"id": task.group(2), "line": line_no, "raw": line, "body": body, "phase": phase, "checked": task.group(1) != " ",
                       "stage": stage.group(1) if stage else None, "anchors": [], "constraints": set()}
            tasks.append(current)
            phase["tasks"].append(current)
            section = None
            continue
        if current is not None and line.startswith(TASK_ANCHOR_PREFIX):
            anchor = TASK_ANCHOR_PATTERN.match(line)
            if anchor:
                current["anchors"].append((line_no, anchor.group(1)))
            else:
                problems.append(problem("format", line_no, "必讀格式不符，請寫成「  - 📎 必讀：`檔案 › 段落 › 識別碼` — 需讀原因」，原因不得為空。"))
            continue
        if current is not None and line.startswith(TASK_CONSTRAINT_PREFIX):
            current["constraints"] |= set(NFR_ID_PATTERN.findall(line))
            continue
        if section == "**📎 必讀**：" and line.startswith("- "):
            anchor = HEADER_ANCHOR_PATTERN.match(line)
            if anchor:
                phase["anchors"].append((line_no, anchor.group(1)))
            else:
                problems.append(problem("format", line_no, "Phase 標頭的必讀格式不符，請寫成「- `檔案 › 段落 › 識別碼` — 需讀原因」。"))
        elif section == NO_TASK_KEY and line.startswith("- "):
            if phase["kind"] in (TECH_PHASE, REMOVE_PHASE):
                entry = ITEM_NO_TASK_PATTERN.match(line)
                if entry:
                    phase["no_task_items"].append((line_no, entry.group(1)))
                else:
                    problems.append(problem("format", line_no, "「不另列任務」的每行請寫成「- <該行技術項、該列 DEL 對象或撤回的 Rule 的原文片段>：理由」。"))
                continue
            entry = NO_TASK_PATTERN.match(line)
            if entry:
                phase["no_task"].append((line_no, set(NFR_ID_PATTERN.findall(entry.group(1)))))
            else:
                problems.append(problem("format", line_no, "「不另列任務」的每行請寫成「- NFR-xxx、NFR-yyy：理由」。"))
    return phases, tasks, problems


def started_numbers(phases: list[dict], tasks: list[dict]) -> set[int]:
    """最後一個已勾選任務（[驗證] 除外）所在的 Phase 之前（含）為已開始的部分。"""
    checked = [task for task in tasks if task["checked"] and task["stage"] != "驗證"]
    if not checked:
        return set()
    last = checked[-1]["phase"]["number"]
    return {phase["number"] for phase in phases if phase["number"] <= last and phase["kind"] != VERIFY_PHASE}


def fully_started(phase: dict, started: set[int]) -> bool:
    """已開始、而且任務全部勾選的 Phase：只保留，不再檢查內容。"""
    return phase["number"] in started and all(task["checked"] for task in phase["tasks"])


# ---------- 與 truth 的 feature 無關的檢查 ----------

def check_text(lines: list[str]) -> list[dict]:
    problems = []
    for line_no, line in enumerate(lines, start=1):
        if LEFTOVER_PATTERN.search(line):
            problems.append(problem("leftover", line_no, "殘留樣板填位符號或重複區塊註解，請替換為實際內容或刪除。"))
        for pattern, label in FORBIDDEN:
            if pattern.search(line):
                problems.append(problem("format", line_no, f"出現已不使用的{label}，請刪除。"))
    return problems


def check_numbering(tasks: list[dict]) -> list[dict]:
    for expected, task in enumerate(tasks, start=1):
        if task["id"] != f"T{expected:03d}":
            return [problem("numbering", task["line"], f"任務編號應為 T{expected:03d}，收到 {task['id']}；請依出現順序從 T001 連續編號（已勾選的任務不改編號，尚未開始的任務接著編號）。")]
    return []


def check_checked(tasks: list[dict], record: dict | None) -> list[dict]:
    """已勾選的任務必須是從 T001 起連續的一段（implement 依序執行），且內容與上次拆解記下的相同。"""
    problems = []
    first_open = next((index for index, task in enumerate(tasks) if not task["checked"]), len(tasks))
    for task in tasks[first_open + 1:]:
        if task["checked"]:
            problems.append(problem("checked", task["line"], f"{task['id']} 已勾選，但它之前有未勾選的任務；implement 依序執行，已勾選的任務必須是從 T001 起連續的一段，請確認勾選是否正確。"))
            break
    lines = (record or {}).get("lines", {})
    for task in tasks:
        if task["checked"] and task["id"] in lines and lines[task["id"]] != task_line_hash(task["raw"]):
            problems.append(problem("checked", task["line"], f"{task['id']} 已勾選，內容卻與上次拆解時記下的不同；已勾選的任務保留原本的內容與編號，要重做的部分請在尚未開始的部分追加 Phase。"))
    return problems


def check_phase_structure(phases: list[dict], tasks: list[dict], kind: str, started: set[int]) -> list[dict]:
    problems = []
    for expected, phase in enumerate(phases, start=1):
        if phase["number"] != expected:
            problems.append(problem("phase", phase["line"], f"Phase 編號應為 {expected}，收到 {phase['number']}；請從 1 連續編號。"))
            break
    for phase in phases:
        if phase["kind"] == "other":
            problems.append(problem("phase", phase["line"], f"Phase「{phase['name']}」不是 Setup、Foundational、`<端點資料夾>/<檔名>.feature`、`修正 <端點資料夾>/<檔名>.feature`、重跑、移除、技術項、NFR 重構、Polish 或 Verify，請依樣板改名或移除。"))
    verify = [phase for phase in phases if phase["kind"] == VERIFY_PHASE]
    if len(verify) != 1 or (phases and phases[-1]["kind"] != VERIFY_PHASE):
        problems.append(problem("phase", None, "tasks.md 必須恰好有一個 Verify Phase，而且是最後一個 Phase；追加任務時把 Verify Phase 移到最後。"))
    kinds = [phase["kind"] for phase in phases]
    for name in REQUIRED_PHASES.get(kind, REQUIRED_PHASES["需求"]):
        if name not in kinds:
            problems.append(problem("phase", None, f"缺少「{name}」Phase；沒有任務的 Phase 也要保留標題並寫一句說明。"))
    for name in EXCLUDED_PHASES.get(kind, ()):
        for phase in phases:
            if phase["kind"] == name:
                problems.append(problem("phase", phase["line"], f"技術修正 plan 只排修正 Phase、重跑、移除、技術項與 Verify，不得有「{phase['name']}」。"))
    pending = [phase for phase in phases if phase["number"] not in started and phase["kind"] in RANK]
    previous = None
    for phase in pending:
        rank = RANK[phase["kind"]]
        if previous is not None and (rank < RANK[previous["kind"]] or (rank == RANK[previous["kind"]] and phase["kind"] not in FEATURE_KINDS)):
            problems.append(problem("phase", phase["line"], f"尚未開始的 Phase 必須依 {ORDER_TEXT} 排列、每種固定 Phase 一個，最後是 Verify；「{phase['name']}」排在「{previous['name']}」之後。已開始的 Phase 不移動，新的 Phase 接在它們之後重新開始一輪。"))
            break
        previous = phase
    return problems


def check_verify(phases: list[dict], tasks: list[dict], started: set[int]) -> list[dict]:
    problems = []
    verify_tasks = [task for task in tasks if task["stage"] == "驗證"]
    for phase in phases:
        if phase["kind"] == VERIFY_PHASE:
            if len(phase["tasks"]) != 1 or phase["tasks"][0]["stage"] != "驗證":
                problems.append(problem("verify", phase["line"], "Verify Phase 必須只有一個標 [驗證] 的任務。"))
        elif any(task["stage"] == "驗證" for task in phase["tasks"]):
            problems.append(problem("verify", phase["line"], f"「{phase['name']}」有 [驗證] 任務，[驗證] 只能出現在最後的 Verify Phase。"))
    pending_tasks = [task for task in tasks if task["phase"]["number"] not in started and task["stage"] != "驗證"]
    if pending_tasks and any(task["checked"] for task in verify_tasks):
        problems.append(problem("verify", verify_tasks[0]["line"], f"{verify_tasks[0]['id']} [驗證] 已勾選，但它之前還有尚未完成的任務（{pending_tasks[0]['id']} 起）；追加任務時要取消 [驗證] 的勾選，讓全端點驗證在最後重新執行。"))
    return problems


def anchor_file(anchor: str) -> str:
    return anchor.split("›")[0].strip()


def check_base_tasks(phases: list[dict], started: set[int]) -> list[dict]:
    problems = []
    required_file = {"Setup": (TECHSTACK_FILE,), TECH_PHASE: (TECH_FILE,), REMOVE_PHASE: (CHANGES_FILE, TASKS_FILE)}
    hint = {"Setup": "`techstack.md › 套件安裝清單 › <workspace>` 等具體列", TECH_PHASE: "`技術項.md › <該行的原文片段>`",
            REMOVE_PHASE: "`truth-changes.md › <該列 DEL 的對象>`，撤回的 Rule 則為實作它的 `tasks.md › <已勾選的任務編號>`"}
    for phase in phases:
        if fully_started(phase, started):
            continue
        kind = phase["kind"]
        for task in phase["tasks"]:
            if task["checked"]:
                continue
            if task["stage"] == RERUN and kind != RERUN:
                problems.append(problem("stage", task["line"], f"{task['id']} 標 [重跑]，[重跑] 任務只能放在「重跑」Phase。"))
            if kind == RERUN and task["stage"] != RERUN:
                problems.append(problem("stage", task["line"], f"{task['id']} 在重跑 Phase，只能標 [重跑]。"))
            if kind not in ANCHORED_PHASES + ("Polish",):
                continue
            if task["stage"]:
                problems.append(problem("stage", task["line"], f"{task['id']} 在 {kind}，不得標 [{task['stage']}]。"))
            if kind != "Polish" and not task["anchors"]:
                problems.append(problem("anchor", task["line"], f"{task['id']} 沒有 📎 必讀，{kind} 任務由 implement 直接實作，必須逐任務列出要對照的位置。"))
            wanted = required_file.get(kind)
            if wanted and not any(anchor_file(anchor) in wanted for _, anchor in task["anchors"]):
                problems.append(problem("anchor", task["line"], f"{task['id']} 是 {kind} 任務，必須有指向 {hint[kind]} 的必讀。"))
            for nfr in sorted(task["constraints"] - spec_nfrs(task["anchors"])):
                problems.append(problem("anchor", task["line"], f"{task['id']} 的 NFR 約束 {nfr} 沒有對應的必讀，請補上 `spec.md › {nfr}`。"))
    return problems


def spec_nfrs(anchors: list[tuple[int, str]]) -> set[str]:
    return {nfr for _, anchor in anchors if anchor.startswith("spec.md ›") for nfr in NFR_ID_PATTERN.findall(anchor)}


def piece_found(piece: str, text: str, is_yaml: bool) -> bool:
    if piece in text:
        return True
    tokens = [token for token in TOKEN_SPLIT_PATTERN.split(piece) if token]
    if is_yaml:
        tokens = [part for token in tokens for part in token.split(".") if part]
    return bool(tokens) and all(token in text for token in tokens)


def locate(name: str, bases: list[Path]) -> Path | None:
    return next((base / name for base in bases if (base / name).is_file()), None)


def check_anchor_targets(phases: list[dict], bases: list[Path], started: set[int]) -> list[dict]:
    problems = []
    cache: dict[Path, str] = {}
    live = [phase for phase in phases if not fully_started(phase, started)]
    anchors = [anchor for phase in live if phase["number"] not in started for anchor in phase["anchors"]]
    anchors += [anchor for phase in live for task in phase["tasks"] if not task["checked"] for anchor in task["anchors"]]
    for line_no, anchor in anchors:
        segments = [segment.strip() for segment in anchor.split("›")]
        path = locate(segments[0], bases)
        if path is None:
            problems.append(problem("anchor", line_no, f"錨點檔案 {segments[0]} 在 plan 資料夾、specs/truth/ 與專案根目錄都找不到；plan 的檔案請寫相對於 plan 資料夾的路徑（如 `spec.md`、`ui/ui-contract.md`），truth 的檔案寫相對於 specs/truth/ 的路徑（如 `data/房間.dbml`、`techstack.md`）。"))
            continue
        if path not in cache:
            cache[path] = path.read_text(encoding="utf-8")
        is_yaml = path.suffix in {".yaml", ".yml"}
        for segment in segments[1:]:
            for piece in (piece.strip() for piece in segment.split("、") if piece.strip()):
                if not piece_found(piece, cache[path], is_yaml):
                    problems.append(problem("anchor", line_no, f"錨點片段「{piece}」不存在於 {segments[0]}，請改為該檔案中實際的標題、識別碼或欄位名稱。"))
    return problems


# ---------- 技術項與移除 ----------

def excerpt_of(anchor: str) -> str:
    return plain(anchor.split("›", 1)[1]) if "›" in anchor else ""


def check_remove_phases(phases: list[dict], summary: dict, started: set[int]) -> list[dict]:
    """每一列 DEL、只刪除了 Example 的 Rule 與撤回的 Rule 都要被某個移除 Phase 的任務或「不另列任務」涵蓋。"""
    problems = []
    remove = [phase for phase in phases if phase["kind"] == REMOVE_PHASE]
    if not remove:
        return problems
    deletions = [(f"truth-changes.md 第 {item['line']} 行的 {item['type']}（{item['owner']}）", plain(item["target"])) for item in summary["deletions"]]
    withdrawn = [(f"撤回的 {item['key']} Rule「{item['rule']}」（由 {'、'.join(item['tasks'])} 實作）", plain(f"Rule「{item['rule']}」")) for item in summary["withdrawn"]]
    anchors = [(phase, task, line_no, excerpt_of(anchor)) for phase in remove for task in phase["tasks"]
               for line_no, anchor in task["anchors"] if anchor_file(anchor) == CHANGES_FILE]
    bodies = [plain(task["body"]) for phase in remove for task in phase["tasks"]]
    exempt = [(phase, line_no, plain(text)) for phase in remove for line_no, text in phase["no_task_items"]]
    for phase, task, line_no, excerpt in anchors:
        if fully_started(phase, started) or task["checked"]:
            continue
        if len(excerpt) < MIN_EXCERPT or not any(excerpt in target for _, target in deletions):
            problems.append(problem("item", line_no, f"「移除」引用的 truth-changes.md 片段找不到對應的 DEL 列或只刪除了 Example 的列；請照抄該列對象欄的原文（至少 {MIN_EXCERPT} 個字）。"))
    for phase, line_no, text in exempt:
        if fully_started(phase, started):
            continue
        matches_row = len(text) >= MIN_EXCERPT and any(text in target for _, target in deletions)
        matches_rule = any(marker in text for _, marker in withdrawn)
        if not matches_row and not matches_rule:
            problems.append(problem("item", line_no, "「移除」的「不另列任務」這一行對不到任何一列 DEL、只刪除了 Example 的列或撤回的 Rule；請照抄該列對象欄的原文，撤回的 Rule 寫成「Rule「名稱」」。"))
    for label, target in deletions:
        cited = any(len(excerpt) >= MIN_EXCERPT and excerpt in target for _, _, _, excerpt in anchors)
        if not cited and not any(len(text) >= MIN_EXCERPT and text in target for _, _, text in exempt):
            problems.append(problem("item", remove[-1]["line"], f"{label} 沒有落在「移除」Phase 的任務必讀（`truth-changes.md › <對象原文>`）或「不另列任務」；請排移除任務，沒有程式要移除時寫在「不另列任務」並附理由。"))
    for label, marker in withdrawn:
        if not any(marker in body for body in bodies) and not any(marker in text for _, _, text in exempt):
            problems.append(problem("item", remove[-1]["line"], f"{label} 已不在 truth，程式與 step 仍在；請在「移除」Phase 排描述寫出「Rule「名稱」」、必讀指向實作它的 `tasks.md › <任務編號>` 的移除任務，沒有程式要移除時寫在「不另列任務」並附理由。"))
    has_items = deletions or withdrawn
    for phase in remove:
        if not has_items and not fully_started(phase, started) and (any(not task["checked"] for task in phase["tasks"]) or phase["no_task_items"]):
            problems.append(problem("item", phase["line"], "這次沒有任何一列 DEL、只刪除了 Example 的 Rule 或撤回的 Rule，「移除」Phase 不應有任務或「不另列任務」，請只保留一句說明。"))
    return problems


def check_tech_phases(phases: list[dict], summary: dict, started: set[int]) -> list[dict]:
    """技術項.md 的每一行都要被某個技術項 Phase 的任務必讀或「不另列任務」涵蓋；修正的擁有者是 task 的行只有程式要改，必須有任務。"""
    problems = []
    tech = [phase for phase in phases if phase["kind"] == TECH_PHASE]
    if not tech:
        return problems
    items = summary["tech_items"]
    anchors = [(phase, task, line_no, excerpt_of(anchor)) for phase in tech for task in phase["tasks"]
               for line_no, anchor in task["anchors"] if anchor_file(anchor) == TECH_FILE]
    exempt = [(phase, line_no, plain(text)) for phase in tech for line_no, text in phase["no_task_items"]]
    problems_texts = [plain(item["problem"]) for item in items]
    for phase, task, line_no, excerpt in anchors:
        if fully_started(phase, started) or task["checked"]:
            continue
        if len(excerpt) < MIN_EXCERPT:
            problems.append(problem("item", line_no, f"「技術項」的引用片段太短，無法判斷是哪一項；請照抄技術項.md 其中一行問題部分（括號之前）至少 {MIN_EXCERPT} 個字的連續原文。"))
        elif not any(excerpt in text for text in problems_texts):
            problems.append(problem("item", line_no, "「技術項」引用的片段在技術項.md 各行的問題部分（括號之前）找不到；請照抄其中一行的連續原文。"))
    for phase, line_no, text in exempt:
        if not fully_started(phase, started) and (len(text) < MIN_EXCERPT or not any(text in item for item in problems_texts)):
            problems.append(problem("item", line_no, "「技術項」的「不另列任務」這一行對不到技術項.md 任何一行的問題部分；請照抄該行括號之前至少 6 個字的連續原文。"))
    for item, text in zip(items, problems_texts):
        linked = any(len(excerpt) >= MIN_EXCERPT and excerpt in text for _, _, _, excerpt in anchors)
        listed = any(len(entry) >= MIN_EXCERPT and entry in text for _, _, entry in exempt)
        if item.get("fix_owner") == "task" and not linked:
            problems.append(problem("item", tech[-1]["line"], f"技術項.md 第 {item['line']} 行的修正擁有者是 task（只有程式要改），必須排一個必讀指向 `技術項.md › <問題原文>` 的任務，不能只寫在「不另列任務」。"))
        elif not linked and not listed:
            problems.append(problem("item", tech[-1]["line"], f"技術項.md 第 {item['line']} 行沒有落在「技術項」Phase 的任務必讀（`技術項.md › <問題原文>`）或「不另列任務」；請排一個任務，沒有程式要修改時寫在「不另列任務」並附理由。"))
    for phase in tech:
        if not items and not fully_started(phase, started) and (any(not task["checked"] for task in phase["tasks"]) or phase["no_task_items"]):
            problems.append(problem("item", phase["line"], "技術項.md 沒有任何一行，「技術項」Phase 不應有任務或「不另列任務」，請只保留一句說明。"))
    return problems


# ---------- 對照 truth 的 feature 的檢查 ----------

def endpoint_rank(endpoint: str) -> int:
    return {BACKEND: 1, FRONTEND: 2}.get(endpoint, 0)


def check_feature_phases(phases: list[dict], summary: dict, own_docs: dict[str, set[str]], started: set[int]) -> list[dict]:
    problems = []
    expected = {entry["phase"]: entry for entry in summary["phases"]}
    keys = {entry["key"]: entry["phase"] for entry in summary["phases"]}
    skipped = {item["key"]: item["reason"] for item in summary["skipped_features"]}
    pending = [phase for phase in phases if phase["kind"] in FEATURE_KINDS and phase["number"] not in started]
    seen: dict[str, int] = {}
    for index, phase in enumerate(pending):
        title = phase["name"]
        if phase["feature"] in {pending[i]["feature"] for i in seen.values()}:
            problems.append(problem("phase", phase["line"], f"{phase['feature']} 在尚未開始的部分已有 Phase，每份端點 feature 在尚未開始的部分只能有一個 Feature Phase 或修正 Phase。"))
            continue
        seen[title] = index
        entry = expected.get(title)
        if entry is None:
            key = phase["feature"]
            if key in keys:
                reason = f"應寫成「{keys[key]}」（feature 已有勾選的階段任務時追加修正 Phase，否則是 Feature Phase）"
            elif key in summary["removed_features"]:
                reason = "這次被整份刪除，請改在「移除」Phase 排移除任務"
            elif key in skipped:
                reason = f"{skipped[key]}，不排 Phase"
            else:
                reason = "沒有要重做紅燈、綠燈、重構的 Rule（或不在 specs/truth/features/ 底下），不排 Phase"
            problems.append(problem("phase", phase["line"], f"Phase「{title}」：{reason}。"))
            continue
        problems += check_feature_tasks(phase, entry)
        problems += check_feature_header(phase, entry, own_docs.get(entry["endpoint"], set()), summary["unverified_nfrs"])
    for title in expected:
        if title not in seen:
            problems.append(problem("phase", None, f"{title} 有要紅燈、綠燈、重構的 Rule，卻沒有這個 Phase（尚未開始的部分）。"))
    for file in {entry["file"] for entry in summary["phases"]}:
        group = sorted((index, pending[index]["feature"].split("/")[0]) for title, index in seen.items()
                       if title in expected and expected[title]["file"] == file)
        ranks = [endpoint_rank(endpoint) for _, endpoint in group]
        if ranks != sorted(ranks):
            order = "、".join(endpoint for _, endpoint in group)
            problems.append(problem("order", None, f"同名 feature {file} 的 Phase 順序為 {order}；組內必須由被呼叫的端點到呼叫者：儲存等內層端點 → backend → frontend。"))
    return problems


def check_feature_tasks(phase: dict, entry: dict) -> list[dict]:
    problems = []
    scope = entry["scope"]
    whole = "＞" not in scope
    scope_note = "整份 feature（不帶 Rule）" if whole else "以 Rule 名稱列出的這些 Rule（feature_summary.py 的 scope）"
    stages = [task["stage"] for task in phase["tasks"]]
    if stages != ["紅燈", "綠燈", "重構"]:
        return [problem("task", phase["line"], f"「{phase['name']}」的任務應恰為 [紅燈]、[綠燈]、[重構] 三個，依序排列，收到 {stages}。")]
    for task in phase["tasks"]:
        matched = SCOPE_PATTERN.match(task["body"])
        if not matched:
            problems.append(problem("scope", task["line"], f"{task['id']} 請寫成「[{task['stage']}] 範疇：`{scope}`：描述」。"))
            continue
        if matched.group(2) != scope:
            problems.append(problem("scope", task["line"], f"{task['id']} 的範疇應為 `{scope}`，也就是{scope_note}，收到 `{matched.group(2)}`。"))
        description = matched.group(3)
        if task["stage"] == "紅燈":
            counts = RED_PATTERN.search(description)
            if not counts:
                problems.append(problem("red", task["line"], f"{task['id']} 的描述請寫成「撰寫 {entry['rule_count']} 條 Rule、{entry['example_count']} 個 Example 的 step definitions（與 Driver），確認因<本層原因>而失敗」。"))
            elif (int(counts.group(1)), int(counts.group(2))) != (entry["rule_count"], entry["example_count"]):
                problems.append(problem("red", task["line"], f"{task['id']} 寫 {counts.group(1)} 條 Rule、{counts.group(2)} 個 Example，但 {entry['phase']} 的範疇實際有 {entry['rule_count']} 條 Rule、{entry['example_count']} 個 Example（場景大綱以標題計）。"))
        if task["stage"] == "綠燈" and not GREEN_PATTERN.search(description):
            ending = "讓 feature 通過" if whole else "讓這些 Rule 通過"
            problems.append(problem("green", task["line"], f"{task['id']} 的描述請以「<要實作什麼>，{ending}」結尾。"))
        if task["stage"] == "重構" and "不改變行為" not in description:
            problems.append(problem("refactor", task["line"], f"{task['id']} 的描述請寫成「整理<範圍>，不改變行為」。"))
        if task["anchors"]:
            problems.append(problem("anchor", task["line"], f"{task['id']} 有逐任務必讀；Feature Phase 與修正 Phase 的必讀只寫在 Phase 標頭。"))
    return problems


def check_feature_header(phase: dict, entry: dict, own_docs: set[str], unverified: list[str]) -> list[dict]:
    problems = []
    headers = phase["headers"]
    order = [key for key in phase["header_order"] if key in HEADER_KEYS]
    expected = [key for key in HEADER_KEYS if key in headers]
    for key in ("**驗收 AC**：", "**預計修改**：", "**📎 必讀**："):
        if key not in headers:
            problems.append(problem("header", phase["line"], f"「{phase['name']}」缺少 {key}。"))
    if order != expected:
        problems.append(problem("header", phase["line"], f"「{phase['name']}」的標頭順序應為驗收 AC、NFR 約束（可無）、預計修改、📎 必讀。"))
    if "**驗收 AC**：" in headers:
        line_no, text = headers["**驗收 AC**："]
        listed = re.findall(r"\bAC-\d+\b", text)
        expected_acs = entry["acceptance"]
        if (listed or ["無"]) != (expected_acs or ["無"]) or (not listed and text != "無"):
            problems.append(problem("acceptance", line_no, f"「{phase['name']}」的驗收 AC 應為 {'、'.join(expected_acs) or '無'}（涵蓋表 AC 涵蓋表中同端點、同 feature、異動為 ADD 或 MOD、Rule 在範疇內的 AC），收到 {text or '（空白）'}。"))
    if "**預計修改**：" in headers:
        line_no, text = headers["**預計修改**："]
        files = [token for token in re.findall(r"`([^`]+)`", text) if FILE_TOKEN_PATTERN.match(token)]
        if not files and not (entry["kind"] == "修正" and text == "無"):
            hint = "；修正 Phase 的綠燈不需要改產品程式時寫「無」" if entry["kind"] == "修正" else ""
            problems.append(problem("planned", line_no, f"「{phase['name']}」的預計修改沒有任何檔案路徑，請列出 plan.md 原始碼中綠燈要改的檔案{hint}。"))
        for group in text.split("，"):
            group_files = [token for token in re.findall(r"`([^`]+)`", group) if FILE_TOKEN_PATTERN.match(token)]
            if group_files and "/" not in group_files[0]:
                problems.append(problem("planned", line_no, f"預計修改的「{group_files[0]}」前面沒有同組的完整路徑；每組第一個檔案寫完整路徑，同目錄的後續檔名以「、」接，不同目錄以「，」分組。"))
    constraints = set(NFR_ID_PATTERN.findall(headers.get("**NFR 約束**：", (0, ""))[1]))
    anchored = spec_nfrs(phase["anchors"])
    for nfr in sorted(constraints - anchored):
        problems.append(problem("anchor", headers["**NFR 約束**："][0], f"「{phase['name']}」的 NFR 約束 {nfr} 沒有對應的必讀，請在 Phase 必讀補上 `spec.md › {nfr}`。"))
    line_no = headers.get("**NFR 約束**：", (phase["line"], ""))[0]
    for nfr in sorted(constraints - set(unverified), key=nfr_key):
        problems.append(problem("constraint", line_no, f"「{phase['name']}」的 NFR 約束 {nfr} 已由 Rule 驗證或不在 spec.md，NFR 約束只能是未驗證的 NFR。"))
    if constraints != set(entry["nfr_constraints"]):
        listed = "、".join(sorted(constraints, key=nfr_key)) or "（無）"
        wanted = "、".join(entry["nfr_constraints"]) or "（無，省略整段）"
        problems.append(problem("constraint", line_no, f"「{phase['name']}」的 NFR 約束應為 {wanted}（介面 {'、'.join(entry['interfaces']) or '無'} 的依據需求扣掉任何 Rule 已驗證的 NFR；介面來源 {entry['interfaces_source']}，只走到部分介面時以 --interfaces 指定），收到 {listed}。"))
    if "**📎 必讀**：" in headers and not phase["anchors"]:
        problems.append(problem("anchor", headers["**📎 必讀**："][0], f"「{phase['name']}」的 📎 必讀沒有任何錨點。"))
    for line_no, anchor in phase["anchors"]:
        path = anchor_file(anchor)
        if path.startswith("features/"):
            problems.append(problem("anchor", line_no, f"Feature Phase 必讀不得列 `{path}`：範疇的 feature、該端點 dsl.md 與用語表由 bdd 每個階段自己讀取。"))
        elif any(path == doc or (doc.endswith("/") and path.startswith(doc)) for doc in own_docs):
            problems.append(problem("anchor", line_no, f"Feature Phase 必讀不得列 `{path}`：它是 {entry['endpoint']} 端點 Planner 的產出文檔，bdd 每個階段會整份讀取。"))
    return problems


def check_rerun_phases(phases: list[dict], summary: dict, started: set[int]) -> list[dict]:
    """尚未開始的部分，feature_summary.py 列出的每個 [重跑] 範疇恰好一個 [重跑] 任務，描述寫出每項改動，必讀引用每一列標明只改說明的異動。"""
    problems = []
    expected = {entry["scope"]: entry for entry in summary["reruns"]}
    pending = [task for phase in phases if phase["kind"] == RERUN and phase["number"] not in started for task in phase["tasks"]]
    matched: set[str] = set()
    for task in pending:
        scope_match = SCOPE_PATTERN.match(task["body"])
        if not scope_match or scope_match.group(1) != RERUN:
            problems.append(problem("rerun", task["line"], f"{task['id']} 請寫成「[重跑] 範疇：`<feature_summary.py 的 reruns 的 scope>`：<改動>，{RERUN_ENDING}」。"))
            continue
        scope, description = scope_match.group(2), scope_match.group(3)
        entry = expected.get(scope)
        if entry is None:
            keys = {item["key"]: item["scope"] for item in summary["reruns"]}
            key = scope.split("/features/", 1)[-1].split(" ＞", 1)[0]
            hint = f"應為 `{keys[key]}`" if key in keys else "這個範疇沒有只需重新執行的 Rule"
            problems.append(problem("rerun", task["line"], f"{task['id']} 的範疇 `{scope}` 不在 feature_summary.py 的 reruns；{hint}。"))
            continue
        if scope in matched:
            problems.append(problem("rerun", task["line"], f"{task['id']} 與前面的 [重跑] 任務範疇相同，每個範疇只排一個 [重跑] 任務。"))
            continue
        matched.add(scope)
        if not description.endswith(RERUN_ENDING):
            problems.append(problem("rerun", task["line"], f"{task['id']} 的描述請以「{RERUN_ENDING}」結尾。"))
        for change in entry["changes"]:
            if change not in description:
                problems.append(problem("rerun", task["line"], f"{task['id']} 的描述沒有寫出改動「{change}」；請照抄 reruns 的 changes，以「；」分隔。"))
        cited = [excerpt_of(anchor) for _, anchor in task["anchors"] if anchor_file(anchor) == CHANGES_FILE]
        for row in entry["rows"]:
            if not any(plain(row) in excerpt for excerpt in cited):
                problems.append(problem("rerun", task["line"], f"{task['id']} 沒有引用 truth-changes.md 中標明改動的列；請補上「  - 📎 必讀：`truth-changes.md › {row}` — 這次改了什麼以此為準」。"))
    for scope, entry in expected.items():
        if scope not in matched:
            problems.append(problem("rerun", None, f"`{scope}` 有只需重新執行的 Rule（{'；'.join(entry['changes'])}），卻沒有 [重跑] 任務；請在「重跑」Phase 排一個 [重跑] 任務。"))
    return problems


def check_nfr_phases(phases: list[dict], summary: dict, scope_root: str, folders: set[str], started: set[int]) -> list[dict]:
    problems = []
    nfr_phases = [phase for phase in phases if phase["kind"] == NFR_PHASE]
    if not nfr_phases:
        return problems
    unverified = set(summary["unverified_nfrs"])
    listed: dict[str, tuple[int, bool]] = {}
    in_tasks: dict[str, tuple[int, bool]] = {}
    for phase in nfr_phases:
        live = not fully_started(phase, started)
        for line_no, nfrs in phase["no_task"]:
            for nfr in nfrs:
                listed[nfr] = (line_no, live)
        refactor_by_folder: dict[str, str] = {}
        for task in phase["tasks"]:
            for nfr in spec_nfrs(task["anchors"]):
                in_tasks.setdefault(nfr, (task["line"], live and not task["checked"]))
            if not live or task["checked"]:
                continue
            if task["stage"] not in (None, "重構"):
                problems.append(problem("stage", task["line"], f"{task['id']} 在 NFR 重構 Phase，只能標 [重構]（不改行為的結構調整）或不標階段（量測、門檻對照等由 implement 直接實作的工作）。"))
            if task["stage"] == "重構":
                matched = SCOPE_PATTERN.match(task["body"])
                scope = matched.group(2) if matched else ""
                folder = scope[len(scope_root):-1] if scope.startswith(scope_root) and scope.endswith("/") else None
                if folder not in folders:
                    problems.append(problem("scope", task["line"], f"{task['id']} 的範疇應為端點資料夾 `{scope_root}<端點資料夾>/`（{('、'.join(sorted(folders)))}），收到 `{scope or '（無）'}`。"))
                elif folder in refactor_by_folder:
                    problems.append(problem("refactor", task["line"], f"{task['id']} 與 {refactor_by_folder[folder]} 都是 {folder} 的 [重構] 任務；同一個 NFR 重構 Phase 的同一端點資料夾只能有一個 [重構] 任務，請把 {task['id']} 的各項併入 {refactor_by_folder[folder]} 的描述與必讀，後續編號順延。"))
                else:
                    refactor_by_folder[folder] = task["id"]
                heads = {nfr for group in REFACTOR_ITEM_PATTERN.findall(matched.group(3) if matched else "") for nfr in NFR_ID_PATTERN.findall(group)}
                for nfr in sorted(spec_nfrs(task["anchors"]) - heads, key=nfr_key):
                    problems.append(problem("refactor", task["line"], f"{task['id']} 的必讀有 `spec.md › {nfr}`，但描述沒有以「{nfr}：」開頭的一項；描述寫在任務那一行，每項寫成「NFR-xxx：<檔案與做法>」並以「；」分隔（implement 只把任務那一行交給 bdd refactor）。"))
            if not task["anchors"]:
                problems.append(problem("anchor", task["line"], f"{task['id']} 沒有 📎 必讀，NFR 重構任務必須附 `spec.md › NFR-xxx` 與必要的介面文檔。"))
    for nfr in sorted(set(listed) & set(in_tasks), key=nfr_key):
        if listed[nfr][1] and in_tasks[nfr][1]:
            problems.append(problem("nfr", listed[nfr][0], f"{nfr} 同時列在「不另列任務」與任務的必讀，每個未驗證 NFR 只能在其中一處。"))
    for nfr in sorted(unverified - set(listed) - set(in_tasks), key=nfr_key):
        problems.append(problem("nfr", nfr_phases[-1]["line"], f"{nfr} 沒有被任何 Rule 驗證，必須列在 NFR 重構 Phase 的任務必讀（`spec.md › {nfr}`）或「不另列任務」並寫理由。"))
    for nfr in sorted((set(listed) | set(in_tasks)) - unverified, key=nfr_key):
        line_no, live = listed.get(nfr) or in_tasks.get(nfr)
        if live:
            problems.append(problem("nfr", line_no, f"{nfr} 已由 Rule 驗證或不在 spec.md，不應列在 NFR 重構 Phase。"))
    return problems


def check_in_progress(summary: dict) -> list[dict]:
    progress = summary["tasks_state"]["in_progress"] or {}
    problems = [problem("scope", None, f"進行中的「{progress['title']}」的 {item['task']} 範疇中有已不存在的 {'、'.join(item['rules'])}；請把它們從未勾選任務的範疇刪去，全部不存在時刪除這個未勾選的任務。")
                for item in progress.get("missing_rules", [])]
    for item in progress.get("renamed_rules", []):
        olds = "、".join("Rule「" + pair["from"] + "」" for pair in item["rules"])
        news = "、".join("Rule「" + pair["to"] + "」" for pair in item["rules"])
        problems.append(problem("scope", None, f"進行中的「{progress['title']}」的 {item['task']} 範疇中的 {olds} 已改名；請把這個未勾選任務的範疇依序改為 {news}，不要刪除任務。"))
    return problems


def parse_own_docs(values: list[str]) -> dict[str, set[str]]:
    own: dict[str, set[str]] = {}
    for value in values:
        endpoint, _, path = value.partition("=")
        if endpoint and path:
            own.setdefault(endpoint.strip(), set()).add(path.strip())
    return own


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查進行中的 plan 的 tasks.md：編號、已勾選任務的位置與內容、Phase 結構與順序（已開始的部分之後可重新開始一輪、Verify 唯一且在最後並在追加任務時重新開放）、"
                                                 "每個尚未開始的 Feature Phase 與修正 Phase 的三個任務與範疇、紅燈 Rule／Example 數、Phase 標頭、[重跑] 任務、非 Feature 任務的必讀、技術項、DEL 列與撤回 Rule 的涵蓋、NFR 重構分割與錨點。")
    parser.add_argument("tasks_path", help="要檢查的 tasks.md 路徑，例如 specs/plans/004-ranking/tasks.md；它所在的資料夾就是 plan 資料夾")
    parser.add_argument("--own-doc", action="append", default=[], metavar="端點資料夾=路徑",
                        help="該端點 Planner 產出的介面文檔，Feature Phase 必讀不得列入；路徑的寫法與必讀相同（plan 的檔案相對於 plan 資料夾，truth 的檔案相對於 specs/truth/），以 / 結尾時視為資料夾；可重複，例如 --own-doc backend=contracts/ --own-doc database=data/ --own-doc frontend=ui/。未提供時略過此項並列在 skipped")
    parser.add_argument("--interfaces", action="append", default=[], metavar="端點資料夾/檔名.feature=介面ID,介面ID",
                        help="轉交 feature_summary.py：該 feature 經 dsl.md 走到的介面 ID，用來計算應有的 NFR 約束；未指定時為該端點的全部介面")
    parser.add_argument("--verified-nfr", action="append", default=[], metavar="NFR-xxx,NFR-yyy",
                        help="轉交 feature_summary.py：確認每個條件都被 Rule 驗證的 NFR，與執行 feature_summary.py 時帶入的相同；未指定的 NFR 一律視為未驗證")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    tasks_path = Path(args.tasks_path)
    if not tasks_path.is_file():
        print(f"錯誤：找不到 {tasks_path}，請傳入 plan 資料夾中 tasks.md 的路徑，例如 specs/plans/004-ranking/tasks.md。", file=sys.stderr)
        return 1
    plan_dir = tasks_path.resolve().parent
    truth_dir = plan_dir.parent.parent / "truth"
    if plan_dir.parent.name != "plans" or not truth_dir.is_dir() or tasks_path.name != TASKS_FILE:
        print(f"錯誤：{tasks_path} 不是 <specs>/plans/<plan 資料夾>/tasks.md，或找不到 <specs>/truth/；請傳入 specs/plans/<plan 資料夾>/tasks.md。", file=sys.stderr)
        return 1
    project_root = plan_dir.parent.parent.parent
    lines = tasks_path.read_text(encoding="utf-8").splitlines()
    phases, tasks, problems = read_tasks(lines)
    if not tasks:
        print("錯誤：找不到任何「- [ ] T001 …」格式的任務，請確認檔案為依樣板撰寫的 tasks.md。", file=sys.stderr)
        return 1
    summary, summary_problems, _ = analyze(plan_dir, parse_interface_overrides(args.interfaces), parse_id_list(args.verified_nfr))
    kind = summary["kind"] if summary else "需求"
    record, _ = load_record(plan_dir / RECORD_NAME)
    started = started_numbers(phases, tasks)
    own_docs = parse_own_docs(args.own_doc)
    problems += check_text(lines) + check_numbering(tasks) + check_checked(tasks, record)
    problems += check_phase_structure(phases, tasks, kind, started) + check_verify(phases, tasks, started) + check_base_tasks(phases, started)
    problems += check_anchor_targets(phases, [plan_dir, truth_dir, project_root], started)
    problems += summary_problems
    skipped = []
    if summary is not None:
        scope_root = f"{truth_dir.relative_to(project_root).as_posix()}/features/"
        folders = {name for name in summary["endpoint_order"] if name}
        problems += check_feature_phases(phases, summary, own_docs, started) + check_rerun_phases(phases, summary, started)
        problems += check_nfr_phases(phases, summary, scope_root, folders, started)
        problems += check_remove_phases(phases, summary, started) + check_tech_phases(phases, summary, started) + check_in_progress(summary)
        missing_own = sorted({entry["endpoint"] for entry in summary["phases"]} - set(own_docs))
        if missing_own:
            skipped.append(f"未提供 --own-doc 的端點（{'、'.join(missing_own)}）沒有檢查 Feature Phase 必讀是否列了本端點 Planner 的產出文檔")
    result = {
        "task_count": len(tasks),
        "checked_count": sum(task["checked"] for task in tasks),
        "phase_count": len(summary["phases"]) if summary else 0,
        "rule_count": sum(entry["rule_count"] for entry in summary["phases"]) if summary else 0,
        "rerun_count": len(summary["reruns"]) if summary else 0,
        "problems": problems,
        "skipped": skipped,
        "warnings": summary["warnings"] if summary else [],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
