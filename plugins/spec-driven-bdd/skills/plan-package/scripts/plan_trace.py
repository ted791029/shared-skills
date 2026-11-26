# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""串接器：依相依表（同目錄的 dependencies.json）以內容計算每個擁有者輸入的摘要（以節為單位）。
record 在擁有者跑完、結果是「改了」或「不用改」時把它目前的輸入摘要寫入 plan 的 .plan-trace.json；
status 列出待補跑的擁有者、順序與變了的輸入單位（本 plan 沒有紀錄的擁有者以基準 commit 時的輸入比較）；
deps 輸出相依表（產物的節、寫入者、事實的家與直接依據它的擁有者）。"""

import argparse
import datetime
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEPS_FILE = SCRIPT_DIR / "dependencies.json"
PLAN_FILE = ".plan.json"
TRACE_FILE = ".plan-trace.json"
LOCK_FILE = ".plan-trace.lock"
IN_PROGRESS = "進行中"
KIND_DEFAULT = "需求"
RESULTS = ("改了", "不用改")
SEP = "＞"
SAMPLE_LIMIT = 20

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")
TABLE_SEP = re.compile(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
ID_BULLET = re.compile(r"^(\s*)[-*]\s+\*\*((?:FR|NFR|SC)-\d+)\*\*")
HEADING_ID = re.compile(r"^((?:[A-Z]{1,5})-\d+)(?![\d])")
STORY = re.compile(r"^使用者故事\s*(\d+)")
WAVE = re.compile(r"^\*\*Wave\s+(\d+)")
INTERFACE_ID = re.compile(r"^([A-Z]{1,5})-\d+$")
REQUIREMENT_ID = re.compile(r"(?<![A-Za-z0-9])((?:FR|NFR|SC)-\d+)(?!\d)")
REQUIREMENT_RANGE = re.compile(r"(?<![A-Za-z0-9])(FR|NFR|SC)-(\d+)\s*[～~至]\s*(?:(?:FR|NFR|SC)-)?(\d+)")
AC_ID = re.compile(r"(?<![A-Za-z0-9])(AC-\d+)(?!\d)")
COVER_LINE = re.compile(r"^#\s*涵蓋\s*[：:](.*)$")
SECTION = re.compile(r"^##\s+(.+?)\s*[（(]\s*(.+?)\s*[）)]\s*$")
FIX_OWNER = re.compile(r"修正[：:]\s*([A-Za-z0-9-]+)")
TECH_ITEM_TAIL = re.compile(r"[（(][^（()）]*修正[：:][^（()）]*[）)]\s*$")
FEATURE_LINE = re.compile(r"^(?:Feature|功能)\s*[:：]\s*(.*)$")
BACKGROUND_LINE = re.compile(r"^(?:Background|背景)\s*[:：]")
RULE_LINE = re.compile(r"^(?:Rule|規則)\s*[:：]\s*(.*?)\s*$")
EXAMPLE_LINE = re.compile(r"^(?:Scenario Outline|Scenario Template|Example|Scenario|場景大綱|劇本大綱|例子|場景|劇本)\s*[:：]\s*(.*?)\s*$")
AC_TITLE = re.compile(r"^(AC-\d+)")
FINDING_TAG = "@開發發現"


class Abort(Exception):
    """無法繼續執行的環境或輸入錯誤。"""


# ---------- 文字與摘要 ----------

def normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def digest(text: str) -> str:
    return hashlib.sha256(normalize(text).encode("utf-8")).hexdigest()[:16]


def clean_title(title: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[*`]", "", title)).strip()


def clean_cell(cell: str) -> str:
    return re.sub(r"\s+", " ", cell.replace("`", "").replace("**", "")).strip()


def split_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|") and not text.endswith("\\|"):
        text = text[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", text)]


def heading_key(title: str) -> str:
    title = clean_title(title)
    story = STORY.match(title)
    if story:
        return f"使用者故事 {story.group(1)}"
    ident = HEADING_ID.match(title)
    if ident:
        return ident.group(1)
    if title.startswith("原始碼"):
        return "原始碼段"
    return title


def markdown_units(text: str) -> dict[str, str]:
    """把 Markdown 切成節：每個標題下的段落、每個表格列（以第一欄為鍵）、每條以 FR／NFR／SC 編號開頭的項目、plan.md 的每個 Wave。"""
    units: dict[str, list[str]] = {}
    seen: dict[str, int] = {}

    def add(key: str, line: str) -> None:
        units.setdefault(key, []).append(line)

    path: list[tuple[int, str]] = []
    base_key = "（開頭）"
    prose_key = base_key
    in_fence = False
    table_rows = 0
    bullet: tuple[str, int] | None = None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if in_fence:
            add(bullet[0] if bullet else prose_key, line)
            if FENCE.match(line):
                in_fence = False
            continue
        heading = HEADING.match(line)
        if heading:
            level = len(heading.group(1))
            path = [item for item in path if item[0] < level] + [(level, heading_key(heading.group(2)))]
            titles = [title for lvl, title in path if lvl >= 2]
            base_key = SEP.join(titles) if titles else "（開頭）"
            prose_key = base_key
            bullet = None
            table_rows = 0
            add(prose_key, line)
            continue
        if FENCE.match(line):
            in_fence = True
            add(bullet[0] if bullet else prose_key, line)
            continue
        if not stripped:
            table_rows = 0
            continue
        if stripped.startswith("|"):
            bullet = None
            table_rows += 1
            if table_rows == 1 or TABLE_SEP.match(stripped):
                add(prose_key, line)
                continue
            cells = split_row(stripped)
            first = clean_cell(cells[0]) if cells else ""
            key = f"{prose_key}{SEP}{first}"
            count = seen.get(key, 0) + 1
            seen[key] = count
            add(key if count == 1 else f"{key}#{count}", line)
            continue
        table_rows = 0
        wave = WAVE.match(stripped)
        if wave:
            bullet = None
            prose_key = f"{base_key}{SEP}Wave {wave.group(1)}"
            add(prose_key, line)
            continue
        if stripped.startswith("共盤點"):
            bullet = None
            add(f"{base_key}{SEP}統計", line)
            prose_key = base_key
            continue
        ident = ID_BULLET.match(line)
        if ident:
            bullet = (ident.group(2), len(ident.group(1)))
            add(bullet[0], line)
            continue
        if bullet and (len(line) - len(line.lstrip())) > bullet[1]:
            add(bullet[0], line)
            continue
        bullet = None
        add(prose_key, line)
    return {key: "\n".join(lines) for key, lines in units.items() if normalize("\n".join(lines))}


def gherkin_blocks(text: str) -> list[dict]:
    """把 feature 切成區塊：Feature 標頭、Background、Rule 標頭與 Example；區塊前的標籤與註解屬於該區塊，空白與縮排不算差異。"""
    blocks: list[dict] = []
    current = {"kind": "feature", "title": "", "rule": None, "lines": [], "tags": []}
    pending: list[str] = []
    rule = None
    for raw in text.splitlines():
        line = re.sub(r"\s+", " ", raw.strip())
        if not line:
            continue
        if line.startswith("@") or line.startswith("#"):
            pending.append(line)
            continue
        feature = FEATURE_LINE.match(line)
        if feature and current["kind"] == "feature":
            current["lines"] += pending + [line]
            current["title"] = feature.group(1)
            pending = []
            continue
        kind = title = None
        if BACKGROUND_LINE.match(line):
            kind, title = "background", "Background"
        else:
            matched = RULE_LINE.match(line)
            if matched:
                kind, title = "rule", matched.group(1)
                rule = title
            else:
                matched = EXAMPLE_LINE.match(line)
                if matched:
                    kind, title = "example", matched.group(1)
        if kind:
            blocks.append(current)
            tags = [token for item in pending if item.startswith("@") for token in item.split()]
            current = {"kind": kind, "title": title, "rule": rule, "lines": pending + [line], "tags": tags}
            pending = []
            continue
        current["lines"] += pending + [line]
        pending = []
    current["lines"] += pending
    blocks.append(current)
    return [block for block in blocks if block["lines"]]


def acceptance_units(text: str) -> dict[str, dict]:
    """驗收 feature：每個 AC、每個 Rule 標頭與 Background 各一個單位；回傳鍵 → {text, finding, ac}。"""
    units: dict[str, dict] = {}
    for block in gherkin_blocks(text):
        ac = AC_TITLE.match(block["title"] or "") if block["kind"] == "example" else None
        if block["kind"] == "feature":
            key = "Feature"
        elif block["kind"] == "background":
            key = f"Rule「{block['rule']}」{SEP}Background" if block["rule"] else "Background"
        elif block["kind"] == "rule":
            key = f"Rule「{block['title']}」"
        else:
            key = ac.group(1) if ac else f"Example「{block['title']}」"
        entry = units.setdefault(key, {"text": "", "finding": False, "ac": None})
        entry["text"] += "\n".join(block["lines"]) + "\n"
        if block["kind"] == "example":
            entry["ac"] = ac.group(1) if ac else None
            entry["finding"] = FINDING_TAG in block["tags"]
    return units


def feature_rule_units(text: str) -> dict[str, str]:
    """端點 feature：Feature 標頭、最上層的 Background 與每條 Rule（含它的 Background 與 Example）各一個單位。"""
    units: dict[str, list[str]] = {}
    for block in gherkin_blocks(text):
        if block["kind"] == "feature":
            key = "Feature"
        elif block["rule"] is None:
            key = "Background" if block["kind"] == "background" else "（無 Rule）"
        else:
            key = f"Rule「{block['rule']}」"
        units.setdefault(key, []).extend(block["lines"])
    return {key: "\n".join(lines) for key, lines in units.items()}


def truth_changes_sections(text: str) -> dict[str, str]:
    """truth-changes.md：每個 owner 一節，內容只取表格的資料列；只有表頭時視為不存在。"""
    sections: dict[str, list[str]] = {}
    owner = None
    rows = 0
    for raw in text.splitlines():
        line = raw.strip()
        if raw.startswith("## "):
            matched = SECTION.match(raw.strip())
            owner = matched.group(1).strip("` ") if matched else None
            rows = 0
            continue
        if owner is None or not line.startswith("|"):
            if not line.startswith("|"):
                rows = 0
            continue
        rows += 1
        if rows == 1 or TABLE_SEP.match(line):
            continue
        sections.setdefault(owner, []).append(re.sub(r"\s+", " ", line))
    return {owner: "\n".join(lines) for owner, lines in sections.items() if lines}


def tech_item_lines(text: str) -> list[dict]:
    """技術項.md：每一行一個技術項，取「修正：<擁有者>」為修正的擁有者。"""
    items = []
    for raw in text.splitlines():
        line = raw.strip()
        if not re.match(r"^[-*]\s+\S", line):
            continue
        body = re.sub(r"^[-*]\s+", "", line)
        tail = TECH_ITEM_TAIL.search(body)
        problem = (body[:tail.start()] if tail else re.split(r"[（(]", body, maxsplit=1)[0]).strip() or body
        fixer = FIX_OWNER.search(tail.group(0) if tail else body)
        items.append({"problem": problem, "text": body, "fix_owner": fixer.group(1) if fixer else None})
    return items


# ---------- 讀取某個時間點的檔案 ----------

def run_git(cwd: Path, *args: str, stdin: bytes | None = None) -> tuple[int, bytes, str]:
    try:
        result = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=cwd, input=stdin, capture_output=True)
    except FileNotFoundError:
        raise Abort("找不到 git 指令。基準 commit 時的輸入以 git 讀取，請先安裝 git。")
    return result.returncode, result.stdout, result.stderr.decode("utf-8", errors="replace").strip()


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


class WorkingSource:
    """目前工作區的 plan、truth 與憲法（專案根目錄的 .claude/constitution/）。"""

    def __init__(self, plan_dir: Path, truth_dir: Path):
        self.plan_dir, self.truth_dir = plan_dir, truth_dir
        self.constitution_dir = truth_dir.parent.parent / ".claude" / "constitution"
        self.ignore = load_ignore(truth_dir)
        self.cache: dict = {}

    def constitution_files(self) -> dict[str, str]:
        if not self.constitution_dir.is_dir():
            return {}
        return {path.relative_to(self.constitution_dir).as_posix(): path.read_text(encoding="utf-8", errors="replace")
                for path in sorted(self.constitution_dir.rglob("*")) if path.is_file()}

    def plan_text(self, rel: str) -> str | None:
        path = self.plan_dir / rel
        return path.read_text(encoding="utf-8") if path.is_file() else None

    def plan_files(self, folder: str, suffix: str = "") -> list[str]:
        base = self.plan_dir / folder
        if not base.is_dir():
            return []
        found = []
        for path in sorted(base.rglob("*")):
            rel = path.relative_to(self.plan_dir).as_posix()
            if path.is_file() and not any(part.startswith(".") for part in rel.split("/")) and rel.endswith(suffix):
                found.append(rel)
        return found

    def truth_text(self, rel: str) -> str | None:
        path = self.truth_dir / rel
        return path.read_text(encoding="utf-8", errors="replace") if path.is_file() and not is_ignored(rel, self.ignore) else None

    def truth_files(self, folder: str, suffix: str = "") -> list[str]:
        base = self.truth_dir / folder
        if not base.is_dir():
            return []
        found = []
        for path in sorted(base.rglob("*")):
            rel = path.relative_to(self.truth_dir).as_posix()
            if path.is_file() and rel.endswith(suffix) and not is_ignored(rel, self.ignore):
                found.append(rel)
        return found


class BaseSource:
    """基準 commit 時的狀態：plan 資料夾當時還不存在；truth 與憲法由 git 讀取。"""

    def __init__(self, root: Path, base: str, truth_rel: str, truth_dir: Path):
        self.ignore = load_ignore(truth_dir)
        self.cache: dict = {}
        self.files: dict[str, str] = {}
        self.constitution: dict[str, str] = {}
        if not base:
            return
        self.files = {rel: text for rel, text in self._load(root, base, truth_rel).items() if not is_ignored(rel, self.ignore)}
        self.constitution = self._load(root, base, "/".join(truth_rel.split("/")[:-2] + [".claude", "constitution"]))

    @staticmethod
    def _load(root: Path, base: str, git_rel: str) -> dict[str, str]:
        """讀取基準 commit 中 git_rel 底下的每個檔案，鍵為相對於 git_rel 的路徑。"""
        code, out, err = run_git(root, "ls-tree", "-r", "-z", base, "--", git_rel)
        if code != 0:
            raise Abort(f"無法讀取基準 commit {base[:12]} 的 {git_rel}：{err}。請確認 .plan.json 的 base 存在於這個倉庫。")
        entries = []
        for item in out.decode("utf-8", errors="replace").split("\0"):
            if "\t" not in item:
                continue
            meta, path = item.split("\t", 1)
            parts = meta.split()
            if len(parts) == 3 and parts[1] == "blob":
                entries.append((parts[2], path[len(git_rel) + 1:] if path.startswith(git_rel + "/") else path))
        if not entries:
            return {}
        code, out, err = run_git(root, "cat-file", "--batch", stdin="".join(f"{sha}\n" for sha, _ in entries).encode("utf-8"))
        if code != 0:
            raise Abort(f"無法讀取基準 commit 的檔案內容：{err}")
        files, offset = {}, 0
        for _, rel in entries:
            newline = out.index(b"\n", offset)
            header = out[offset:newline].decode("utf-8", errors="replace").split()
            size = int(header[2]) if len(header) >= 3 and header[1] != "missing" else 0
            files[rel] = out[newline + 1:newline + 1 + size].decode("utf-8", errors="replace")
            offset = newline + 1 + size + 1
        return files

    def constitution_files(self) -> dict[str, str]:
        return self.constitution

    def plan_text(self, rel: str) -> str | None:
        return None

    def plan_files(self, folder: str, suffix: str = "") -> list[str]:
        return []

    def truth_text(self, rel: str) -> str | None:
        return self.files.get(rel)

    def truth_files(self, folder: str, suffix: str = "") -> list[str]:
        prefix = folder.rstrip("/") + "/" if folder else ""
        return sorted(rel for rel in self.files if rel.startswith(prefix) and rel.endswith(suffix))


# ---------- 產物的節 ----------

def cached(source, name: str, build):
    if name not in source.cache:
        source.cache[name] = build()
    return source.cache[name]


def md_artifact(source, scope: str, rel: str) -> dict[str, str]:
    def build():
        text = source.plan_text(rel) if scope == "plan" else source.truth_text(rel)
        return {} if text is None else markdown_units(text)
    return cached(source, f"md:{scope}:{rel}", build)


def file_units(source, scope: str, folder: str, suffix: str = "") -> dict[str, str]:
    def build():
        files = source.plan_files(folder, suffix) if scope == "plan" else source.truth_files(folder, suffix)
        reader = source.plan_text if scope == "plan" else source.truth_text
        result = {}
        for rel in files:
            text = reader(rel)
            if text is not None:
                result[f"{scope}:{rel}"] = digest(text)
        return result
    return cached(source, f"files:{scope}:{folder}:{suffix}", build)


def keyed(scope: str, rel: str, units: dict[str, str], skip=lambda key: False) -> dict[str, str]:
    return {f"{scope}:{rel}{SEP}{key}": digest(text) for key, text in units.items() if not skip(key)}


def spec_units(source) -> dict[str, str]:
    units = md_artifact(source, "plan", "spec.md")
    return keyed("plan", "spec.md", units, skip=lambda key: key == "（開頭）" or key.split(SEP)[0] == "釐清紀錄")


def requirement_ids(text: str) -> list[str]:
    """取出 FR、NFR、SC 編號，「FR-002～FR-005」這類範圍展開成每個編號。"""
    found = set(REQUIREMENT_ID.findall(text))
    for matched in REQUIREMENT_RANGE.finditer(text):
        kind, start, end = matched.group(1), int(matched.group(2)), int(matched.group(3))
        if start <= end <= start + 200:
            found |= {f"{kind}-{number:0{len(matched.group(2))}d}" for number in range(start, end + 1)}
    return sorted(found)


def covered_requirements(text: str) -> list[str]:
    """驗收 AC 上方「# 涵蓋：」註解列出的 FR、NFR、SC 編號。"""
    found: list[str] = []
    for line in text.splitlines():
        matched = COVER_LINE.match(line.strip())
        if matched:
            found += requirement_ids(matched.group(1))
    return found


