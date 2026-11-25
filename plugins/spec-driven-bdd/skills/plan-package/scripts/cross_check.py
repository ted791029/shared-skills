# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""交叉檢查（上下游一致原則第 4 條）：以可以重算的方式判定上下游有沒有改完。
1. dsl.md 用到的 API 操作、回應欄位、testid 與資料表存在於契約、UI 契約與資料模型；
2. 每個 AC 都有測試（涵蓋表的 AC 涵蓋表指到存在、且有 Example 的 Rule）；
3. tasks.md 的範疇涵蓋基準以來實際異動的 Rule，truth-changes.md 的每一列 DEL 都有移除任務或寫在「不另列任務」；
4. 每一行技術項都有任務（deliver 時要已勾選），或寫在「不另列任務」並附理由；
5. techstack.md 與各 plan 的 research.md 一致（technical-research 的 check_techstack.py）；基準時就有、本 plan 也沒有改到那一列的問題只列為提醒（warnings），不擋傳遞與交付。
round 在每輪傳遞結束（沒有待補跑）時執行，deliver 在交付前執行。"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import plan_trace as trace  # noqa: E402

SKILLS_DIR = Path(__file__).resolve().parents[2]
CHECK_TECHSTACK = SKILLS_DIR / "technical-research" / "scripts" / "check_techstack.py"
OPERATION = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_\-/{}.]*)")
PATH_KEY = re.compile(r"^  (/[^:\s]*):\s*$")
REF_LINE = re.compile(r"^\s+\$ref:\s*(\S+)\s*$")
METHOD_LINE = re.compile(r"^(get|post|put|patch|delete):\s*$")
YAML_KEY = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*):")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
TESTID_ATTR = re.compile(r"data-testid=[\"']([a-z0-9-]+)[\"']")
KEBAB = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")
FIELD_PATH = re.compile(r"^[a-z_][a-z0-9_]*(?:\.[a-z_][a-z0-9_]*)+$")
SNAKE = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
TABLE_LINE = re.compile(r"^\s*Table\s+\"?([A-Za-z0-9_]+)\"?")
COLUMN_LINE = re.compile(r"^\s+\"?([A-Za-z_][A-Za-z0-9_]*)\"?\s+[A-Za-z]")
TASK_LINE = re.compile(r"^\s*-\s+\[( |x|X)\]\s+(T\d+)\s+(.*)$")
TAG = re.compile(r"\[(紅燈|綠燈|重構|驗證|重跑)\]")
SCOPE_SPAN = re.compile(r"`(specs/truth/features/[^`]+)`")
ANCHOR = re.compile(r"📎\s*必讀[：:]\s*`([^`]+)`")
PHASE = re.compile(r"^##\s+Phase\s+\d+[：:]\s*(.*)$")
HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
RENAME_CLAUSE = re.compile(r"改名\s*[：:]\s*原為")


MIN_EXCERPT = 6


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("`", "")).strip()


def plain(text: str) -> str:
    """與 task 的 check_tasks.py 相同的比對方式：去掉所有空白與反引號。"""
    return re.sub(r"[\s`]+", "", text)


def excerpt_hits(excerpts: list[str], target: str) -> bool:
    """任務必讀或「不另列任務」的摘錄（至少 6 個字）是對象原文的一段時算涵蓋，與 check_tasks.py 一致。"""
    return any(len(excerpt) >= MIN_EXCERPT and excerpt in target for excerpt in excerpts)


def exempt_excerpts(items: list[str]) -> list[str]:
    """「不另列任務」每一行冒號前的摘錄；冒號後沒有理由的不算。"""
    found = []
    for entry in items:
        head, _, reason = entry.partition("：")
        if reason.strip():
            found.append(plain(head))
    return found


def problem(check: str, detail: str, home: str, next_step: str) -> dict:
    return {"check": check, "detail": detail, "home": home, "next": next_step}


# ---------- 1. dsl.md 的識別碼 ----------

