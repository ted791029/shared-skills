# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""統計進行中的 plan 要排的 Feature Phase、修正 Phase 與 [重跑] 任務：範疇（整份 feature，或以 Rule 名稱列出的 Rule）、範疇內的 Rule 數與 Example 數、驗收 AC、Rule 需求聯集、
涵蓋的最高優先故事與 NFR 約束（走到的介面在 plan.md 介面盤點「依據需求」中的 NFR，扣掉任何 Rule 已驗證的 NFR），依故事優先、最小 AC、檔名列出同名 feature 組。
新增或修改的 Rule 之外，用到改了測試寫法的句型、Background、預設值或用語表參數值的 Rule 也算受影響；dsl-refine 在 truth-changes.md 以「只改說明：」標明的改動、只改了註解或只刪除了 Example 的 Rule 改排 [重跑]。
truth-changes.md 以「改名：原為「舊名稱」」記錄的 Rule 改名（既有 Rule 記在 MOD 列，本 plan 新增的 Rule 記在 ADD 列），新舊名稱視為同一條 Rule：只改名時排 [重跑]，舊名稱不算刪除或撤回。
tasks.md 已有勾選的任務時，已開始的 feature 以上次拆解記下的逐 Example 狀態（plan 資料夾的 .task.json）為參考點，只把之後變了的 Rule 列入修正 Phase，尚未開始的任務依目前的輸入重新規劃。
並列出被整份刪除的 feature、truth-changes.md 的每一列 DEL、只刪除了 Example 的 Rule、已勾選任務實作過但已撤回的 Rule、技術項.md 的每一行、這次異動的技術堆疊，以及 spec.md 中沒有被任何 Rule 驗證的 NFR；
--record 在拆解完成後寫入 .task.json。技術修正 plan 只需要 truth-changes.md、技術項.md 與 truth 的端點資料夾。"""

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "truth-changes" / "scripts"))
import truth_changes  # noqa: E402

REQUIREMENT_ID_PATTERN = re.compile(r"\b(?:FR|NFR|SC)-\d+\b")
NFR_ID_PATTERN = re.compile(r"\bNFR-\d+\b")
AC_ID_PATTERN = re.compile(r"\bAC-\d+\b")
US_PATTERN = re.compile(r"\bUS(\d+)\b")
STORY_HEADING_PATTERN = re.compile(r"^###\s+使用者故事\s*(\d+)\b.*?(?:優先順序|Priority)\s*[:：]\s*P(\d+)")
HEADING_PATTERN = re.compile(r"^(#{2,3})\s")
DEFINITION_PATTERN = re.compile(r"^\s*-\s*\*\*((?:FR|NFR|SC)-\d+)\*\*")
COVER_PATTERN = re.compile(r"^\s*#\s*(?:涵蓋|開發發現)[:：](.+)$")
TECH_ITEM_PATTERN = re.compile(r"^- (\S.*)$")
FIX_OWNER_PATTERN = re.compile(r"修正[：:]\s*([A-Za-z0-9-]+)")
STEP_PATTERN = re.compile(r"^(?:Given|When|Then|And|But)\s+(.*)$")
PARAMETER_PATTERN = re.compile(r"\{[^{}]+\}")
PHASE_PATTERN = re.compile(r"^## Phase (\d+)：(.+?)\s*$")
TASK_PATTERN = re.compile(r"^- \[([ xX])\] (T\d{3})\b(.*)$")
STAGE_PATTERN = re.compile(r"\[(紅燈|綠燈|重構|驗證|重跑)\]")
SCOPE_SPAN_PATTERN = re.compile(r"範疇：`([^`]+)`")
LINE_SCOPE_PATTERN = re.compile(r"^(.+?\.feature)((?::\d+)+)$")
FEATURE_KEY_PATTERN = re.compile(r"^[^/\s]+/[^/\s]+\.feature$")
DSL_VALUE_HEADING_PATTERN = re.compile(r"^### `\{[^{}]+\}`")
FEATURE_KEYWORDS = ("Feature", "Business Need", "Ability", "功能")
RULE_KEYWORDS = ("Rule", "規則")
BACKGROUND_KEYWORDS = ("Background", "背景")
SCENARIO_KEYWORDS = ("Scenario Outline", "Scenario Template", "場景大綱", "劇本大綱", "Scenario", "Example", "場景", "劇本")
ACCEPTANCE_DIR = "acceptance"
GLOSSARY = "用語表.md"
COVERAGE = "涵蓋表.md"
TECH_ITEMS = "技術項.md"
FEATURES_DIR = "features"
TECHSTACK = "techstack.md"
TASKS_NAME = "tasks.md"
RECORD_NAME = ".task.json"
VALUES_SECTION = "參數合法值"
TECH_FIX = "技術修正"
REQUIREMENT_KIND = "需求"
WORK_CHANGES = ("ADD", "MOD")
STAGES = ("紅燈", "綠燈", "重構")
RERUN = "重跑"
VERIFY = "驗證"
FIX_PREFIX = "修正 "
RULE_SEPARATOR = " ＞ "
DOC_ONLY = "只改說明"
REWRITE = "改測試寫法"
RENAME_CLAUSE = re.compile(r"改名\s*[：:]\s*原為")
MERGED_INTO = re.compile(r"併入「([^」]+)」")
KEPT_PATTERN = re.compile(r"句型「(.+)」")
DEFAULTS_COMMENT = "# 預設值"
FRONTEND = "frontend"
BACKEND = "backend"
FIXED_PHASES = ("Setup", "Foundational", RERUN, "移除", "技術項", "NFR 重構", "Polish", "Verify")
BLOCK_KEYS = ("core", "defaults", "other")
PREAMBLE_KEYS = ("header", "core", "defaults", "other")
NOT_IN_PROGRESS = ("{plan} 不是進行中的 plan（狀態：{status}）：已交付的 plan 唯讀，也無法再由 git 的差異得知它這次異動的 Rule；"
                   "要修改或補做時請開立新的 plan（有需求時以 /specify，只為技術修正時以 plan-package 的 open）。")


def problem(kind: str, message: str) -> dict:
    return {"type": kind, "line": None, "message": message}


def digest(lines: list[str]) -> str:
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()[:12]


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def plain(text: str) -> str:
    return re.sub(r"[\s`]+", "", text)


def keyword_of(line: str, keywords: tuple[str, ...]) -> bool:
    stripped = line.strip()
    return any(re.match(rf"^{re.escape(keyword)}\s*[:：]", stripped) for keyword in keywords)


def title_of(line: str) -> str:
    return compact(re.split(r"[:：]", line.strip(), maxsplit=1)[1])


def ac_number(ac: str) -> int:
    return int(ac.split("-")[1])


def nfr_number(nfr: str) -> int:
    return int(nfr.split("-")[1])


def split_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def task_line_hash(line: str) -> str:
    """任務那一行的摘要，勾選狀態不算差異。"""
    return digest([re.sub(r"^- \[[ xX]\]", "- [ ]", line.rstrip())])


# ---------- 以 Rule 名稱定位的範疇 ----------

def rule_refs(text: str) -> list[str]:
    """取出「Rule「名稱」」中的名稱；名稱本身含「」時依括號成對計算。"""
    names, index, opener = [], 0, "Rule「"
    while True:
        start = text.find(opener, index)
        if start < 0:
            return names
        depth, position = 1, start + len(opener)
        while position < len(text) and depth:
            if text[position] == "「":
                depth += 1
            elif text[position] == "」":
                depth -= 1
            position += 1
        if depth:
            return names
        names.append(compact(text[start + len(opener):position - 1]))
        index = position


def renamed_from(summary: str) -> list[str]:
    """改動摘要中「改名：原為「舊名稱」、「更早的名稱」」的每個舊名稱（MOD 列寫在開頭，ADD 列接在新增說明之後）；名稱本身含「」時依括號成對計算。"""
    text = summary.replace("`", "")
    matched = RENAME_CLAUSE.search(text)
    if not matched:
        return []
    names, position = [], matched.end()
    while True:
        while position < len(text) and text[position] in " 、":
            position += 1
        if position >= len(text) or text[position] != "「":
            return names
        depth, cursor = 1, position + 1
        while cursor < len(text) and depth:
            if text[cursor] == "「":
                depth += 1
            elif text[cursor] == "」":
                depth -= 1
            cursor += 1
        if depth:
            return names
        names.append(compact(text[position + 1:cursor - 1]))
        position = cursor


def rename_map(rows: list[dict]) -> dict[str, dict[str, str]]:
    """truth-changes.md 中 Rule 改名的列（MOD 或 ADD、對象是新名稱、摘要含「改名：原為「舊名稱」」）：feature 鍵 → {舊名稱：新名稱}。"""
    renames: dict[str, dict[str, str]] = {}
    for row in rows:
        olds = renamed_from(row["summary"]) if row["type"] in ("MOD", "ADD") else []
        names = rule_refs(row["target"].replace("`", "")) if olds else []
        if len(names) != 1:
            continue
        for file in row["files"]:
            if file.startswith(FEATURES_DIR + "/") and file.endswith(".feature"):
                for old in olds:
                    if old != names[0]:
                        renames.setdefault(file[len(FEATURES_DIR) + 1:], {})[old] = names[0]
    return renames


def scope_text(scope_root: str, key: str, names: list[str], ordered: list[str]) -> str:
    """範疇涵蓋 feature 的全部 Rule 時寫整份 feature 的路徑，否則依 feature 中的順序以 Rule 名稱列出。"""
    chosen = set(names)
    if chosen >= set(ordered):
        return scope_root + key
    return scope_root + key + RULE_SEPARATOR + "、".join(f"Rule「{name}」" for name in ordered if name in chosen)


def parse_scope(scope: str | None, scope_root: str) -> dict:
    """範疇 → feature 鍵（端點資料夾/檔名）與 Rule 名稱或行號；整份 feature 時兩者皆為 None，端點資料夾或其他範疇的鍵為 None。"""
    empty = {"key": None, "names": None, "lines": None}
    if not scope or not scope.startswith(scope_root):
        return empty
    rest = scope[len(scope_root):]
    if "＞" in rest:
        path, _, tail = rest.partition("＞")
        return {"key": path.strip(), "names": rule_refs(tail), "lines": None}
    with_lines = LINE_SCOPE_PATTERN.match(rest)
    if with_lines:
        return {"key": with_lines.group(1), "names": None, "lines": [int(number) for number in with_lines.group(2).split(":") if number]}
    if FEATURE_KEY_PATTERN.match(rest):
        return {"key": rest, "names": None, "lines": None}
    return empty


# ---------- feature 的狀態 ----------

def new_block(line: int = 0) -> dict:
    return {"line": line, "core": [], "defaults": [], "other": [], "steps": []}


def flush(pending: list[str], block: dict) -> None:
    for item in pending:
        if item.startswith("@"):
            block["core"].append(item)
        elif item.startswith(DEFAULTS_COMMENT):
            block["defaults"].append(item)
        else:
            block["other"].append(item)
    pending.clear()


def unique_title(examples: dict, title: str) -> str:
    key, number = title, 2
    while key in examples:
        key, number = f"{title}#{number}", number + 1
    return key


def feature_state(text: str) -> dict:
    """把 feature 切成 Feature 標頭、最上層的 Background 與每條 Rule（Rule 標頭與每個 Example），每塊的行分成內容（含標籤）、預設值註解與其他註解；
    空白與縮排不算差異。Rule 標頭含 Rule 內的 Background；Rule 名稱是它的鍵，不算進標頭的內容，只改名時內容的摘要不變。
    不在 Rule 底下的 Example 各自視為一條以標題命名的 Rule。"""
    header, background = new_block(), new_block()
    rules: dict[str, dict] = {}
    block, rule, pending, fence = header, None, [], None
    for number, raw in enumerate(text.splitlines(), start=1):
        line = compact(raw)
        if not line:
            continue
        if fence:
            block["core"].append(line)
            if line.startswith(fence):
                fence = None
            continue
        if line.startswith(("#", "@")):
            pending.append(line)
            continue
        if keyword_of(line, FEATURE_KEYWORDS) and block is header:
            flush(pending, header)
            header["core"].append(line)
            continue
        if keyword_of(line, BACKGROUND_KEYWORDS):
            block = background if rule is None else rule["head"]
        elif keyword_of(line, RULE_KEYWORDS):
            name = unique_title(rules, title_of(line))
            rule = {"line": number, "head": new_block(number), "examples": {}}
            rules[name] = rule
            block = rule["head"]
            flush(pending, block)
            continue
        elif keyword_of(line, SCENARIO_KEYWORDS):
            title = title_of(line)
            if rule is None or rule.get("standalone"):
                name = unique_title(rules, title)
                rule = {"line": number, "head": new_block(number), "examples": {}, "standalone": True}
                rules[name] = rule
            block = new_block(number)
            rule["examples"][unique_title(rule["examples"], title)] = block
        flush(pending, block)
        block["core"].append(line)
        if line.startswith(('"""', "```")):
            fence = line[:3]
            continue
        step = STEP_PATTERN.match(line)
        if step:
            block["steps"].append(step.group(1))
    flush(pending, block)
    return {"header": header, "background": background, "rules": rules}