def plan_rows(source) -> list[dict]:
    """plan.md 介面盤點的每一列：介面 ID、前綴、列文字與引用的需求編號。"""
    def build():
        rows = []
        for key, text in md_artifact(source, "plan", "plan.md").items():
            parts = key.split(SEP)
            if len(parts) >= 2 and parts[-2] == "介面盤點":
                matched = INTERFACE_ID.match(parts[-1])
                if matched:
                    rows.append({"key": key, "id": parts[-1], "prefix": matched.group(1), "text": text,
                                 "requirements": requirement_ids(text)})
        return rows
    return cached(source, "plan_rows", build)


def acceptance_all(source) -> dict[str, dict]:
    def build():
        result = {}
        for rel in source.plan_files("features/acceptance", ".feature"):
            text = source.plan_text(rel)
            if text is None:
                continue
            for key, unit in acceptance_units(text).items():
                result[f"plan:{rel}{SEP}{key}"] = unit
        return result
    return cached(source, "acceptance", build)


# ---------- 選擇器：擁有者的輸入 ----------

def select(source, ctx: dict, owner: dict, expr: str) -> dict[str, str]:
    name, _, arg = expr.partition(":")
    if arg == "self":
        arg = owner["name"]
    if name == "spec.requirements":
        return spec_units(source)
    if name == "research":
        return keyed("plan", "research.md", md_artifact(source, "plan", "research.md"))
    if name == "techstack":
        return keyed("truth", "techstack.md", md_artifact(source, "truth", "techstack.md"))
    if name == "design":
        return keyed("truth", "ui/DESIGN.md", md_artifact(source, "truth", "ui/DESIGN.md"))
    if name == "product":
        return keyed("plan", "ui/PRODUCT.md", md_artifact(source, "plan", "ui/PRODUCT.md"))
    if name == "plan.all":
        return keyed("plan", "plan.md", md_artifact(source, "plan", "plan.md"), skip=lambda key: key == "（開頭）")
    if name == "plan.interfaces":
        return {f"plan:plan.md{SEP}{row['key']}": digest(row["text"]) for row in plan_rows(source)}
    if name == "plan.prefix":
        prefix = owner.get("prefix")
        result = {f"plan:plan.md{SEP}{row['key']}": digest(row["text"]) for row in plan_rows(source) if row["prefix"] == prefix}
        for key, text in md_artifact(source, "plan", "plan.md").items():
            last = key.split(SEP)[-1]
            if last.startswith("Wave ") and re.search(rf"(?<![A-Z]){re.escape(prefix)}-\d", text):
                result[f"plan:plan.md{SEP}{key}"] = digest(text)
            elif last == "分析 Wave":
                result[f"plan:plan.md{SEP}{key}"] = digest(text)
        return result
    if name == "spec.cited":
        cited = {item for row in plan_rows(source) if row["prefix"] == owner.get("prefix") for item in row["requirements"]}
        return {key: value for key, value in spec_units(source).items() if key.split(SEP)[-1] in cited}
    if name == "acceptance.cited":
        # 涵蓋註解引用了本端點介面列依據需求的 AC：只改 AC 時，Planner 也會判斷它的契約或 UI 契約是否與新的 AC 衝突
        cited = {item for row in plan_rows(source) if row["prefix"] == owner.get("prefix") for item in row["requirements"]}
        return {key: digest(unit["text"]) for key, unit in acceptance_all(source).items()
                if unit["ac"] and set(covered_requirements(unit["text"])) & cited}
    if name == "wave-report":
        return file_units(source, "plan", "", "wave-report.md") if source.plan_text("wave-report.md") is not None else {}
    if name == "ui-contract":
        return keyed("plan", "ui/ui-contract.md", md_artifact(source, "plan", "ui/ui-contract.md"))
    if name == "data-migration":
        text = source.plan_text("data-migration.md")
        return {} if text is None else {"plan:data-migration.md": digest(text)}
    if name == "contracts":
        return file_units(source, "truth", "contracts")
    if name == "data":
        return file_units(source, "truth", "data")
    if name == "coverage":
        return keyed("plan", "features/涵蓋表.md", md_artifact(source, "plan", "features/涵蓋表.md"))
    if name == "acceptance":
        return {key: digest(unit["text"]) for key, unit in acceptance_all(source).items()}
    if name == "truth-changes":
        text = source.plan_text("truth-changes.md")
        if text is None:
            return {}
        sections = truth_changes_sections(text)
        return {f"plan:truth-changes.md{SEP}{owner_name}": digest(rows) for owner_name, rows in sections.items()
                if arg == "*" or owner_name == arg or (arg.startswith("*") and owner_name.endswith(arg[1:]))}
    if name == "tech-items":
        text = source.plan_text("技術項.md")
        if text is None:
            return {}
        # 摘要只算問題與修正的擁有者：之後補充或改寫發現的 skill 與依據，不會讓已判斷過的擁有者再成為待補跑
        return {f"plan:技術項.md{SEP}{item['problem']}": digest(f"{item['problem']}\n{item['fix_owner'] or ''}") for item in tech_item_lines(text)
                if arg == "*" or item["fix_owner"] == arg}
    if name == "findings-cited":
        cited = set()
        text = source.plan_text("truth-changes.md")
        if text is not None:
            cited |= set(AC_ID.findall(truth_changes_sections(text).get(owner["name"], "")))
        for output in owner.get("outputs", []):
            scope, _, rel = output.partition(":")
            if scope != "plan" or rel.startswith("features/acceptance"):
                continue
            files = source.plan_files(rel.rstrip("/")) if rel.endswith("/") else [rel]
            for item in files:
                content = source.plan_text(item)
                if content is not None:
                    cited |= set(AC_ID.findall(content))
        return {key: digest(unit["text"]) for key, unit in acceptance_all(source).items() if unit["finding"] and unit["ac"] in cited}
    if name == "features":
        def build():
            result = {}
            for rel in source.truth_files("features", ".feature"):
                if rel.count("/") < 2:
                    continue
                text = source.truth_text(rel)
                if text is not None:
                    result.update(keyed("truth", rel, feature_rule_units(text)))
            return result
        return cached(source, "features", build)
    if name == "dsl":
        def build():
            result = {}
            for rel in source.truth_files("features", "dsl.md"):
                if rel.count("/") == 2:
                    result.update(keyed("truth", rel, md_artifact(source, "truth", rel)))
            return result
        return cached(source, "dsl", build)
    if name == "constitution":
        skills = [item.strip() for item in arg.split(",") if item.strip()] or [owner["name"]]
        return {f"repo:.claude/constitution/{rel}": digest(text) for rel, text in source.constitution_files().items()
                if rel.startswith("shared/") or any(rel.startswith(f"skills/{skill}/") for skill in skills)}
    if name == "glossary":
        return keyed("truth", "features/用語表.md", md_artifact(source, "truth", "features/用語表.md"))
    raise Abort(f"相依表的輸入「{expr}」無法辨識。請修正 {DEPS_FILE.name}，可用的輸入見 plan_trace.py 的 select()。")