def contract_operations(truth_dir: Path) -> tuple[set[tuple[str, str]], set[str]]:
    """契約的 (方法, 路徑) 與所有出現過的屬性名稱。"""
    operations: set[tuple[str, str]] = set()
    keys: set[str] = set()
    contracts = truth_dir / "contracts"
    entry = contracts / "openapi.yaml"
    if entry.is_file():
        lines = entry.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            matched = PATH_KEY.match(line)
            if not matched:
                continue
            path = matched.group(1)
            ref = REF_LINE.match(lines[index + 1]) if index + 1 < len(lines) else None
            target = contracts / ref.group(1) if ref else None
            if target and target.is_file():
                for item in target.read_text(encoding="utf-8").splitlines():
                    method = METHOD_LINE.match(item)
                    if method:
                        operations.add((method.group(1).upper(), canonical_path(path)))
    for path in contracts.rglob("*.yaml") if contracts.is_dir() else []:
        for line in path.read_text(encoding="utf-8").splitlines():
            matched = YAML_KEY.match(line)
            if matched:
                keys.add(matched.group(1))
    return operations, keys


def canonical_path(path: str) -> str:
    path = path.split("?")[0].rstrip("/.")
    return re.sub(r"\{[^}]*\}", "{}", path)


def ui_testids(plans_dir: Path) -> set[str]:
    found: set[str] = set()
    for contract in sorted(plans_dir.glob("*/ui/ui-contract.md")):
        text = contract.read_text(encoding="utf-8")
        found |= set(TESTID_ATTR.findall(text))
        found |= {span for span in CODE_SPAN.findall(text) if KEBAB.match(span)}
    return found


def data_names(truth_dir: Path) -> set[str]:
    """資料模型的資料表、欄位、列舉值與約束名稱（約束常寫在 name 設定或 Note 中，所以收集模組檔中出現的所有識別字）。"""
    names: set[str] = set()
    data = truth_dir / "data"
    for path in sorted(data.glob("*.dbml")) if data.is_dir() else []:
        text = path.read_text(encoding="utf-8")
        names |= set(re.findall(r"(?<![A-Za-z0-9_])([a-z][a-z0-9_]*)(?![A-Za-z0-9_])", text))
        for line in text.splitlines():
            table = TABLE_LINE.match(line)
            if table:
                names.add(table.group(1))
    return names


def check_dsl_identifiers(truth_dir: Path, plans_dir: Path) -> list[dict]:
    problems: list[dict] = []
    operations, keys = contract_operations(truth_dir)
    testids = ui_testids(plans_dir)
    tables = data_names(truth_dir)
    features = truth_dir / "features"
    for dsl in sorted(features.glob("*/dsl.md")) if features.is_dir() else []:
        endpoint = dsl.parent.name
        text = dsl.read_text(encoding="utf-8")
        rel = f"features/{endpoint}/dsl.md"
        missing_ops = sorted({f"{method} {path}" for method, path in OPERATION.findall(text)
                              if path.startswith(("/api", "/ws")) and (method, canonical_path(path)) not in operations})
        for item in missing_ops:
            problems.append(problem("dsl.md 識別碼", f"{rel} 用到 `{item}`，契約沒有這個操作", "dsl-refine 或 api-plan",
                                    "先判斷錯在哪一邊：dsl.md 寫錯由 dsl-refine 改；契約缺少由 api-plan 補（經 dev-finding 記錄）"))
        spans = set(CODE_SPAN.findall(text))
        known = keys | tables
        missing_fields = sorted({span for span in spans if FIELD_PATH.match(span)
                                 and any(segment not in known for segment in span.split(".") if "_" in segment)})
        for item in missing_fields:
            absent = [segment for segment in item.split(".") if "_" in segment and segment not in known]
            problems.append(problem("dsl.md 識別碼", f"{rel} 用到欄位 `{item}`，契約與資料模型都沒有 {'、'.join(absent)}", "dsl-refine、api-plan 或 data-plan",
                                    "先判斷錯在哪一邊：dsl.md 寫錯由 dsl-refine 改；契約或資料模型缺少由 api-plan 或 data-plan 補（經 dev-finding 記錄）"))
        if endpoint == "frontend" and testids:
            ids = {span for span in spans if KEBAB.match(span) and not span.startswith(("aria-", "data-"))} | set(TESTID_ATTR.findall(text))
            for item in sorted(ids - testids):
                problems.append(problem("dsl.md 識別碼", f"{rel} 用到 `{item}`，任何 plan 的 ui/ui-contract.md 都沒有這個定位", "ui-ux-plan",
                                        "testid 的家是 UI 契約：由 ui-ux-plan 在本 plan 的 UI 契約補上（畫面在本 plan 標「無」時先由 system-analysis 改為 MOD），或由 dsl-refine 改用 UI 契約既有的定位"))
        if endpoint == "database" and tables:
            for item in sorted({span for span in spans if SNAKE.match(span)} - tables):
                problems.append(problem("dsl.md 識別碼", f"{rel} 用到 `{item}`，資料模型沒有這個資料表或欄位", "dsl-refine 或 data-plan",
                                        "先判斷錯在哪一邊：dsl.md 寫錯由 dsl-refine 改；資料模型缺少由 data-plan 補（經 dev-finding 記錄）"))
    return problems