def hashes(block: dict) -> dict:
    return {"core": digest(block["core"]), "defaults": digest(block["defaults"]), "other": digest(block["other"])}


def pack(snap: dict) -> dict:
    """紀錄用的精簡寫法：每塊的摘要以「|」接成一個字串。"""
    def join(values: dict, keys: tuple[str, ...]) -> str:
        return "|".join(values[key] for key in keys)
    return {"preamble": join(snap["preamble"], PREAMBLE_KEYS),
            "rules": {name: {"head": join(rule["head"], BLOCK_KEYS), "examples": {title: join(example, BLOCK_KEYS) for title, example in rule["examples"].items()}}
                      for name, rule in snap["rules"].items()}}


def unpack(packed: dict) -> dict:
    def split(text: str, keys: tuple[str, ...]) -> dict:
        return dict(zip(keys, text.split("|")))
    return {"preamble": split(packed["preamble"], PREAMBLE_KEYS),
            "rules": {name: {"head": split(rule["head"], BLOCK_KEYS), "examples": {title: split(value, BLOCK_KEYS) for title, value in rule["examples"].items()}}
                      for name, rule in packed["rules"].items()}}


def snapshot(state: dict) -> dict:
    """可存進紀錄、可與基準比較的摘要：Feature 標頭、Background 與每條 Rule 的標頭和每個 Example。"""
    header, background = state["header"], state["background"]
    return {
        "preamble": {"header": digest(header["core"]), "core": digest(background["core"]),
                     "defaults": digest(header["defaults"] + background["defaults"]), "other": digest(header["other"] + background["other"])},
        "rules": {name: {"head": hashes(rule["head"]), "examples": {title: hashes(example) for title, example in rule["examples"].items()}}
                  for name, rule in state["rules"].items()},
    }


def rule_class(before: dict, after: dict) -> tuple[str, list[str]]:
    """一條 Rule 相對於參考點的改動：modified（內容改了或多了 Example）、defaults（只改了預設值註解）、examples_removed（只刪除了 Example）、comment（只改了其他註解）或 same。"""
    old, new = before["examples"], after["examples"]
    removed = [title for title in old if title not in new]
    common = [title for title in new if title in old]
    if before["head"]["core"] != after["head"]["core"] or any(title not in old for title in new) or any(old[t]["core"] != new[t]["core"] for t in common):
        return "modified", removed
    if before["head"]["defaults"] != after["head"]["defaults"] or any(old[t]["defaults"] != new[t]["defaults"] for t in common):
        return "defaults", removed
    if removed:
        return "examples_removed", removed
    if before["head"]["other"] != after["head"]["other"] or any(old[t]["other"] != new[t]["other"] for t in common):
        return "comment", removed
    return "same", removed


# ---------- dsl.md 與用語表 ----------

def dsl_patterns(text: str) -> dict[str, str]:
    """dsl.md 每個句型列：句型 → 該列內容的摘要。"""
    patterns: dict[str, str] = {}
    for line in text.splitlines():
        if line.startswith("| `"):
            matched = re.search(r"`([^`]+)`", split_cells(line)[0])
            if matched:
                patterns.setdefault(compact(matched.group(1)), digest([compact(line)]))
    return patterns


def value_units(text: str, glossary: bool) -> dict[str, dict[str, str]]:
    """參數合法值的小節：小節標題 → {值：該列內容的摘要}。用語表取「參數合法值」底下的每個小節，dsl.md 取「### `{參數}`」小節。"""
    units: dict[str, dict[str, str]] = {}
    section, current, header_seen = None, None, False
    for line in text.splitlines():
        if line.startswith("## "):
            section, current = line[3:].strip(), None
            continue
        if line.startswith("### "):
            wanted = section == VALUES_SECTION if glossary else bool(DSL_VALUE_HEADING_PATTERN.match(line))
            current = compact(line[4:]) if wanted else None
            header_seen = False
            if current:
                units.setdefault(current, {})
            continue
        if current is None or not line.startswith("|"):
            continue
        cells = split_cells(line)
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        if not header_seen:
            header_seen = True
            continue
        units[current].setdefault(cells[0].strip("`"), digest([compact(line)]))
    return units