# ---------- 擁有者 ----------

def load_deps() -> dict:
    try:
        return json.loads(DEPS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise Abort(f"無法讀取相依表 {DEPS_FILE}（{error}）。請確認檔案存在且是合法的 JSON。")


def owners_for(deps: dict, ctx: dict) -> list[dict]:
    """相依表的擁有者，加上 plan.md 中表外前綴與 truth-changes.md 中表外 owner 的 Planner。"""
    fixed = [dict(item) for item in deps["owners"] if item["name"] != "*"]
    template = next((item for item in deps["owners"] if item["name"] == "*"), None)
    names = {item["name"] for item in fixed}
    prefixes = deps.get("planner_prefixes", {})
    extra = []
    for prefix in sorted({row["prefix"] for row in ctx["rows"]}):
        name = prefixes.get(prefix, f"{prefix.lower()}-plan")
        if name not in names and template:
            extra.append(dict(template, name=name, prefix=prefix))
            names.add(name)
    for name in ctx["truth_change_owners"]:
        if name not in names and name.endswith("-plan") and template:
            extra.append(dict(template, name=name, prefix=None))
            names.add(name)
    return fixed + extra


def planner_scheduled(owner: dict, ctx: dict) -> bool:
    return any(row["prefix"] == owner.get("prefix") for row in ctx["rows"])


def planner_relevant(owner: dict, ctx: dict, source) -> bool:
    if planner_scheduled(owner, ctx) or owner["name"] in ctx["fix_owners"] or owner["name"] in ctx["truth_change_owners"]:
        return True
    for output in owner.get("outputs", []):
        scope, _, rel = output.partition(":")
        if scope == "truth" and (source.truth_files(rel.rstrip("/")) if rel.endswith("/") else source.truth_text(rel) is not None):
            return True
    return False


def gate_open(owner: dict, ctx: dict) -> bool:
    """有 gate_prefix 的擁有者（例如只服務前端的 ui-direction）只在 plan.md 有該前綴的介面列、或被技術項或 truth-changes.md 點名時才算數。"""
    gate = owner.get("gate_prefix")
    return (not gate or any(row["prefix"] == gate for row in ctx["rows"])
            or owner["name"] in ctx["fix_owners"] or owner["name"] in ctx["truth_change_owners"])


def input_exprs(owner: dict, ctx: dict, source) -> list[str]:
    if "prefix" not in owner:
        return owner.get("inputs", [])
    if not planner_relevant(owner, ctx, source):
        return []
    phase = owner.get("scheduled", []) if planner_scheduled(owner, ctx) else owner.get("unscheduled", [])
    return phase + owner.get("always", [])


def compute_inputs(owner: dict, exprs: list[str], source, ctx: dict) -> dict[str, str]:
    result: dict[str, str] = {}
    for expr in exprs:
        result.update(select(source, ctx, owner, expr))
    return dict(sorted(result.items()))


def diff_units(before: dict[str, str], after: dict[str, str]) -> list[dict]:
    changes = []
    for key in sorted(set(before) | set(after)):
        if key not in before:
            changes.append({"status": "ADD", "unit": key})
        elif key not in after:
            changes.append({"status": "DEL", "unit": key})
        elif before[key] != after[key]:
            changes.append({"status": "MOD", "unit": key})
    return changes


# ---------- plan 與紀錄 ----------

def load_plan(plan_arg: str) -> dict:
    plan_dir = Path(plan_arg)
    if not plan_dir.is_dir():
        raise Abort(f"找不到 plan 資料夾 {plan_dir}。請傳入 plan 的路徑，例如 specs/plans/004-ranking")
    plan_dir = plan_dir.resolve()
    plan_file = plan_dir / PLAN_FILE
    if not plan_file.is_file():
        raise Abort(f"{plan_dir.name} 沒有 {PLAN_FILE}。plan 必須由 plan-package 的 open 開立。")
    try:
        data = json.loads(plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise Abort(f"{plan_file} 不是合法的 JSON（{error}）。")
    truth_dir = plan_dir.parent.parent / "truth"
    if not truth_dir.is_dir():
        raise Abort(f"找不到 truth 資料夾 {truth_dir}。plan 必須位於 <specs>/plans/ 底下，且 <specs>/truth/ 存在。")
    return {"dir": plan_dir, "data": data, "truth_dir": truth_dir}


def load_trace(plan_dir: Path) -> dict:
    path = plan_dir / TRACE_FILE
    if not path.is_file():
        return {"version": 1, "owners": {}, "history": []}
    try:
        trace = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise Abort(f"{path} 不是合法的 JSON（{error}）。這個檔只能由 plan_trace.py record 寫入；請以 git 還原或刪除後讓擁有者重新記錄。")
    trace.setdefault("owners", {})
    trace.setdefault("history", [])
    return trace


def git_context(plan_dir: Path) -> tuple[Path, str]:
    code, out, err = run_git(plan_dir, "rev-parse", "--show-toplevel")
    if code != 0:
        raise Abort(f"{plan_dir} 不在 git 倉庫中（{err}）。plan 的基準以 git 記錄。")
    root = Path(out.decode("utf-8").strip())
    code, out, _ = run_git(plan_dir, "rev-parse", "--show-prefix")
    prefix = out.decode("utf-8").strip().strip("/")
    truth_rel = "/".join(prefix.split("/")[:-2] + ["truth"])
    return root, truth_rel


class Tracker:
    """一個 plan 的串接狀態：目前與基準時的輸入、紀錄與待補跑。"""

    def __init__(self, plan_arg: str):
        plan = load_plan(plan_arg)
        self.plan_dir, self.data, self.truth_dir = plan["dir"], plan["data"], plan["truth_dir"]
        if self.data.get("status") != IN_PROGRESS:
            raise Abort(f"{self.plan_dir.name} 的狀態是「{self.data.get('status') or '未知'}」，只有進行中的 plan 有串接紀錄；已交付的 plan 唯讀。")
        self.kind = self.data.get("kind") or KIND_DEFAULT
        self.base = str(self.data.get("base") or "")
        self.deps = load_deps()
        self.current = WorkingSource(self.plan_dir, self.truth_dir)
        self._base_source = None
        self.trace = load_trace(self.plan_dir)
        tech = self.current.plan_text("技術項.md")
        changes = self.current.plan_text("truth-changes.md")
        self.ctx = {
            "rows": plan_rows(self.current),
            "fix_owners": {item["fix_owner"] for item in tech_item_lines(tech)} if tech else set(),
            "truth_change_owners": sorted(truth_changes_sections(changes)) if changes else [],
        }
        self.owners = owners_for(self.deps, self.ctx)

    def base_source(self):
        if self._base_source is None:
            if not self.base:
                raise Abort(f"{self.plan_dir.name} 的 .plan.json 沒有基準 commit（base），無法判斷本 plan 還沒有紀錄的擁有者。請以 plan-package 重新開立 plan。")
            root, truth_rel = git_context(self.plan_dir)
            self._base_source = BaseSource(root, self.base, truth_rel, self.truth_dir)
        return self._base_source

    def owner(self, name: str) -> dict:
        for item in self.owners:
            if item["name"] == name:
                return item
        known = "、".join(item["name"] for item in self.owners)
        raise Abort(f"「{name}」不是相依表中的擁有者。可用的擁有者：{known}。不是擁有者的 skill（例如 implement、analyze）呼叫 check 時不帶 --owner。")

    def wave_order(self, owner: dict) -> int:
        prefix = owner.get("prefix")
        for key, text in md_artifact(self.current, "plan", "plan.md").items():
            last = key.split(SEP)[-1]
            if prefix and last.startswith("Wave ") and re.search(rf"(?<![A-Z]){re.escape(prefix)}-\d", text):
                return int(last.split()[1])
        return 99

    def status_of(self, owner: dict, recording: bool = False) -> dict:
        record = self.trace["owners"].get(owner["name"])
        exprs = input_exprs(owner, self.ctx, self.current)
        if record is None and not recording and not gate_open(owner, self.ctx):
            exprs = []  # 沒有紀錄又不在服務範圍內（例如只有後端的 plan）：不列為待補跑；擁有者自己記錄時照常計算輸入
        current = compute_inputs(owner, exprs, self.current, self.ctx)
        scheduled = planner_scheduled(owner, self.ctx) if "prefix" in owner else None
        fresh = record is not None and "prefix" in owner and record.get("scheduled") is False and scheduled
        if record is not None:
            changes = diff_units(record.get("inputs", {}), current)
            basis = "排進 Wave 後第一次執行（輸入集合擴大）" if fresh else "上次紀錄"
        elif exprs:
            changes = diff_units(compute_inputs(owner, exprs, self.base_source(), self.ctx), current)
            basis = "基準 commit"
        else:
            changes, basis = [], "沒有被追蹤的輸入"
        unfinished = owner["name"] in self.trace.get("started", {})
        if unfinished:
            basis = f"上次執行沒有完成（{self.trace['started'][owner['name']]} 開始後沒有 record：中斷，或結果是不能改）；" + basis
        return {
            "owner": owner["name"], "order": owner.get("order", 0), "wave": self.wave_order(owner) if "prefix" in owner else None,
            "recorded": record is not None and not fresh and not unfinished, "last_result": record.get("result") if record else None,
            "basis": basis, "pending": bool(changes) or unfinished, "unfinished": unfinished, "changes": changes,
            "inputs": len(current), "via": owner.get("via", ""), "current": current, "scheduled": scheduled,
        }

    def all_status(self) -> list[dict]:
        statuses = [self.status_of(owner) for owner in self.owners if owner.get("inputs") or "prefix" in owner]
        return sorted(statuses, key=lambda item: (item["order"], item["wave"] or 0, item["owner"]))


def artifact_of(unit: str) -> str:
    return unit.split(SEP, 1)[0]


SELF_DETAIL_LIMIT = 300


def public(status: dict, limit: int | None, detail: bool = False) -> dict:
    """本 plan 有紀錄時列出變了的單位（依差異逐項判斷用）；沒有紀錄時照完整流程執行，只列各產物的單位數。
    呼叫者自己（detail）即使沒有紀錄也列出單位，供被交辦時判斷交辦以外的差異，數量太多時只列摘要。"""
    result = {key: status[key] for key in ("owner", "recorded", "last_result", "basis", "pending", "unfinished", "via")}
    result["change_count"] = len(status["changes"])
    if status["recorded"] or (detail and len(status["changes"]) <= SELF_DETAIL_LIMIT):
        result["changes"] = status["changes"] if limit is None else status["changes"][:limit]
        if limit is not None and len(status["changes"]) > limit:
            result["changes_truncated"] = True
    else:
        summary: dict[str, int] = {}
        for change in status["changes"]:
            summary[artifact_of(change["unit"])] = summary.get(artifact_of(change["unit"]), 0) + 1
        result["changed_artifacts"] = summary
    return result


def run_status(plan_arg: str, owner_name: str | None) -> dict:
    tracker = Tracker(plan_arg)
    statuses = tracker.all_status()
    pending = [public(item, SAMPLE_LIMIT) for item in statuses if item["pending"]]
    result = {"plan": tracker.plan_dir.name, "kind": tracker.kind, "base": tracker.base, "pending": pending}
    if owner_name:
        owner = tracker.owner(owner_name)
        mine = next((item for item in statuses if item["owner"] == owner["name"]), None) or tracker.status_of(owner)
        result["self"] = public(mine, None, detail=True)
        order = [item["owner"] for item in statuses]
        index = order.index(owner["name"]) if owner["name"] in order else len(order)
        result["upstream_pending"] = [item["owner"] for item in statuses[:index] if item["pending"]]
    return result


def run_record(plan_arg: str, owner_name: str, result_text: str) -> dict:
    if result_text not in RESULTS:
        raise Abort(f"--result 只接受「改了」或「不用改」，收到「{result_text}」。結果是「不能改」時不記錄：停下回報擋住的規則或上游與交辦對象，該擁有者會維持待補跑。")
    tracker = Tracker(plan_arg)
    owner = tracker.owner(owner_name)
    status = tracker.status_of(owner, recording=True)
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    entry = {"recorded_at": now, "result": result_text, "inputs": status["current"]}
    if status["scheduled"] is not None:
        entry["scheduled"] = status["scheduled"]

    def apply(trace: dict) -> None:
        trace["owners"][owner["name"]] = entry
        trace.setdefault("started", {}).pop(owner["name"], None)
        trace["history"].append({"at": now, "owner": owner["name"], "result": result_text,
                                 "was_pending": status["pending"], "changed_units": len(status["changes"])})

    update_trace(tracker.plan_dir, apply)
    after = Tracker(plan_arg)
    still = [item["owner"] for item in after.all_status() if item["pending"]]
    return {"ok": True, "plan": tracker.plan_dir.name, "owner": owner["name"], "result": result_text,
            "inputs": len(status["current"]), "pending_now": still}


def mark_started(plan_arg: str, owner_name: str) -> None:
    """擁有者以 check 開始一次執行時記下開始時間；record 會清除它。之後沒有 record（中斷，或結果是不能改）的擁有者一直算待補跑。"""
    tracker = Tracker(plan_arg)
    owner = tracker.owner(owner_name)
    if not owner.get("inputs") and "prefix" not in owner:
        return  # 沒有被追蹤的輸入（例如 dev-finding）不會是待補跑，不記開始時間
    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    update_trace(tracker.plan_dir, lambda trace: trace.setdefault("started", {}).__setitem__(owner["name"], now))


def update_trace(plan_dir: Path, apply) -> None:
    """在檔案鎖內重新讀取 .plan-trace.json、套用修改並寫回；system-analysis 的 Wave 會讓多個 Planner 同時 check 與 record。"""
    lock = plan_dir / LOCK_FILE
    deadline = time.monotonic() + 60
    while True:
        try:
            handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise Abort(f"{lock} 已存在超過 60 秒，可能是先前的 record 中斷留下的。確認沒有其他擁有者正在記錄後刪除這個檔案再重試。")
            time.sleep(0.2)
    try:
        trace = load_trace(plan_dir)
        apply(trace)
        trace["plan"] = plan_dir.name
        trace["version"] = 1
        (plan_dir / TRACE_FILE).write_text(json.dumps(trace, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    finally:
        os.close(handle)
        lock.unlink(missing_ok=True)


def run_deps(fmt: str) -> str:
    deps = load_deps()
    if fmt == "json":
        return json.dumps(deps, ensure_ascii=False, indent=2)
    lines = ["# 相依表", "", "## 產物的節與事實的家", "", "| 產物 | 節 | 寫入者 | 事實的家 |", "|---|---|---|---|"]
    for artifact in deps["artifacts"]:
        for section in artifact["sections"]:
            lines.append(f"| `{artifact['path']}` | {section['name']} | {section['writers']} | {section['home']} |")
    lines += ["", "## 擁有者與直接依據的輸入", "", "| 擁有者 | 輸入 | 產出 | 待補跑時的執行方式 |", "|---|---|---|---|"]
    for owner in sorted(deps["owners"], key=lambda item: item.get("order", 0)):
        if "prefix" in owner:
            inputs = f"排進 Wave：{'、'.join(owner.get('scheduled', [])) or '無'}；沒有排進：{'、'.join(owner.get('unscheduled', [])) or '無'}；另含：{'、'.join(owner.get('always', []))}"
        else:
            inputs = "、".join(owner.get("inputs", [])) or "無（只記錄歷程）"
        name = "其他 Planner" if owner["name"] == "*" else owner["name"]
        lines.append(f"| {name} | {inputs} | {'、'.join(owner.get('outputs', [])) or '—'} | {owner.get('via', '')} |")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="串接器：記錄擁有者的輸入摘要、列出待補跑與輸出相依表。")
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status", help="列出待補跑的擁有者、順序與變了的輸入單位")
    status.add_argument("plan_dir", help="plan 資料夾，例如 specs/plans/004-ranking")
    status.add_argument("--owner", help="呼叫者的 skill 名稱；有帶時另輸出它自己的輸入差異（self）與上游的待補跑")
    record = commands.add_parser("record", help="擁有者跑完、結果是改了或不用改時，記錄它目前的輸入摘要")
    record.add_argument("plan_dir", help="plan 資料夾，例如 specs/plans/004-ranking")
    record.add_argument("--owner", required=True, help="擁有者的 skill 名稱，例如 api-plan")
    record.add_argument("--result", required=True, help="這次的結果：改了 或 不用改（不能改不記錄）")
    deps = commands.add_parser("deps", help="輸出相依表")
    deps.add_argument("--format", choices=("markdown", "json"), default="markdown", help="輸出格式（預設 markdown）")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        if args.command == "deps":
            print(run_deps(args.format))
            return 0
        if args.command == "status":
            result = run_status(args.plan_dir, args.owner)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            names = "、".join(item["owner"] for item in result["pending"]) or "無"
            print(f"待補跑：{names}", file=sys.stderr)
            return 0
        result = run_record(args.plan_dir, args.owner, args.result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"已記錄 {result['owner']}（{result['result']}），輸入 {result['inputs']} 個單位；目前待補跑：{'、'.join(result['pending_now']) or '無'}", file=sys.stderr)
        return 0
    except Abort as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