# ---------- 2. 每個 AC 都有測試 ----------

def coverage_rows(plan_dir: Path) -> list[dict] | None:
    path = plan_dir / "features" / "涵蓋表.md"
    if not path.is_file():
        return None
    rows, header, in_section = [], None, False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## AC 涵蓋表"
            header = None
            continue
        if not in_section or not line.strip().startswith("|") or trace.TABLE_SEP.match(line.strip()):
            continue
        cells = [trace.clean_cell(cell) for cell in trace.split_row(line)]
        if header is None:
            header = cells
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def rule_examples(truth_dir: Path) -> dict[tuple[str, str, str], int]:
    """(端點, feature 檔名, Rule) → Example 數。"""
    found: dict[tuple[str, str, str], int] = {}
    features = truth_dir / "features"
    for path in sorted(features.glob("*/*.feature")) if features.is_dir() else []:
        for block in trace.gherkin_blocks(path.read_text(encoding="utf-8")):
            if block["rule"] is None:
                continue
            key = (path.parent.name, path.name, norm(block["rule"]))
            found.setdefault(key, 0)
            if block["kind"] == "example":
                found[key] += 1
    return found


def check_ac_tests(plan_dir: Path, truth_dir: Path) -> list[dict]:
    acceptance = trace.WorkingSource(plan_dir, truth_dir)
    acs = sorted({unit["ac"] for unit in trace.acceptance_all(acceptance).values() if unit["ac"]})
    if not acs:
        return []
    rows = coverage_rows(plan_dir)
    if rows is None:
        return [problem("AC 測試", "acceptance 有 AC，但 plan 沒有 features/涵蓋表.md", "dsl-refine", "由 dsl-refine 衍生端點 feature 並撰寫涵蓋表")]
    rules = rule_examples(truth_dir)
    problems = []
    for ac in acs:
        mine = [row for row in rows if row.get("AC") == ac]
        tested = [row for row in mine if rules.get((row.get("端點", ""), row.get("feature", ""), norm(row.get("Rule", ""))), 0) > 0]
        if not mine:
            problems.append(problem("AC 測試", f"{ac} 在涵蓋表的 AC 涵蓋表沒有任何一列", "dsl-refine", "由 dsl-refine 為這個 AC 衍生 Rule 並登記涵蓋表"))
        elif not tested:
            targets = "、".join(f"{row.get('端點')}/{row.get('feature')} ＞ Rule「{row.get('Rule')}」" for row in mine)
            problems.append(problem("AC 測試", f"{ac} 在涵蓋表指到的 Rule 不存在或沒有 Example：{targets}", "dsl-refine", "由 dsl-refine 修正涵蓋表或補上 Rule 與 Example"))
    return problems


# ---------- 3. tasks.md 的範疇與實際異動 ----------

def parse_tasks(text: str) -> list[dict]:
    tasks, phase, current = [], "", None
    for line in text.splitlines():
        header = PHASE.match(line)
        if header:
            phase = header.group(1).strip()
            current = None
            continue
        matched = TASK_LINE.match(line)
        if matched:
            current = {"id": matched.group(2), "done": matched.group(1) != " ", "text": matched.group(3), "phase": phase, "anchors": []}
            tag = TAG.search(matched.group(3))
            current["tag"] = tag.group(1) if tag else None
            current["anchors"] += ANCHOR.findall(line)
            tasks.append(current)
            continue
        if current is not None and line.startswith("  "):
            current["anchors"] += ANCHOR.findall(line)
            current["text"] += " " + line.strip()
    return tasks