def pattern_regex(pattern: str, cache: dict) -> re.Pattern:
    if pattern not in cache:
        out, position = "", 0
        for matched in PARAMETER_PATTERN.finditer(pattern):
            out += re.escape(pattern[position:matched.start()]) + r'(?:"[^"]*"|<[^<>]+>|[^\s"]+)'
            position = matched.end()
        cache[pattern] = re.compile("^" + out + re.escape(pattern[position:]) + "$")
    return cache[pattern]


def truth_state(truth_features: Path) -> dict:
    features = {f"{path.parent.name}/{path.name}": feature_state(path.read_text(encoding="utf-8"))
                for path in sorted(truth_features.glob("*/*.feature"))}
    patterns, values = {}, {}
    for folder in sorted(path for path in truth_features.iterdir() if path.is_dir() and not path.name.startswith(".")):
        dsl = folder / "dsl.md"
        if dsl.is_file():
            text = dsl.read_text(encoding="utf-8")
            patterns[folder.name] = dsl_patterns(text)
            values[f"{folder.name}/dsl.md"] = value_units(text, glossary=False)
    glossary = truth_features / GLOSSARY
    if glossary.is_file():
        values[GLOSSARY] = value_units(glossary.read_text(encoding="utf-8"), glossary=True)
    return {"features": features, "patterns": patterns, "values": values}


def base_state(context: dict, current: dict) -> dict:
    """基準 commit 時的摘要：基準以來沒有異動的檔案沿用目前的內容。"""
    changes = context["changes"]

    def base_text(rel: str) -> str | None:
        status = changes.get(rel)
        if status is None:
            return None
        if status == "ADD":
            return ""
        return truth_changes.git(context["root"], "show", f"{context['base']}:{context['truth_rel']}/{rel}")

    features = {}
    for key, state in current["features"].items():
        text = base_text(f"{FEATURES_DIR}/{key}")
        features[key] = snapshot(state) if text is None else (snapshot(feature_state(text)) if text else None)
    patterns, values = {}, {}
    for endpoint, rows in current["patterns"].items():
        text = base_text(f"{FEATURES_DIR}/{endpoint}/dsl.md")
        patterns[endpoint] = rows if text is None else dsl_patterns(text)
    for name, units in current["values"].items():
        text = base_text(f"{FEATURES_DIR}/{name}")
        values[name] = units if text is None else value_units(text, glossary=name == GLOSSARY)
    return {"features": features, "patterns": patterns, "values": values}


# ---------- dsl-refine 在 truth-changes.md 的標註 ----------

def summary_class(summary: str) -> str | None:
    text = summary.replace("`", "").strip()
    if text.startswith(DOC_ONLY):
        return DOC_ONLY
    if text.startswith(REWRITE):
        return REWRITE
    return None


def row_target(row: dict) -> str:
    return compact(row["target"].replace("`", ""))


def find_row(rows: list[dict], file: str, markers: list[str], bare: bool = True) -> dict | None:
    """記錄這個檔案、對象含任一標記的列；都沒有時取對象只寫到檔案（沒有「＞」）的列。"""
    candidates = [row for row in rows if file in row["files"]]
    for marker in markers:
        for row in candidates:
            if plain(marker) in plain(row["target"]):
                return row
    if bare:
        for row in candidates:
            if "＞" not in row["target"]:
                return row
    return None


# ---------- 一份 feature 相對於參考點的工作 ----------

def feature_work(key: str, state: dict, reference: dict | None, changed_patterns: dict, changed_values: list[dict], rows: list[dict], cache: dict,
                 renames: dict[str, str] | None = None) -> dict:
    """回傳 classes（每條 Rule 的改動）、deleted、removed_examples、renamed（改名的 Rule → 參考點的名稱）、work（要紅燈、綠燈、重構的 Rule → 理由）、
    rerun（只要重新執行的 Rule → 改動說明）與 rows（[重跑] 引用的 truth-changes.md 對象）。renames 是這份 feature 的改名紀錄（舊名稱 → 新名稱）。"""
    names = list(state["rules"])
    result = {"status": "ADD" if reference is None else "MOD", "classes": {}, "deleted": [], "removed_examples": {}, "renamed": {},
              "work": {}, "rerun": {}, "rows": {}}
    work, rerun, cited = result["work"], result["rerun"], result["rows"]

    def add(target: dict, name: str, reason: str) -> None:
        if reason not in target.setdefault(name, []):
            target[name].append(reason)

    def cite(name: str, row: dict | None) -> None:
        if row is not None:
            cited.setdefault(name, set()).add(row_target(row))

    file = f"{FEATURES_DIR}/{key}"
    if reference is None:
        for name in names:
            result["classes"][name] = "added"
            add(work, name, "新增")
        return result
    current = snapshot(state)
    previous = {new: old for old, new in (renames or {}).items()
                if old in reference["rules"] and old not in state["rules"] and new in state["rules"] and new not in reference["rules"]}
    result["renamed"] = dict(previous)
    before, after = reference["preamble"], current["preamble"]
    if before["core"] != after["core"] or before["defaults"] != after["defaults"]:
        label = "Background" if before["core"] != after["core"] else "預設值"
        row = find_row(rows, file, ["Background", "預設值", "Feature"])
        if row is not None and summary_class(row["summary"]) == DOC_ONLY:
            for name in names:
                add(rerun, name, f"{label} 只改說明" if label == "Background" else "預設值只改說明")
                cite(name, row)
        else:
            for name in names:
                add(work, name, label)
    elif before["header"] != after["header"] or before["other"] != after["other"]:
        row = find_row(rows, file, ["Feature"])
        for name in names:
            add(rerun, name, "Feature 標頭只改說明" if before["header"] != after["header"] else "只改了註解")
            cite(name, row)
    for name in names:
        before_name = previous.get(name, name)
        if before_name not in reference["rules"]:
            result["classes"][name] = "added"
            add(work, name, "新增")
            continue
        kind, removed = rule_class(reference["rules"][before_name], current["rules"][name])
        if name in previous and kind == "same":
            kind = "renamed"
        result["classes"][name] = kind
        if removed:
            result["removed_examples"][name] = removed
        row = find_row(rows, file, [f"Rule「{name}」"])
        if kind == "modified":
            add(work, name, "修改")
        elif kind == "defaults":
            if row is not None and summary_class(row["summary"]) == DOC_ONLY:
                add(rerun, name, "預設值只改說明")
                cite(name, row)
            else:
                add(work, name, "預設值")
        elif kind == "examples_removed":
            for title in removed:
                add(rerun, name, f"只刪除了 Example「{title}」")
            cite(name, row)
        elif kind == "comment":
            add(rerun, name, "只改了註解")
            cite(name, row)
        if name in previous and kind != "modified":
            add(rerun, name, f"Rule 改名（原為「{before_name}」）")
            cite(name, row)
    result["deleted"] = [name for name in reference["rules"] if name not in state["rules"] and name not in previous.values()]
    if changed_patterns:
        shared = state["background"]["steps"]
        for name, rule in state["rules"].items():
            steps = shared + rule["head"]["steps"] + [step for example in rule["examples"].values() for step in example["steps"]]
            for pattern, (status, kind, row) in changed_patterns.items():
                regex = pattern_regex(pattern, cache)
                if not any(regex.match(step) for step in steps):
                    continue
                if kind == DOC_ONLY:
                    kept = KEPT_PATTERN.search(row["target"]) if status == "DEL" and row else None
                    add(rerun, name, f"句型「{kept.group(1)}」只改說明（併入了「{pattern}」）" if kept else f"句型「{pattern}」只改說明")
                    cite(name, row)
                else:
                    add(work, name, f"句型「{pattern}」{'已刪除' if status == 'DEL' else '改了測試寫法'}")
    for change in changed_values:
        quoted, value = f'"{change["value"]}"', change["value"]
        for name, rule in state["rules"].items():
            lines = state["background"]["core"] + rule["head"]["core"] + [line for example in rule["examples"].values() for line in example["core"]]
            hit = any(quoted in line or (line.startswith("|") and any(value in cell.split("、") for cell in split_cells(line))) for line in lines)
            if not hit:
                continue
            if change["kind"] == DOC_ONLY:
                add(rerun, name, f"參數「{change['unit']}」只改說明")
                cite(name, change["row"])
            else:
                add(work, name, f"參數「{change['unit']}」的值「{value}」")
    for name, reasons in rerun.items():
        merged = {reason.split("（併入了")[0] for reason in reasons if "（併入了" in reason}
        rerun[name] = [reason for reason in reasons if reason not in merged]
    for name in list(rerun):
        if name in work:
            del rerun[name]
            cited.pop(name, None)
    return result