def no_task_items(text: str, phase_word: str) -> list[str]:
    """某個 Phase 的「不另列任務」清單中，每一行的文字（含理由）。"""
    items, in_phase, in_list = [], False, False
    for line in text.splitlines():
        header = PHASE.match(line)
        if header or line.startswith("## "):
            in_phase = bool(header) and phase_word in header.group(1)
            in_list = False
            continue
        if not in_phase:
            continue
        if line.strip().startswith("**不另列任務**"):
            in_list = True
            continue
        if in_list and re.match(r"^\s*-\s+\[", line):
            in_list = False
        if in_list and re.match(r"^\s*-\s+\S", line):
            items.append(re.sub(r"^\s*-\s+", "", line).strip())
    return items


def rule_names(text: str) -> list[str]:
    """取出範疇中每個 Rule「…」的名稱；名稱本身可能含「」，所以成對計算括號。"""
    names, index, opener = [], 0, "Rule「"
    while True:
        start = text.find(opener, index)
        if start < 0:
            return names
        depth, cursor = 1, start + len(opener)
        while cursor < len(text) and depth:
            depth += 1 if text[cursor] == "「" else -1 if text[cursor] == "」" else 0
            cursor += 1
        if depth == 0:
            names.append(text[start + len(opener):cursor - 1])
        index = cursor


def names_after(text: str, marker: str) -> list[str]:
    """marker 之後以「、」接續的每個「名稱」；名稱本身可能含「」，所以成對計算括號。"""
    start = text.find(marker)
    if start < 0:
        return []
    names, cursor = [], start + len(marker)
    while True:
        while cursor < len(text) and text[cursor] in " 、":
            cursor += 1
        if cursor >= len(text) or text[cursor] != "「":
            return names
        depth, end = 1, cursor + 1
        while end < len(text) and depth:
            depth += 1 if text[end] == "「" else -1 if text[end] == "」" else 0
            end += 1
        if depth:
            return names
        names.append(text[cursor + 1:end - 1])
        cursor = end


def rule_renames(plan_dir: Path) -> dict[str, dict[str, str]]:
    """truth-changes.md 中 Rule 改名的列（MOD 或 ADD、對象是新名稱、摘要含「改名：原為「舊名稱」」）：feature 路徑 → {舊名稱：新名稱}。"""
    record = plan_dir / "truth-changes.md"
    renames: dict[str, dict[str, str]] = {}
    if not record.is_file():
        return renames
    for rows in trace.truth_changes_sections(record.read_text(encoding="utf-8")).values():
        for row in rows.splitlines():
            cells = trace.split_row(row)
            if len(cells) < 3 or cells[0].strip() not in ("MOD", "ADD"):
                continue
            summary = cells[2].replace("`", "")
            clause = RENAME_CLAUSE.search(summary)
            path = re.search(r"`(features/[^`]+\.feature)`", cells[1])
            new = rule_names(cells[1])
            if not clause or not path or len(new) != 1:
                continue
            for old in names_after(summary[clause.end() - len("原為"):], "原為"):
                if norm(old) != norm(new[0]):
                    renames.setdefault(path.group(1), {})[norm(old)] = norm(new[0])
    return renames


def rule_line_map(text: str) -> list[tuple[int, str]]:
    """每條 Rule 的起始行號與名稱（行號從 1 起算）。"""
    found = []
    for number, line in enumerate(text.splitlines(), 1):
        matched = trace.RULE_LINE.match(line.strip())
        if matched:
            found.append((number, norm(matched.group(1))))
    return found


def covered_rules(tasks: list[dict], truth_dir: Path) -> dict[str, set[str] | None]:
    """紅燈、綠燈、重跑任務的範疇：feature 路徑 → 涵蓋的 Rule 名稱（None 表示整份）。"""
    covered: dict[str, set[str] | None] = {}
    for task in tasks:
        if task["tag"] not in ("紅燈", "綠燈", "重跑"):
            continue
        for span in SCOPE_SPAN.findall(task["text"]):
            path_match = re.match(r"specs/truth/(features/[^:＞\s]+\.feature)", span)
            if not path_match:
                continue
            rel = path_match.group(1)
            rest = span[path_match.end():]
            names = {norm(name) for name in rule_names(rest)}
            lines = [int(item) for item in re.findall(r":(\d+)", rest)]
            if not names and lines:
                file = truth_dir / rel
                mapping = rule_line_map(file.read_text(encoding="utf-8")) if file.is_file() else []
                for line in lines:
                    owner = [name for start, name in mapping if start <= line]
                    if owner:
                        names.add(owner[-1])
            if not names and not lines:
                covered[rel] = None
            elif covered.get(rel, set()) is not None:
                covered.setdefault(rel, set())
                covered[rel] |= names
    return covered


def changed_rules(plan_dir: Path, truth_dir: Path, base: str) -> dict[str, dict]:
    """基準以來每份端點 feature 新增、修改、刪除的 Rule；truth-changes.md 記錄改名的 Rule 算修改，不算舊名稱刪除加新名稱新增。"""
    root, truth_rel = trace.git_context(plan_dir)
    before = trace.BaseSource(root, base, truth_rel, truth_dir)
    after = trace.WorkingSource(plan_dir, truth_dir)
    renames = rule_renames(plan_dir)
    result = {}
    files = sorted(set(before.truth_files("features", ".feature")) | set(after.truth_files("features", ".feature")))
    for rel in files:
        if rel.count("/") < 2:
            continue
        old_text, new_text = before.truth_text(rel), after.truth_text(rel)
        old = trace.feature_rule_units(old_text) if old_text is not None else {}
        new = trace.feature_rule_units(new_text) if new_text is not None else {}
        rules = lambda units: {key[len("Rule「"):-1]: value for key, value in units.items() if key.startswith("Rule「")}
        old_rules, new_rules = rules(old), rules(new)
        added = [name for name in new_rules if name not in old_rules]
        modified = [name for name in new_rules if name in old_rules and trace.normalize(new_rules[name]) != trace.normalize(old_rules[name])]
        deleted = [name for name in old_rules if name not in new_rules]
        for before_name, after_name in renames.get(rel, {}).items():
            if before_name in deleted and after_name in added:
                deleted.remove(before_name)
                added.remove(after_name)
                modified.append(after_name)
        shared = [key for key in ("Feature", "Background") if trace.normalize(old.get(key, "")) != trace.normalize(new.get(key, ""))]
        if added or modified or deleted or (shared and old_text is not None and new_text is not None):
            result[rel] = {"added": added, "modified": modified, "deleted": deleted, "shared_changed": bool(shared),
                           "status": "ADD" if old_text is None else "DEL" if new_text is None else "MOD"}
    return result


def check_task_scope(plan_dir: Path, truth_dir: Path, base: str, stage: str) -> list[dict]:
    tasks_path = plan_dir / "tasks.md"
    changes = changed_rules(plan_dir, truth_dir, base)
    deletions = []
    record = plan_dir / "truth-changes.md"
    if record.is_file():
        for owner, rows in trace.truth_changes_sections(record.read_text(encoding="utf-8")).items():
            for row in rows.splitlines():
                cells = trace.split_row(row)
                if len(cells) >= 2 and cells[0].strip() == "DEL":
                    deletions.append((owner, norm(cells[1])))
    if not tasks_path.is_file():
        if (changes or deletions) and stage == "deliver":
            return [problem("tasks.md 範疇", "truth 有異動，但 plan 沒有 tasks.md", "task", "由 task 拆解任務")]
        return []
    text = tasks_path.read_text(encoding="utf-8")
    tasks = parse_tasks(text)
    covered = covered_rules(tasks, truth_dir)
    problems = []
    for rel, change in changes.items():
        if change["status"] == "DEL":
            continue
        scope = covered.get(rel, set())
        if scope is None:
            continue
        need = set(change["added"]) | set(change["modified"])
        if change["shared_changed"]:
            file = truth_dir / rel
            all_rules = {name for _, name in rule_line_map(file.read_text(encoding="utf-8"))} if file.is_file() else set()
            uncovered = sorted(name for name in all_rules if name not in scope)
            if uncovered or not all_rules:
                problems.append(problem("tasks.md 範疇", f"`{rel}` 的 Background 或 Feature 標頭改了，整份 feature 的 Example 都受影響，但紅燈、綠燈、重跑任務的範疇合起來沒有涵蓋："
                                        + ("、".join(f"Rule「{name}」" for name in uncovered) or "整份 feature"),
                                        "task", "由 task 的增量入口補上涵蓋整份 feature 的任務（只改說明時排 [重跑]）"))
            continue
        missing = sorted(name for name in need if norm(name) not in scope)
        if missing:
            problems.append(problem("tasks.md 範疇", f"`{rel}` 的 Rule 改了但沒有紅燈、綠燈或重跑任務涵蓋：" + "、".join(f"Rule「{name}」" for name in missing),
                                    "task", "由 task 的增量入口追加修正 Phase"))
    anchors = [plain(anchor.split("›", 1)[1]) for task in tasks for anchor in task["anchors"] if "›" in anchor]
    exempt = exempt_excerpts(no_task_items(text, "移除"))
    for owner, target in deletions:
        if not excerpt_hits(anchors, plain(target)) and not excerpt_hits(exempt, plain(target)):
            problems.append(problem("tasks.md 範疇", f"truth-changes.md 的 DEL「{target}」（{owner}）沒有移除任務，也不在「不另列任務」", "task", "由 task 的增量入口排移除任務或寫明不另列任務的理由"))
    return problems