def changed_patterns_of(endpoint: str, reference: dict, current: dict, rows: list[dict]) -> dict:
    """這個端點相對於參考點修改或刪除的句型 → （MOD 或 DEL、只改說明或改測試寫法、標註的列）。"""
    before, after = reference["patterns"].get(endpoint, {}), current["patterns"].get(endpoint, {})
    file = f"{FEATURES_DIR}/{endpoint}/dsl.md"
    changed = {}
    for pattern, value in before.items():
        if after.get(pattern) == value:
            continue
        if pattern not in after:
            # dsl-refine 合併重複句型時，被併入的句型記 DEL（摘要「併入「X」」），保留的 X 記 MOD「只改說明：」：既有 step 不用改，只重新執行
            del_row = find_row(rows, file, [f"句型「{pattern}」"], bare=False)
            merged = MERGED_INTO.search(del_row["summary"]) if del_row else None
            kept_row = find_row(rows, file, [f"句型「{merged.group(1)}」"], bare=False) if merged and merged.group(1) in after else None
            if kept_row and summary_class(kept_row["summary"]) == DOC_ONLY:
                changed[pattern] = ("DEL", DOC_ONLY, kept_row)
            else:
                changed[pattern] = ("DEL", REWRITE, del_row)
            continue
        row = find_row(rows, file, [f"句型「{pattern}」"], bare=False)
        changed[pattern] = ("MOD", (summary_class(row["summary"]) if row else None) or REWRITE, row)
    return changed


def changed_values_of(endpoint: str, reference: dict, current: dict, rows: list[dict]) -> list[dict]:
    """這個端點適用的參數合法值（用語表與該端點的 dsl.md）中，參考點與目前都有、內容不同的值。"""
    changed = []
    for name in (GLOSSARY, f"{endpoint}/dsl.md"):
        before, after = reference["values"].get(name, {}), current["values"].get(name, {})
        for unit, old_values in before.items():
            for value, digest_value in old_values.items():
                if value in after.get(unit, {}) and after[unit][value] != digest_value:
                    unit_name = unit.replace("`", "")
                    row = find_row(rows, f"{FEATURES_DIR}/{name}", [unit_name, value])
                    kind = (summary_class(row["summary"]) if row else None) or REWRITE
                    changed.append({"source": name, "unit": unit_name, "value": value, "kind": kind, "row": row})
    return changed


# ---------- plan 的輸入 ----------

def table_rows(lines: list[str], heading: str) -> list[dict]:
    rows, header, inside = [], None, False
    for line in lines:
        if line.startswith("## "):
            inside = line[3:].strip() == heading
            header = None
            continue
        if not inside or not line.startswith("|"):
            continue
        cells = split_cells(line)
        if header is None:
            header = cells
        elif not all(set(cell) <= set("-: ") for cell in cells):
            rows.append(dict(zip(header, cells)))
    return rows


def read_acceptance(acceptance_dir: Path) -> dict[str, dict]:
    covers: dict[str, dict] = {}
    if not acceptance_dir.is_dir():
        return covers
    for path in sorted(acceptance_dir.glob("*.feature")):
        pending = None
        for raw in path.read_text(encoding="utf-8").splitlines():
            cover = COVER_PATTERN.match(raw)
            if cover:
                pending = cover.group(1)
                continue
            if keyword_of(raw, SCENARIO_KEYWORDS):
                ac = AC_ID_PATTERN.search(title_of(raw))
                if ac:
                    text = pending or ""
                    covers[ac.group(0)] = {"requirements": set(REQUIREMENT_ID_PATTERN.findall(text)), "stories": {int(n) for n in US_PATTERN.findall(text)}}
                pending = None
    return covers


def read_spec(spec_path: Path) -> tuple[dict[int, int], dict[str, int], list[str]]:
    """回傳故事優先順序、定義在故事底下的需求所屬故事，以及 spec.md 定義的全部 NFR。"""
    priorities: dict[int, int] = {}
    owner: dict[str, int] = {}
    nfrs: list[str] = []
    if not spec_path.is_file():
        return priorities, owner, nfrs
    story = None
    for line in spec_path.read_text(encoding="utf-8").splitlines():
        heading = STORY_HEADING_PATTERN.match(line)
        if heading:
            story = int(heading.group(1))
            priorities[story] = int(heading.group(2))
            continue
        if HEADING_PATTERN.match(line):
            story = None
            continue
        definition = DEFINITION_PATTERN.match(line)
        if definition:
            requirement = definition.group(1)
            if requirement.startswith("NFR-") and requirement not in nfrs:
                nfrs.append(requirement)
            if story is not None:
                owner[requirement] = story
    return priorities, owner, nfrs


def read_interfaces(plan_path: Path) -> dict[str, set[str]]:
    """回傳 plan.md「介面盤點」表每個介面 ID 的「依據需求」中的 NFR。"""
    interfaces: dict[str, set[str]] = {}
    if not plan_path.is_file():
        return interfaces
    inside, header = False, None
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            inside = line.lstrip("#").strip() == "介面盤點"
            header = None
            continue
        if not inside or not line.startswith("|"):
            continue
        cells = split_cells(line)
        if header is None:
            header = cells
            continue
        if all(set(cell) <= set("-: ") for cell in cells):
            continue
        row = dict(zip(header, cells))
        interface_id = row.get("介面 ID", "").strip("`")
        if interface_id:
            interfaces[interface_id] = set(NFR_ID_PATTERN.findall(row.get("依據需求", "")))
    return interfaces


def read_tech_items(path: Path) -> list[dict]:
    """技術項.md 的每一行「- 問題（發現的 skill；依據；修正：擁有者）」；問題取第一個括號之前的文字，舊格式沒有「修正：」時擁有者為 None。"""
    if not path.is_file():
        return []
    items = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        matched = TECH_ITEM_PATTERN.match(raw)
        if not matched:
            continue
        text = matched.group(1).strip()
        problem_text = re.split(r"[（(]", text, maxsplit=1)[0].strip() or text
        meta = text[len(problem_text):].strip()
        if meta[:1] in ("（", "(") and meta[-1:] in ("）", ")"):
            meta = meta[1:-1]
        parts = [part.strip() for part in re.split(r"[；;]", meta) if part.strip()] if meta else []
        fixer = FIX_OWNER_PATTERN.search(meta)
        items.append({"line": number, "text": text, "problem": problem_text, "finder": parts[0] if parts else None,
                      "basis": "；".join(part for part in parts[1:] if not FIX_OWNER_PATTERN.match(part)) or None,
                      "fix_owner": fixer.group(1) if fixer else None})
    return items