# ---------- 4. 技術項 ----------

def check_tech_items(plan_dir: Path, stage: str) -> list[dict]:
    items_path = plan_dir / "技術項.md"
    if not items_path.is_file():
        return []
    items = trace.tech_item_lines(items_path.read_text(encoding="utf-8"))
    if not items:
        return []
    tasks_path = plan_dir / "tasks.md"
    if not tasks_path.is_file():
        return [problem("技術項", f"技術項.md 有 {len(items)} 行，但 plan 沒有 tasks.md", "task", "由 task 為每一行排任務或寫明不另列任務的理由")] if stage == "deliver" else []
    text = tasks_path.read_text(encoding="utf-8")
    tasks = parse_tasks(text)
    exempt = exempt_excerpts(no_task_items(text, "技術項"))
    problems = []
    for item in items:
        problem_text = plain(item["problem"])
        linked = [task for task in tasks for anchor in task["anchors"]
                  if plain(anchor).startswith("技術項.md") and "›" in anchor and excerpt_hits([plain(anchor.split("›", 1)[1])], problem_text)]
        reasons = excerpt_hits(exempt, problem_text)
        if reasons and item["fix_owner"] != "task":
            continue
        if not linked and item["fix_owner"] == "task":
            problems.append(problem("技術項", f"技術項「{item['problem']}」的修正擁有者是 task（要改程式），必須有任務，不能只寫在「不另列任務」", "task", "由 task 的增量入口為它排一個必讀指向 `技術項.md › <問題原文>` 的任務"))
            continue
        if not linked:
            problems.append(problem("技術項", f"技術項「{item['problem']}」沒有任務，也不在「不另列任務」", "task", "由 task 的增量入口排任務，或寫在「不另列任務」並附理由"))
        elif stage == "deliver" and not any(task["done"] for task in linked):
            ids = "、".join(task["id"] for task in linked)
            problems.append(problem("技術項", f"技術項「{item['problem']}」的任務 {ids} 尚未勾選", "implement", "由 implement 完成任務"))
    return problems


# ---------- 5. techstack 與 research ----------

def techstack_problems(techstack: Path, plans_dir: Path, plan_name: str | None) -> list[dict]:
    """以 check_techstack.py 檢查一份 techstack.md，回傳它的問題（type、line、message）。"""
    command = [sys.executable, str(CHECK_TECHSTACK), str(techstack), "--plans", str(plans_dir)]
    if plan_name:
        command += ["--plan", plan_name]
    result = subprocess.run(command, capture_output=True)
    if result.returncode == 0:
        return []
    try:
        return json.loads(result.stdout.decode("utf-8"))["problems"]
    except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError):
        detail = result.stderr.decode("utf-8", errors="replace").strip() or result.stdout.decode("utf-8", errors="replace").strip()
        return [{"type": "error", "line": None, "message": f"check_techstack.py 無法完成檢查：{detail[:1500]}"}]


def changed_lines(root: Path, base: str, rel: str) -> set[int]:
    """基準以來，目前的檔案中新增或修改的行號（git diff -U0 的新版區段）。"""
    code, out, _ = trace.run_git(root, "diff", "-U0", "--no-color", "--no-ext-diff", base, "--", rel)
    found: set[int] = set()
    if code != 0:
        return found
    for line in out.decode("utf-8", errors="replace").splitlines():
        matched = HUNK.match(line)
        if matched:
            start, count = int(matched.group(1)), int(matched.group(2) or 1)
            found.update(range(start, start + count))
    return found


def check_techstack(plan_dir: Path, truth_dir: Path, base: str) -> tuple[list[dict], list[dict]]:
    """回傳（問題、提醒）。基準時的 techstack.md 就有同樣的問題、本 plan 也沒有改到它所在的列時，是先前 plan 留下的，只列為提醒；
    其餘（本 plan 新增、修改或刪除列造成的，以及本 plan 改到的列上原有的問題）擋傳遞與交付。"""
    techstack = truth_dir / "techstack.md"
    if not techstack.is_file() or not CHECK_TECHSTACK.is_file():
        return [], []
    plans_dir = plan_dir.parent
    current = techstack_problems(techstack, plans_dir, plan_dir.name if (plan_dir / "research.md").is_file() else None)
    if not current:
        return [], []
    root, truth_rel = trace.git_context(plan_dir)
    rel = f"{truth_rel}/techstack.md" if truth_rel else "techstack.md"
    code, out, _ = trace.run_git(root, "show", f"{base}:{rel}")
    existed: set[tuple[str, str]] = set()
    if code == 0:
        with tempfile.TemporaryDirectory() as folder:
            before = Path(folder) / "techstack.md"
            before.write_bytes(out)
            existed = {(item.get("type"), item.get("message")) for item in techstack_problems(before, plans_dir, None)}
    touched = changed_lines(root, base, rel)
    issues, reminders = [], []
    for item in current:
        where = f"techstack.md 第 {item['line']} 行：" if item.get("line") else "techstack.md："
        lines = {item.get("line"), item.get("related_line")} - {None}
        if (item.get("type"), item.get("message")) not in existed or lines & touched:
            issues.append(problem("techstack 與 research", where + item["message"], "technical-research", "由 technical-research 修正 techstack.md"))
        else:
            reminders.append(problem("techstack 與 research", where + item["message"], "technical-research",
                                     "先前 plan 留下、本 plan 沒有改到的問題，不擋本 plan 的傳遞與交付；交付後另開技術修正 plan，以技術項交給 technical-research 修正"))
    return issues, reminders


def run(plan_arg: str, stage: str) -> dict:
    plan = trace.load_plan(plan_arg)
    plan_dir, truth_dir, data = plan["dir"], plan["truth_dir"], plan["data"]
    if data.get("status") != trace.IN_PROGRESS:
        raise trace.Abort(f"{plan_dir.name} 不是進行中的 plan，已交付的 plan 唯讀，不做交叉檢查。")
    base = str(data.get("base") or "")
    if not base:
        raise trace.Abort(f"{plan_dir.name} 的 .plan.json 沒有基準 commit（base）。請以 plan-package 重新開立 plan。")
    techstack_issues, reminders = check_techstack(plan_dir, truth_dir, base)
    checks = {
        "dsl.md 識別碼": check_dsl_identifiers(truth_dir, plan_dir.parent),
        "AC 測試": check_ac_tests(plan_dir, truth_dir),
        "tasks.md 範疇": check_task_scope(plan_dir, truth_dir, base, stage),
        "技術項": check_tech_items(plan_dir, stage),
        "techstack 與 research": techstack_issues,
    }
    problems = [item for items in checks.values() for item in items]
    return {"ok": not problems, "plan": plan_dir.name, "stage": stage,
            "checks": {name: ("通過" if not items else f"{len(items)} 個問題") for name, items in checks.items()},
            "problems": problems, "warnings": reminders}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="交叉檢查：dsl.md 的識別碼、AC 的測試、tasks.md 的範疇、技術項的任務與 techstack 的一致。")
    parser.add_argument("plan_dir", help="進行中的 plan 資料夾，例如 specs/plans/004-ranking")
    parser.add_argument("--stage", choices=("round", "deliver"), default="round",
                        help="round：每輪傳遞結束時（技術項只要求有任務）；deliver：交付前（技術項的任務要已勾選、truth 有異動就要有 tasks.md）")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        result = run(args.plan_dir, args.stage)
    except trace.Abort as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    for item in result["problems"]:
        print(f"{item['check']}：{item['detail']}（交給：{item['home']}）", file=sys.stderr)
    for item in result["warnings"]:
        print(f"提醒（先前 plan 留下，不擋交付）：{item['detail']}", file=sys.stderr)
    print("交叉檢查通過" if result["ok"] else f"交叉檢查未通過，{len(result['problems'])} 個問題", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