def read_kind(plan_dir: Path) -> str:
    try:
        data = json.loads((plan_dir / ".plan.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return REQUIREMENT_KIND
    return str(data.get("kind") or REQUIREMENT_KIND)


def load_record(path: Path) -> tuple[dict | None, str | None]:
    if not path.is_file():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return None, f"{path.name} 不是合法的 JSON（{error}），已開始的 feature 改以基準 commit 為參考點；拆解完成後以 --record 重新寫入。"
    if not isinstance(data, dict) or not isinstance(data.get("truth"), dict) or not isinstance(data.get("tasks"), dict):
        return None, f"{path.name} 缺少 truth 或 tasks，已開始的 feature 改以基準 commit 為參考點；拆解完成後以 --record 重新寫入。"
    try:
        data["truth"]["features"] = {key: unpack(value) for key, value in data["truth"].get("features", {}).items()}
    except (KeyError, AttributeError, TypeError):
        return None, f"{path.name} 的 truth.features 格式不符，已開始的 feature 改以基準 commit 為參考點；拆解完成後以 --record 重新寫入。"
    return data, None


def coverage_key(row: dict) -> str:
    return f"{row.get('端點', '')}/{row.get('feature', '').strip('`').split('/')[-1]}"


def rule_name(text: str) -> str:
    return compact(text.strip("`"))


def endpoint_rank(endpoint: str, order: list[str]) -> int:
    """組內預設順序：前端最後、後端在前端之前，其餘內層端點依用語表端點表順序排在後端之前。"""
    if endpoint == FRONTEND:
        return 10_000
    if endpoint == BACKEND:
        return 9_000
    return order.index(endpoint) if endpoint in order else 8_000


# ---------- tasks.md 的進度 ----------

def phase_kind(title: str) -> str:
    if title in FIXED_PHASES:
        return title
    if title.startswith(FIX_PREFIX) and FEATURE_KEY_PATTERN.match(title[len(FIX_PREFIX):]):
        return "修正"
    return "Feature" if FEATURE_KEY_PATTERN.match(title) else "other"


def read_task_state(path: Path, scope_root: str) -> dict:
    """tasks.md 的 Phase、任務、勾選與範疇；已勾選的任務必須是從 T001 起連續的一段，最後一個已勾選任務所在的 Phase 之前（含）為已開始的部分。"""
    state = {"exists": path.is_file(), "phases": [], "tasks": []}
    if not state["exists"]:
        return state
    phase = None
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        head = PHASE_PATTERN.match(raw)
        if head:
            title = head.group(2).strip()
            phase = {"number": int(head.group(1)), "title": title, "kind": phase_kind(title), "tasks": []}
            state["phases"].append(phase)
            continue
        task = TASK_PATTERN.match(raw)
        if not task or phase is None:
            continue
        body = task.group(3)
        stage = STAGE_PATTERN.search(body)
        scope = SCOPE_SPAN_PATTERN.search(body)
        entry = {"id": task.group(2), "checked": task.group(1) != " ", "stage": stage.group(1) if stage else None,
                 "scope": scope.group(1) if scope else None, "phase": phase["number"], "line": line_no, "hash": task_line_hash(raw)}
        entry.update(parse_scope(entry["scope"], scope_root))
        state["tasks"].append(entry)
        phase["tasks"].append(entry["id"])
    return state


def resolve_rules(task: dict, record: dict | None, current: dict) -> tuple[list[str], bool]:
    """任務範疇涵蓋的 Rule 名稱；整份 feature 或行號的範疇優先取紀錄中同一個範疇的解析結果，沒有時以目前的 feature 解析（第二個值為 False）。"""
    if task["names"] is not None:
        return list(task["names"]), True
    previous = (record or {}).get("tasks", {}).get(task["id"])
    if previous and previous.get("scope") == task["scope"] and isinstance(previous.get("rules"), list):
        return list(previous["rules"]), True
    state = current["features"].get(task["key"])
    if state is None:
        return [], False
    if task["lines"]:
        return [name for name, rule in state["rules"].items() if rule["line"] in task["lines"]], False
    return list(state["rules"]), False


def progress(task_state: dict, record: dict | None, current: dict, renames: dict[str, dict[str, str]] | None = None) -> dict:
    """已開始的部分、進行中的 Phase、[驗證] 的狀態，以及已開始的 feature 與它們實作過的 Rule；renames 是各 feature 的改名紀錄（舊名稱 → 新名稱）。"""
    renames = renames or {}
    tasks = task_state["tasks"]
    verify = next((task for task in tasks if task["stage"] == VERIFY), None)
    checked = [task for task in tasks if task["checked"] and task["stage"] != VERIFY]
    last = checked[-1] if checked else None
    phases = task_state["phases"]
    started = [phase["number"] for phase in phases if last and phase["number"] <= last["phase"] and phase["kind"] != "Verify"]
    in_progress, kept_rerun = None, {}
    if last:
        phase = next(phase for phase in phases if phase["number"] == last["phase"])
        unchecked = [task for task in tasks if task["phase"] == phase["number"] and not task["checked"]]
        if unchecked:
            missing, moved = [], []
            for task in unchecked:
                if task["key"] is None or task["stage"] not in STAGES + (RERUN,):
                    continue
                aliases = renames.get(task["key"], {})
                if task["stage"] == RERUN:
                    kept_rerun.setdefault(task["key"], set()).update(aliases.get(name, name) for name in resolve_rules(task, record, current)[0])
                state = current["features"].get(task["key"])
                if state is None:
                    missing.append({"task": task["id"], "rules": ["（整份 feature 已不存在）"]})
                elif task["names"]:
                    absent = [name for name in task["names"] if name not in state["rules"]]
                    gone = [name for name in absent if aliases.get(name) not in state["rules"]]
                    renamed = [{"from": name, "to": aliases[name]} for name in absent if aliases.get(name) in state["rules"]]
                    if gone:
                        missing.append({"task": task["id"], "rules": gone})
                    if renamed:
                        moved.append({"task": task["id"], "rules": renamed})
            in_progress = {"phase": phase["number"], "title": phase["title"], "unchecked": [task["id"] for task in unchecked],
                           "missing_rules": missing, "renamed_rules": moved}
    touched, touched_stage, implemented, unresolved = set(), set(), {}, []
    for task in checked:
        if task["key"] is None or task["stage"] not in STAGES + (RERUN,):
            continue
        touched.add(task["key"])
        if task["stage"] in STAGES:
            touched_stage.add(task["key"])
            names, resolved = resolve_rules(task, record, current)
            if not resolved:
                unresolved.append(task["id"])
            for name in names:
                implemented.setdefault(task["key"], {}).setdefault(name, []).append(task["id"])
    return {"checked": [task["id"] for task in checked], "last": last["id"] if last else None, "started": started, "in_progress": in_progress,
            "verify": {"id": verify["id"], "checked": verify["checked"]} if verify else None, "kept_rerun": kept_rerun,
            "touched": touched, "touched_stage": touched_stage, "implemented": implemented, "unresolved": unresolved}


def carried(record: dict | None, checked: set[str]) -> tuple[dict[str, set[str]], dict[str, dict[str, dict]]]:
    """上次拆解時還沒開始、到現在也還沒開始的 Phase 中，階段任務與 [重跑] 任務涵蓋的 Rule。"""
    work: dict[str, set[str]] = {}
    rerun: dict[str, dict[str, dict]] = {}
    if not record:
        return work, rerun
    for info in record.get("phases", {}).values():
        ids = info.get("tasks", [])
        if info.get("started") or any(task_id in checked for task_id in ids):
            continue
        for task_id in ids:
            entry = record["tasks"].get(task_id)
            if not entry or not entry.get("key"):
                continue
            if entry.get("stage") in STAGES:
                work.setdefault(entry["key"], set()).update(entry.get("rules", []))
            elif entry.get("stage") == RERUN:
                for name in entry.get("rules", []):
                    rerun.setdefault(entry["key"], {})[name] = {"changes": entry.get("rule_changes", {}).get(name, []), "rows": entry.get("rule_rows", {}).get(name, [])}
    return work, rerun


# ---------- 統計 ----------

def summarize(plan_dir: Path, interface_overrides: dict[str, list[str]] | None = None, verified_nfrs: list[str] | None = None) -> tuple[dict | None, list[dict]]:
    summary, problems, _ = analyze(plan_dir, interface_overrides, verified_nfrs)
    return summary, problems


def analyze(plan_dir: Path, interface_overrides: dict[str, list[str]] | None = None, verified_nfrs: list[str] | None = None) -> tuple[dict | None, list[dict], dict]:
    """verified_nfrs 是讀過涵蓋它的 Rule、確認每個條件都被驗證的 NFR；沒有帶入時一律視為未驗證。"""
    try:
        context = truth_changes.load_context(str(plan_dir))
    except truth_changes.Abort as error:
        return None, [problem("input", str(error))], {}
    if context["changes"] is None:
        return None, [problem("input", NOT_IN_PROGRESS.format(plan=context["plan"], status=context["status"] or "未知"))], {}
    plan_dir = plan_dir.resolve()
    kind = read_kind(plan_dir)
    technical = kind == TECH_FIX
    truth_features = context["truth_dir"] / FEATURES_DIR
    glossary = truth_features / GLOSSARY
    coverage = plan_dir / FEATURES_DIR / COVERAGE
    acceptance_dir = plan_dir / FEATURES_DIR / ACCEPTANCE_DIR
    spec = plan_dir / "spec.md"
    plan = plan_dir / "plan.md"
    if technical:
        missing = [path for path in (glossary, plan_dir / TECH_ITEMS) if not path.exists()]
        hint = "技術修正 plan 只需要 truth-changes.md、技術項.md 與 truth 的端點資料夾：技術項.md 由 plan-package 開立時建立、dev-finding 記錄，用語表與端點資料夾由 dsl-refine 產出"
    else:
        missing = [path for path in (glossary, coverage, acceptance_dir, spec, plan) if not path.exists()]
        hint = "truth 的 features/ 與用語表、plan 的涵蓋表由 dsl-refine 產出，acceptance 由 spec-by-example 產出，spec.md 由 specify 產出，plan.md 由 system-analysis 產出，請先執行它們"
    if missing:
        return None, [problem("input", f"找不到 {'、'.join(str(path) for path in missing)}；{hint}。")], {}
    problems: list[dict] = []
    warnings: list[str] = []
    scope_root = f"{context['truth_rel']}/{FEATURES_DIR}/"
    endpoint_rows = table_rows(glossary.read_text(encoding="utf-8").splitlines(), "端點")
    endpoint_order = [row.get("資料夾", "").strip("`") for row in endpoint_rows]
    prefix_folder = {row.get("介面前綴", "").strip("`"): row.get("資料夾", "").strip("`") for row in endpoint_rows}
    for name in endpoint_order:
        folder = truth_features / name
        if name and not any(folder.glob("*.feature")):
            problems.append(problem("input", f"用語表「端點」表登記了 {name}，但 specs/truth/features/{name}/ 不存在或沒有任何 feature，請回到 dsl-refine 補齊（沒有該端點的案例時應從端點表移除）。"))
        elif name and not (folder / "dsl.md").is_file():
            problems.append(problem("input", f"端點資料夾 {name} 沒有 dsl.md，請回到 dsl-refine 產出。"))
    interfaces = read_interfaces(plan)
    priorities, owner, all_nfrs = read_spec(spec)
    covers = read_acceptance(acceptance_dir)
    rows = [row for section in context["sections"] for row in section["rows"] if row["type"] in truth_changes.TYPES]
    feature_rows = [row for row in rows if any(file.startswith(FEATURES_DIR + "/") for file in row["files"])]
    renames = rename_map(feature_rows)
    current = truth_state(truth_features)
    base = base_state(context, current)
    record, record_issue = load_record(plan_dir / RECORD_NAME)
    if record_issue:
        warnings.append(record_issue)
    task_state = read_task_state(plan_dir / TASKS_NAME, scope_root)
    state = progress(task_state, record, current, renames)
    if state["unresolved"]:
        warnings.append(f"已勾選的 {'、'.join(state['unresolved'])} 以整份 feature 或行號為範疇，紀錄中沒有它們當時涵蓋的 Rule，已改以目前的 feature 解析；撤回的 Rule 可能找不齊。")
    cache: dict = {}

    # ---- 相對於基準 commit：涵蓋表、移除與 plan 的異動總覽 ----
    base_patterns = {endpoint: changed_patterns_of(endpoint, base, current, feature_rows) for endpoint in current["patterns"]}
    base_values = {endpoint: changed_values_of(endpoint, base, current, feature_rows) for endpoint in current["patterns"]}
    base_view = {}
    for key, feature in current["features"].items():
        endpoint = key.split("/")[0]
        base_view[key] = feature_work(key, feature, base["features"].get(key), base_patterns.get(endpoint, {}), base_values.get(endpoint, []), feature_rows, cache,
                                      renames.get(key))
    removed = sorted(file[len(FEATURES_DIR) + 1:] for file, status in context["changes"].items()
                     if status == "DEL" and file.startswith(FEATURES_DIR + "/") and file.endswith(".feature") and file.count("/") == 2)

    # ---- 涵蓋表 ----
    registered: set[tuple[str, str]] = set()
    candidates: dict[str, list[dict]] = {}
    coverage_rows: list[dict] = []
    if not technical:
        coverage_lines = coverage.read_text(encoding="utf-8").splitlines()
        for heading, label_column in (("AC 涵蓋表", "AC"), ("補充案例", "來源需求")):
            for row in table_rows(coverage_lines, heading):
                key, rule, change = coverage_key(row), rule_name(row.get("Rule", "")), row.get("異動", "").strip("`")
                label = row.get(label_column, "")
                feature = current["features"].get(key)
                if feature is None or rule not in feature["rules"]:
                    problems.append(problem("coverage", f"涵蓋表「{heading}」的 {label}「{rule}」在 specs/truth/features/{key} 找不到同名 Rule，請回到 dsl-refine 修正涵蓋表或 feature。"))
                    continue
                if heading == "AC 涵蓋表":
                    ac = AC_ID_PATTERN.search(label)
                    if ac and ac.group(0) not in covers:
                        problems.append(problem("coverage", f"涵蓋表 AC 涵蓋表的 {ac.group(0)} 在 plan 的 features/acceptance/ 找不到附「# 涵蓋：」或「# 開發發現：」註解的 Example，請回到 spec-by-example 補齊。"))
                    sources = covers.get(ac.group(0), {}).get("requirements", set()) if ac else set()
                    stories = covers.get(ac.group(0), {}).get("stories", set()) if ac else set()
                    ac_id = ac.group(0) if ac else None
                else:
                    ac_id = None
                    sources = set(REQUIREMENT_ID_PATTERN.findall(label))
                    stories = {owner[source] for source in sources if source in owner}
                for nfr in sorted({nfr for source in sources for nfr in NFR_ID_PATTERN.findall(source)}, key=nfr_number):
                    candidates.setdefault(nfr, []).append({"key": key, "rule": rule, "via": ac_id or "補充案例"})
                view = base_view[key]
                required = {name for name, kind_of in view["classes"].items() if kind_of in ("added", "modified")}
                touched_rules = {name for name, kind_of in view["classes"].items() if kind_of != "same"} | set(view["work"]) | set(view["rerun"])
                if change in WORK_CHANGES:
                    if rule not in touched_rules:
                        problems.append(problem("coverage", f"涵蓋表「{heading}」把 {key} 的「{rule}」標為 {change}，但基準以來這條 Rule 沒有新增或修改，請回到 dsl-refine 修正「異動」欄或 feature。"))
                        continue
                    registered.add((key, rule))
                    coverage_rows.append({"key": key, "rule": rule, "ac": ac_id, "sources": sources, "stories": stories})
                elif rule in required:
                    problems.append(problem("coverage", f"涵蓋表「{heading}」把 {key} 的「{rule}」標為「{change}」，但基準以來這條 Rule 有新增或修改，請回到 dsl-refine 把「異動」欄改為 ADD 或 MOD。"))
        for key, view in base_view.items():
            for name, kind_of in view["classes"].items():
                if kind_of in ("added", "modified") and (key, name) not in registered:
                    line = current["features"][key]["rules"][name]["line"]
                    problems.append(problem("coverage", f"{key}:{line} 的 Rule「{name}」這次有新增或修改，卻沒有以 ADD 或 MOD 登記在涵蓋表的 AC 涵蓋表或補充案例，請回到 dsl-refine 補登。"))
    for nfr in sorted(set(verified_nfrs or []), key=lambda n: (not NFR_ID_PATTERN.fullmatch(n), n)):
        if nfr not in all_nfrs:
            problems.append(problem("nfr", f"--verified-nfr 指定的 {nfr} 不是 spec.md 定義的 NFR，請改為 NFR-xxx 的編號。"))
        elif nfr not in candidates:
            problems.append(problem("nfr", f"--verified-nfr 指定的 {nfr} 在涵蓋表沒有任何 Rule 涵蓋它，不能視為已驗證；請拿掉它，或回到 dsl-refine 補上驗證它的 Rule。"))
    verified = sorted(set(verified_nfrs or []) & set(candidates) & set(all_nfrs), key=nfr_number)
    overrides = interface_overrides or {}

    def requirement_info(key: str, names: set[str]) -> dict:
        chosen = [row for row in coverage_rows if row["key"] == key and row["rule"] in names]
        stories = {story for row in chosen for story in row["stories"]}
        story = min(stories, key=lambda s: (priorities.get(s, 99), s)) if stories else None
        return {"acceptance": sorted({row["ac"] for row in chosen if row["ac"]}, key=ac_number),
                "requirements": sorted({source for row in chosen for source in row["sources"]}),
                "story": story, "story_priority": priorities.get(story) if story is not None else None}

    def interface_info(key: str) -> dict:
        endpoint = key.split("/")[0]
        endpoint_interfaces = sorted(interface_id for interface_id in interfaces if prefix_folder.get(interface_id.split("-")[0]) == endpoint)
        chosen = overrides.get(key, endpoint_interfaces)
        reached = {nfr for interface_id in chosen for nfr in interfaces.get(interface_id, set())}
        return {"interfaces": list(chosen), "interfaces_source": "given" if key in overrides else "endpoint_default",
                "nfr_constraints": sorted(reached - set(verified), key=nfr_number), "_endpoint_interfaces": endpoint_interfaces}

    # ---- 這次異動的總覽（相對於基準 commit，供 analyze 與涵蓋檢查） ----
    features, skipped = [], []
    for key, view in base_view.items():
        feature = current["features"][key]
        names = [name for name, kind_of in view["classes"].items() if kind_of in ("added", "modified")]
        changed_file = f"{FEATURES_DIR}/{key}" in context["changes"]
        if not names:
            if changed_file:
                kinds = sorted({kind_of for kind_of in view["classes"].values() if kind_of != "same"})
                labels = {"defaults": "改了預設值", "examples_removed": "刪除了 Example", "comment": "改了註解", "renamed": "改了 Rule 名稱"}
                reason = "、".join([labels[k] for k in kinds if k in labels] + (["刪除了 Rule"] if view["deleted"] else [])) or "改了 Feature 標頭或 Background"
                skipped.append({"key": key, "reason": f"只{reason}，沒有新增或修改的 Rule"})
            continue
        ordered = list(feature["rules"])
        info = requirement_info(key, set(names))
        entry = {"key": key, "endpoint": key.split("/")[0], "file": key.split("/")[1], "status": view["status"],
                 "scope": scope_text(scope_root, key, names, ordered), "rule_count": len(names),
                 "example_count": sum(len(feature["rules"][name]["examples"]) for name in names), **info}
        entry.update({k: v for k, v in interface_info(key).items() if not k.startswith("_")})
        entry["rules"] = [{"line": feature["rules"][name]["line"], "name": name, "change": "ADD" if view["classes"][name] == "added" else "MOD"} for name in names]
        entry["deleted_rules"] = view["deleted"]
        features.append(entry)

    # ---- 要排的 Phase 與 [重跑]（已開始的 feature 以紀錄為參考點） ----
    checked = set(state["checked"])
    carry_work, carry_rerun = carried(record, checked)
    record_truth = record["truth"] if record else None
    record_patterns, record_values = {}, {}
    if record_truth:
        record_patterns = {endpoint: changed_patterns_of(endpoint, record_truth, current, feature_rows) for endpoint in current["patterns"]}
        record_values = {endpoint: changed_values_of(endpoint, record_truth, current, feature_rows) for endpoint in current["patterns"]}
    fallback = []
    phases, reruns = [], []
    renamed_seen = [{"key": key, "from": old, "to": new} for key, view in base_view.items() for new, old in view["renamed"].items()]
    for key, feature in current["features"].items():
        endpoint = key.split("/")[0]
        ordered = list(feature["rules"])
        aliases = renames.get(key, {})
        if key in state["touched"] and record_truth and key in record_truth.get("features", {}):
            view = feature_work(key, feature, record_truth["features"][key], record_patterns.get(endpoint, {}), record_values.get(endpoint, []), feature_rows, cache,
                                aliases)
            reference = "record"
            renamed_seen += [{"key": key, "from": old, "to": new} for new, old in view["renamed"].items()
                             if {"key": key, "from": old, "to": new} not in renamed_seen]
        else:
            view = base_view[key]
            reference = "base"
            if key in state["touched"]:
                fallback.append(key)
        work = {name: list(reasons) for name, reasons in view["work"].items()}
        rerun = {name: list(reasons) for name, reasons in view["rerun"].items()}
        cited = {name: set(targets) for name, targets in view["rows"].items()}
        if key in state["touched"]:
            for name in carry_work.get(key, set()):
                name = aliases.get(name, name)
                if name in feature["rules"]:
                    work.setdefault(name, ["上次拆解後尚未開始"])
            for name, info in carry_rerun.get(key, {}).items():
                name = aliases.get(name, name)
                if name in feature["rules"] and name not in work:
                    for change in info["changes"] or ["上次拆解後尚未開始"]:
                        if change not in rerun.setdefault(name, []):
                            rerun[name].append(change)
                    cited.setdefault(name, set()).update(info["rows"])
        for name in list(rerun):
            if name in work or name in state["kept_rerun"].get(key, set()):
                del rerun[name]
        if work:
            names = [name for name in ordered if name in work]
            info = requirement_info(key, set(names))
            title = f"{FIX_PREFIX}{key}" if technical or key in state["touched_stage"] else key
            entry = {"phase": title, "kind": "修正" if title.startswith(FIX_PREFIX) else "Feature", "key": key, "endpoint": endpoint, "file": key.split("/")[1],
                     "status": base_view[key]["status"], "reference": reference, "scope": scope_text(scope_root, key, names, ordered),
                     "rule_count": len(names), "example_count": sum(len(feature["rules"][name]["examples"]) for name in names), **info}
            entry.update({k: v for k, v in interface_info(key).items() if not k.startswith("_")})
            entry["rules"] = [{"line": feature["rules"][name]["line"], "name": name,
                               "change": {"added": "ADD", "modified": "MOD"}.get(base_view[key]["classes"].get(name, ""), "受影響"),
                               "reasons": work[name]} for name in names]
            phases.append(entry)
        if rerun:
            names = [name for name in ordered if name in rerun]
            changes = []
            for name in names:
                changes += [change for change in rerun[name] if change not in changes]
            reruns.append({"key": key, "endpoint": endpoint, "file": key.split("/")[1], "reference": reference,
                           "scope": scope_text(scope_root, key, names, ordered), "rule_count": len(names),
                           "example_count": sum(len(feature["rules"][name]["examples"]) for name in names),
                           "changes": changes, "rows": sorted({target for name in names for target in cited.get(name, set())}),
                           "rules": [{"line": feature["rules"][name]["line"], "name": name, "changes": rerun[name],
                                      "rows": sorted(cited.get(name, set()))} for name in names]})
    if fallback:
        warnings.append(f"沒有 {RECORD_NAME} 記下的狀態，已開始的 {'、'.join(fallback)} 改以基準 commit 為參考點，修正 Phase 可能包含已完成的 Rule。")
    for key in overrides:
        if key not in {entry["key"] for entry in phases} | {entry["key"] for entry in features}:
            problems.append(problem("interfaces", f"--interfaces 指定的 {key} 不是這次要排 Phase 的端點 feature，請寫成 `<端點資料夾>/<檔名>.feature=介面ID,介面ID`。"))
    for key in {entry["key"] for entry in phases} | {entry["key"] for entry in features}:
        info = interface_info(key)
        for interface_id in overrides.get(key, []):
            if interface_id not in info["_endpoint_interfaces"]:
                problems.append(problem("interfaces", f"--interfaces 指定 {key} 走到 {interface_id}，但它不是 plan.md 介面盤點中 {key.split('/')[0]} 端點的介面（{'、'.join(info['_endpoint_interfaces']) or '無'}）。"))

    # ---- Phase 順序：同名 feature 成組 ----
    groups: dict[str, dict] = {}
    for entry in phases:
        group = groups.setdefault(entry["file"], {"file": entry["file"], "story_priority": None, "story": None, "min_ac": None, "phases": []})
        group["phases"].append(entry)
        if entry["story_priority"] is not None and (group["story_priority"] is None or (entry["story_priority"], entry["story"]) < (group["story_priority"], group["story"])):
            group["story_priority"], group["story"] = entry["story_priority"], entry["story"]
        for ac in entry["acceptance"]:
            if group["min_ac"] is None or ac_number(ac) < ac_number(group["min_ac"]):
                group["min_ac"] = ac
    ordered_groups = sorted(groups.values(), key=lambda g: (g["story_priority"] is None, g["story_priority"] or 0, ac_number(g["min_ac"]) if g["min_ac"] else 10**9, g["file"]))
    phase_order = []
    for group in ordered_groups:
        group["phases"].sort(key=lambda entry: endpoint_rank(entry["endpoint"], endpoint_order))
        group["endpoints"] = [entry["endpoint"] for entry in group["phases"]]
        phase_order.extend(entry["phase"] for entry in group["phases"])
    reruns.sort(key=lambda entry: (endpoint_rank(entry["endpoint"], endpoint_order), entry["file"]))

    # ---- 移除：DEL 列、只刪除 Example 的 Rule、撤回的 Rule ----
    deletions = [{"owner": section["owner"], "type": "DEL", "target": row["target"], "summary": row["summary"], "reason": row["reason"], "line": row["line"]}
                 for section in context["sections"] for row in section["rows"] if row["type"] == "DEL"]
    seen_rows = set()
    for key, view in base_view.items():
        for name, titles in view["removed_examples"].items():
            if view["classes"].get(name) in ("added", "modified"):
                continue
            row = find_row(feature_rows, f"{FEATURES_DIR}/{key}", [f"Rule「{name}」"])
            if row is None:
                problems.append(problem("coverage", f"{key} 的 Rule「{name}」刪除了 Example（{'、'.join(titles)}），但 truth-changes.md 沒有 dsl-refine 記錄這個 feature 的列，請回到 dsl-refine 以 truth-changes 補記。"))
                continue
            if row["line"] in seen_rows:
                next(item for item in deletions if item["line"] == row["line"])["examples"] += [f"Rule「{name}」＞ Example「{title}」" for title in titles]
                continue
            seen_rows.add(row["line"])
            owner_name = next(section["owner"] for section in context["sections"] if row in section["rows"])
            deletions.append({"owner": owner_name, "type": row["type"], "target": row["target"], "summary": row["summary"], "reason": row["reason"],
                              "line": row["line"], "examples": [f"Rule「{name}」＞ Example「{title}」" for title in titles]})
    del_targets = [plain(row["target"]) for row in rows if row["type"] == "DEL"]
    withdrawn = []
    for key, implemented in sorted(state["implemented"].items()):
        feature = current["features"].get(key)
        file_target = plain(f"{FEATURES_DIR}/{key}")
        for name, ids in implemented.items():
            if feature is not None and (name in feature["rules"] or renames.get(key, {}).get(name) in feature["rules"]):
                continue
            rule_target = plain(f"{FEATURES_DIR}/{key}{RULE_SEPARATOR}Rule「{name}」")
            if any(target == file_target or rule_target in target for target in del_targets):
                continue
            withdrawn.append({"key": key, "rule": name, "target": f"{FEATURES_DIR}/{key}{RULE_SEPARATOR}Rule「{name}」", "tasks": ids})

    techstack_changes = [{"type": row["type"], "target": row["target"], "summary": row["summary"]}
                         for section in context["sections"] if TECHSTACK in section["paths"]
                         for row in section["rows"] if row["type"] in truth_changes.TYPES]
    summary = {
        "plan": context["plan"],
        "kind": kind,
        "endpoint_order": endpoint_order,
        "tasks_state": {
            "exists": task_state["exists"], "mode": "增量" if state["checked"] else "完整", "task_count": len(task_state["tasks"]),
            "checked_count": len(state["checked"]), "last_checked": state["last"], "started_phases": state["started"],
            "in_progress": state["in_progress"], "verify": state["verify"],
            "record": {"exists": record is not None, "generated_at": record.get("generated_at") if record else None},
        },
        "phases": sorted(phases, key=lambda entry: phase_order.index(entry["phase"])),
        "groups": [{key: group[key] for key in ("file", "story", "story_priority", "min_ac", "endpoints")} for group in ordered_groups],
        "default_phase_order": phase_order,
        "reruns": reruns,
        "features": features,
        "skipped_features": skipped,
        "removed_features": removed,
        "deletions": deletions,
        "withdrawn": withdrawn,
        "renamed_rules": renamed_seen,
        "tech_items": read_tech_items(plan_dir / TECH_ITEMS),
        "techstack_changes": techstack_changes,
        "nfrs": all_nfrs,
        "nfr_candidates": [{"nfr": nfr, "rules": candidates[nfr]} for nfr in sorted(candidates, key=nfr_number)],
        "verified_nfrs": verified,
        "unverified_nfrs": [nfr for nfr in all_nfrs if nfr not in verified],
        "warnings": warnings,
    }
    return summary, problems, {"current": current, "task_state": task_state, "record": record, "scope_root": scope_root, "plan_dir": plan_dir}


def build_record(summary: dict, extra: dict) -> dict:
    """這次拆解的紀錄：truth 的逐 Example 狀態、每個 Phase 是否已開始，以及每個階段任務與 [重跑] 任務涵蓋的 Rule；已勾選的任務沿用上次記下的解析結果。"""
    current, task_state, previous = extra["current"], extra["task_state"], extra["record"] or {}
    checked = {task["id"] for task in task_state["tasks"] if task["checked"]}
    reruns = {entry["scope"]: entry for entry in summary["reruns"]}
    tasks = {}
    for task in task_state["tasks"]:
        if task["stage"] not in STAGES + (RERUN,) or task["key"] is None:
            continue
        before = previous.get("tasks", {}).get(task["id"])
        entry = {"stage": task["stage"], "checked": task["checked"], "phase": task["phase"], "key": task["key"], "scope": task["scope"], "hash": task["hash"]}
        if task["stage"] == RERUN and task["checked"]:
            tasks[task["id"]] = entry
            continue
        if task["checked"] and before and before.get("scope") == task["scope"] and isinstance(before.get("rules"), list):
            entry["rules"] = before["rules"]
            for field in ("rule_changes", "rule_rows"):
                if field in before:
                    entry[field] = before[field]
        else:
            entry["rules"], _ = resolve_rules({**task, "id": "（不沿用）"}, None, current)
            planned = reruns.get(task["scope"]) if task["stage"] == RERUN else None
            if planned:
                entry["rule_changes"] = {rule["name"]: rule["changes"] for rule in planned["rules"]}
                entry["rule_rows"] = {rule["name"]: rule["rows"] for rule in planned["rules"]}
        tasks[task["id"]] = entry
    phases = {str(phase["number"]): {"title": phase["title"], "started": any(task_id in checked for task_id in phase["tasks"]), "tasks": phase["tasks"]}
              for phase in task_state["phases"]}
    keys = {entry["key"] for entry in tasks.values()}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "truth": {"features": {key: pack(snapshot(state)) for key, state in current["features"].items() if key in keys},
                  "patterns": current["patterns"], "values": current["values"]},
        "phases": phases,
        "tasks": tasks,
        "lines": {task["id"]: task["hash"] for task in task_state["tasks"]},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="統計進行中的 plan 要排的 Feature Phase、修正 Phase 與 [重跑] 任務的範疇、Rule 數、Example 數、驗收 AC、需求聯集與最高優先故事，列出預設的 Phase 順序、tasks.md 的進度、"
                                                 "被刪除的 feature、truth-changes.md 的每一列 DEL、只刪除了 Example 的 Rule、撤回的 Rule、技術項與沒有被任何 Rule 驗證的 NFR；--record 寫入這次拆解的紀錄。")
    parser.add_argument("plan_dir", help="plan 資料夾（含 truth-changes.md；需求 plan 另含 spec.md、plan.md 與 features/），例如 specs/plans/004-ranking")
    parser.add_argument("--brief", action="store_true", help="省略每個 Phase、[重跑] 與 feature 的 Rule 清單，只輸出計數與排序所需欄位")
    parser.add_argument("--interfaces", action="append", default=[], metavar="端點資料夾/檔名.feature=介面ID,介面ID",
                        help="該 feature 經 dsl.md 技術對應走到的介面 ID；可重複。未指定的 feature 預設為該端點在 plan.md 介面盤點的全部介面")
    parser.add_argument("--verified-nfr", action="append", default=[], metavar="NFR-xxx,NFR-yyy",
                        help="讀過 nfr_candidates 列出的 Rule、確認每個條件都被驗證的 NFR；可重複或以逗號分隔。未指定的 NFR 一律視為未驗證（列入 NFR 約束與 NFR 重構）")
    parser.add_argument("--record", action="store_true",
                        help=f"tasks.md 拆解並檢查完成後使用：把 truth 的逐 Example 狀態與每個任務涵蓋的 Rule 寫入 plan 資料夾的 {RECORD_NAME}，作為下次拆解的參考點；有問題時不寫入")
    return parser.parse_args()


def parse_interface_overrides(values: list[str]) -> dict[str, list[str]]:
    overrides: dict[str, list[str]] = {}
    for value in values:
        key, _, ids = value.partition("=")
        overrides[key.strip()] = [item.strip() for item in re.split(r"[,、]", ids) if item.strip()]
    return overrides


def parse_id_list(values: list[str]) -> list[str]:
    return [item.strip() for value in values for item in re.split(r"[,、\s]+", value) if item.strip()]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    plan_dir = Path(args.plan_dir)
    if not plan_dir.is_dir():
        print(f"錯誤：找不到 plan 資料夾 {plan_dir}，請傳入 plan 的路徑，例如 specs/plans/004-ranking。", file=sys.stderr)
        return 1
    summary, problems, extra = analyze(plan_dir, parse_interface_overrides(args.interfaces), parse_id_list(args.verified_nfr))
    if summary is None:
        print(json.dumps({"problems": problems}, ensure_ascii=False, indent=2))
        return 1
    for warning in summary["warnings"]:
        print(f"警告：{warning}", file=sys.stderr)
    if args.record:
        if problems:
            print(json.dumps({"problems": problems}, ensure_ascii=False, indent=2))
            print(f"錯誤：還有 {len(problems)} 個問題，沒有寫入 {RECORD_NAME}；請先依回報修正輸入或 tasks.md，再以 --record 寫入。", file=sys.stderr)
            return 1
        if not extra["task_state"]["exists"]:
            print(f"錯誤：{extra['plan_dir'] / TASKS_NAME} 不存在，沒有任務可以記錄；請先撰寫 tasks.md 並通過 check_tasks.py，再以 --record 寫入。", file=sys.stderr)
            return 1
        record = build_record(summary, extra)
        path = extra["plan_dir"] / RECORD_NAME
        path.write_text(json.dumps(record, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"已寫入 {len(record['truth']['features'])} 份 feature 的逐 Example 狀態與 {len(record['tasks'])} 個任務的範疇", file=sys.stderr)
        print(json.dumps({"record": path.as_posix(), "features": len(record["truth"]["features"]), "tasks": len(record["tasks"])}, ensure_ascii=False, indent=2))
        return 0
    if args.brief:
        for entry in summary["phases"] + summary["reruns"] + summary["features"]:
            entry.pop("rules", None)
    print(json.dumps({**summary, "problems": problems}, ensure_ascii=False, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
