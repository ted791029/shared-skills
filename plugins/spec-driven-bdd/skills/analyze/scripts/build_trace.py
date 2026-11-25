# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""解析進行中的 plan 與 specs/truth/，只追溯這個 plan 的異動：spec.md 的需求（含所屬故事與優先順序）與受影響的既有功能、plan.md 介面盤點（含異動欄）、這次異動的介面文檔段落（OpenAPI 的 operation 另列每個回應與它和基準 commit 相比的異動）、plan 的涵蓋表（含異動欄）、acceptance 的涵蓋註解與開發發現的 AC、這次新增與修改的 Rule（取自 task 的 feature_summary.py）、端點 feature 與 dsl.md，以及 tasks.md 的 Phase 標頭與任務，輸出需求、介面、介面文檔、Rule 與任務之間的追溯 JSON。
段落與任務的對應以 Rule 為準：Rule 的步驟、表格，或步驟對到的 dsl.md 句型提到段落的定位值時，該 Rule 操作或查證了這個段落；範疇含這條 Rule 的 Feature Phase 任務與必讀指向段落的任務是段落的負責任務，不以介面 ID 前綴推定。"""

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS.parents[1] / "task" / "scripts"))
from collect_artifacts import (GLOSSARY, collect_endpoints, display_path, project_root, read_feature_endpoints,  # noqa: E402
                               read_inventory, read_table, read_truth_changes, strip_code)
from feature_summary import summarize  # noqa: E402
from truth_changes import Abort, git, load_context  # noqa: E402

REQUIREMENT_PATTERN = re.compile(r"^\s*- \*\*((FR|NFR|SC)-\d+)\*\*(?:（([^）]*)）)?：(.*)$")
STORY_PATTERN = re.compile(r"^### 使用者故事 (\d+) - (.+?)（優先順序：(P\d+)）")
SUBHEADING_PATTERN = re.compile(r"^#{3,4} (.+)$")
STORY_RESET_PATTERN = re.compile(r"^#{2,3}\s")
ID_RANGE_PATTERN = re.compile(r"\b([A-Z]+)-(\d+)(?:～(?:[A-Z]+-)?(\d+))?")
REQUIREMENT_REF_PATTERN = re.compile(r"\b(?:FR|NFR|SC)-\d+")
AC_PATTERN = re.compile(r"\bAC-\d+\b")
US_PATTERN = re.compile(r"\bUS\d+\b")
PHASE_PATTERN = re.compile(r"^## Phase (\d+)：(.+)$")
FEATURE_PHASE_PATTERN = re.compile(r"^(修正\s*)?([^/\s]+)/(.+\.feature)$")
TASK_PATTERN = re.compile(r"^- \[([ xX])\] (T\d{3})\b(.*)$")
STAGE_PATTERN = re.compile(r"\[(紅燈|綠燈|重構|重跑|驗證)\]")
SCOPE_PATTERN = re.compile(r"範疇：`([^`]+)`")
SCOPE_PATH_PATTERN = re.compile(r"specs/[^`]*?features/([^/]+)/?([^:/]*\.feature)?((?::\d+)*)$")
SCOPE_RULE_PATTERN = re.compile(r"(?:Rule|規則)\s*「([^」]+)」")
RED_COUNT_PATTERN = re.compile(r"撰寫 (\d+) 條 Rule、(\d+) 個 Example")
TASK_ANCHOR_PATTERN = re.compile(r"^  - 📎 必讀：`([^`]+)` — (.*)$")
TASK_CONSTRAINT_PATTERN = re.compile(r"^  - NFR 約束：(.*)$")
HEADER_PATTERN = re.compile(r"^\*\*(驗收 AC|NFR 約束|預計修改|📎 必讀|不另列任務)\*\*：(.*)$")
HEADER_ANCHOR_PATTERN = re.compile(r"^- `([^`]+)` — (.*)$")
NO_TASK_PATTERN = re.compile(r"^- ((?:(?:FR|NFR|SC)-\d+[、，, ]*)+)：(.+)$")
PHASE_REF_PATTERN = re.compile(r"Phase\s*(\d+)((?:\s*(?:[、,，]|[～~至到-])\s*(?:Phase\s*)?\d+)*)")
PHASE_REF_PART_PATTERN = re.compile(r"([、,，]|[～~至到-])\s*(?:Phase\s*)?(\d+)")
COVER_PATTERN = re.compile(r"^\s*#\s*涵蓋[:：](.+)$")
FINDING_PATTERN = re.compile(r"^\s*#\s*開發發現[:：](.+)$")
RULE_PATTERN = re.compile(r"^\s*(?:Rule|規則)\s*[:：]\s*(.+?)\s*$")
EXAMPLE_PATTERN = re.compile(r"^\s*(?:Scenario Outline|Scenario Template|Scenario|Example|場景大綱|劇本大綱|場景|劇本|例子)\s*[:：]\s*(.*)$")
STEP_PATTERN = re.compile(r"^\s*(?:(?:Given|When|Then|And|But)\s+|\*\s+|(?:假設|假定|假如|當|那麼|而且|並且|同時|但是)\s*)(\S.*?)\s*$")
DSL_ROW_PATTERN = re.compile(r"^\|\s*`([^`]+)`\s*\|")
PARAM_PATTERN = re.compile(r"\{[^{}]*\}")
STEP_VALUE = r'("[^"]*"|<[^>]+>|\S+?)'
MD_HEADING_PATTERN = re.compile(r"^(#{1,6}) (.+)$")
PATH_PATTERN = re.compile(r"^  (/\S*):\s*$")
ENTRY_PATH_PATTERN = re.compile(r"^  (['\"]?)(/[^'\"]*)\1:\s*$")
REF_PATTERN = re.compile(r"^\s+\$ref:\s*['\"]?([^'\"\s]+)['\"]?\s*$")
METHOD_PATTERN = re.compile(r"^    (get|post|put|patch|delete|head|options):\s*$")
TOP_METHOD_PATTERN = re.compile(r"^(get|post|put|patch|delete|head|options):\s*$")
OPERATION_PATTERN = re.compile(r"^\s+operationId:\s*(\S+)")
RESPONSES_PATTERN = re.compile(r"^\s*responses:\s*$")
STATUS_PATTERN = re.compile(r"""^\s*['"]?([1-5]\d\d|[1-5]XX|default)['"]?:\s*$""")
CODE_LEAD_PATTERN = re.compile(r"(?<![A-Za-z_])`?code`?\s*(?:為|是|:|：)\s*")
CODE_NAME_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9]*(?:[_-][A-Za-z0-9]+)*")
DESCRIPTION_PATTERN = re.compile(r"(?:^|\s)description:\s*(?:[>|][-+]?\s+)?(.*?)(?=\s+(?:content|headers|links|\$ref|x-[\w-]+):|$)")
BACKTICK_CODE_PATTERN = re.compile(r"`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`")
CLAUSE_SPLIT_PATTERN = re.compile(r"；|;|<br>|・")
SCHEMA_PATTERN = re.compile(r"^    ([A-Za-z0-9_]+):\s*$")
DBML_PATTERN = re.compile(r"^(Table|Ref|Enum|TableGroup|Project)\b\s*([^\s{:]*)")
TESTID_PATTERN = re.compile(r'data-testid="([^"]+)"')
CODE_SPAN_PATTERN = re.compile(r"`([^`\s]{4,})`")
LOCATOR_TOKEN_PATTERN = re.compile(r"^[A-Za-z][\w]*(?:[-_./][\w{}]+)+$")
DEFINITION_PATTERN = re.compile(r"^(?:extend\s+)?([a-z]+)\s+([A-Za-z_][\w.]*)\b[^{;]*\{\s*$")
TECHNICAL_BASIS_PATTERN = re.compile(r"技術[：:]\s*(.+)$")
AFFECTED_HEADING = "## 受影響的既有功能"
AFFECTED_ITEM_PATTERN = re.compile(r"^- (.+?)：(.+)$")
REQUIREMENT_KINDS = ("FR", "NFR", "SC")
BASE_PHASES = {"Setup": "setup", "Foundational": "foundational", "移除": "removal", "技術項": "tech_items",
               "NFR 重構": "nfr_refactor", "Polish": "polish", "Verify": "verify"}
SUPPORT_KINDS = {"setup", "foundational", "removal", "tech_items", "polish", "verify"}
WORK_CHANGES = {"ADD", "MOD"}
MAIN_SECTION_KINDS = {"operation", "table", "h2", "definition"}
KNOWN_DOC_SUFFIXES = {".md", ".yaml", ".yml", ".dbml", ".html"}
ASSET_SUFFIXES = {
    ".css", ".js", ".mjs", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico",
    ".woff", ".woff2", ".ttf", ".otf", ".mp3", ".mp4", ".webm", ".pdf",
}
COVERAGE = "features/涵蓋表.md"
ENTRY_CONTRACT = "contracts/openapi.yaml"
LISTED_RULES = 5
LISTED_RESPONSE_RULES = 3
DESCRIPTION_CHARS = 80


def expand_ids(text: str, prefixes: tuple[str, ...] | None = None) -> list[str]:
    """展開「FR-001～FR-004」這類範圍；編號可能有空號，只走 spec.md 中存在的需求時不會誤判。"""
    ids = []
    for prefix, start, end in ID_RANGE_PATTERN.findall(text):
        if prefixes and prefix not in prefixes:
            continue
        width = len(start)
        last = int(end) if end else int(start)
        for number in range(int(start), max(int(start), last) + 1):
            item = f"{prefix}-{number:0{width}d}"
            if item not in ids:
                ids.append(item)
    return ids


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read_spec(spec_path: Path) -> tuple[list[dict], list[dict], list[dict]]:
    """需求的 story 是定義它的使用者故事；定義在故事以外（全域需求、成功標準）時為 None。"""
    requirements, stories, affected = [], [], []
    category = ""
    story = None
    in_affected = False
    for line_no, line in enumerate(spec_path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith("## "):
            in_affected = line.strip() == AFFECTED_HEADING
        if in_affected:
            item = AFFECTED_ITEM_PATTERN.match(line)
            if item:
                affected.append({"name": item.group(1).strip(), "impact": item.group(2).strip(), "line": line_no})
            continue
        matched_story = STORY_PATTERN.match(line)
        if matched_story:
            stories.append({"id": f"US{matched_story.group(1)}", "title": matched_story.group(2), "priority": matched_story.group(3), "line": line_no})
            category = f"使用者故事 {matched_story.group(1)}"
            story = f"US{matched_story.group(1)}"
            continue
        if STORY_RESET_PATTERN.match(line):
            story = None
        heading = SUBHEADING_PATTERN.match(line)
        if heading:
            category = heading.group(1).strip()
            continue
        matched = REQUIREMENT_PATTERN.match(line)
        if matched:
            requirements.append({
                "id": matched.group(1),
                "kind": matched.group(2),
                "category": matched.group(3) or category,
                "story": story,
                "line": line_no,
                "text": matched.group(4).strip(),
            })
    return requirements, stories, affected


def section_tokens(lines: list[str], start: int, level: int) -> list[str]:
    """收集 Markdown 段落（含子段落）內可被測試操作的定位值：testid 與含分隔符的程式碼片段。"""
    tokens = []
    for line in lines[start:]:
        heading = MD_HEADING_PATTERN.match(line)
        if heading and len(heading.group(1)) <= level:
            break
        for token in TESTID_PATTERN.findall(line) + CODE_SPAN_PATTERN.findall(line):
            if LOCATOR_TOKEN_PATTERN.match(token) and token not in tokens:
                tokens.append(token)
    return tokens


def read_routes(truth_dir: Path) -> dict[str, str]:
    """由 truth 的 OpenAPI 入口檔建立「路徑檔 → 路由」的對照（入口檔以 $ref 掛上每個路徑檔）。"""
    entry = truth_dir / ENTRY_CONTRACT
    routes: dict[str, str] = {}
    if not entry.is_file():
        return routes
    in_paths, route = False, None
    for line in entry.read_text(encoding="utf-8").splitlines():
        if not line.startswith(" "):
            in_paths = line.strip() == "paths:"
            route = None
            continue
        if not in_paths:
            continue
        matched = ENTRY_PATH_PATTERN.match(line)
        if matched:
            route = matched.group(2)
            continue
        ref = REF_PATTERN.match(line)
        if ref and route:
            target = (entry.parent / ref.group(1)).resolve()
            try:
                routes[target.relative_to(truth_dir.resolve()).as_posix()] = route
            except ValueError:
                pass
            route = None
    return routes


def response_codes(text: str) -> list[str]:
    """回應說明中「code 為 a（…）、b（…）」列出的錯誤碼；沒有這種寫法時改取以反引號標出的 snake_case 識別碼。"""
    codes: list[str] = []
    for lead in CODE_LEAD_PATTERN.finditer(text):
        depth, kept = 0, []
        for char in text[lead.end():]:
            if char in "（(":
                depth += 1
            elif char in "）)":
                if depth == 0:
                    break
                depth -= 1
            elif depth:
                continue
            elif char in "；;。，,":
                break
            else:
                kept.append(char)
        for piece in re.split(r"[、/]|或", "".join(kept)):
            words = piece.replace("`", " ").split()
            token = words[0] if words else ""
            if CODE_NAME_PATTERN.fullmatch(token) and token not in codes:
                codes.append(token)
    if not codes:
        codes = list(dict.fromkeys(BACKTICK_CODE_PATTERN.findall(text)))
    return codes


def read_responses(block: list[tuple[int, str]]) -> list[dict]:
    """operation 區塊中 `responses:` 底下的每個狀態碼與它的說明、錯誤碼。"""
    responses: list[dict] = []
    current = None
    base_indent = status_indent = None
    for line_no, text in block:
        if not text.strip():
            continue
        indent = len(text) - len(text.lstrip(" "))
        if base_indent is None:
            if RESPONSES_PATTERN.match(text):
                base_indent = indent
            continue
        if indent <= base_indent:
            break
        status = STATUS_PATTERN.match(text)
        if status and (status_indent is None or indent == status_indent):
            status_indent = indent
            current = {"status": status.group(1), "line": line_no, "lines": []}
            responses.append(current)
            continue
        if current is not None:
            current["lines"].append(text.strip())
    for response in responses:
        text = compact(" ".join(response.pop("lines")))
        matched = DESCRIPTION_PATTERN.search(text)
        description = matched.group(1).strip() if matched else ""
        response["codes"] = response_codes(description)
        response["description"] = description[:DESCRIPTION_CHARS]
        response["text"] = text
    return responses


def yaml_operations(lines: list[str], route: str | None) -> list[dict]:
    """依 method 區塊取出每個 operation：operationId 的行號、method、路徑、區塊內容與回應；拆檔的路徑檔以入口檔給的路由為路徑。"""
    blocks: list[dict] = []
    block = None
    current_path = route or ""
    method_pattern = TOP_METHOD_PATTERN if route is not None else METHOD_PATTERN
    for line_no, line in enumerate(lines, start=1):
        indent = len(line) - len(line.lstrip(" "))
        if block is not None and line.strip() and indent <= block["indent"]:
            blocks.append(block)
            block = None
        if route is None:
            path_line = PATH_PATTERN.match(line)
            if path_line:
                current_path = path_line.group(1)
                continue
        method = method_pattern.match(line)
        if method:
            block = {"method": method.group(1).upper(), "path": current_path, "indent": indent, "lines": []}
            continue
        if block is not None:
            block["lines"].append((line_no, line))
    if block is not None:
        blocks.append(block)
    operations = []
    for item in blocks:
        operation = next(((line_no, OPERATION_PATTERN.match(text).group(1)) for line_no, text in item["lines"] if OPERATION_PATTERN.match(text)), None)
        if operation is None:
            continue
        operations.append({
            "line": operation[0], "name": operation[1], "method": item["method"], "path": item["path"],
            "block": compact("\n".join(text for _, text in item["lines"])), "responses": read_responses(item["lines"]),
        })
    return operations


def index_text(lines: list[str], suffix: str, doc: str, prefix: str, route: str | None, id_prefix: str = "") -> list[dict]:
    """id_prefix 是這個 plan 的編號加斜線（例如 004/）：介面 ID 只在各 plan 內唯一，truth 的 dsl.md 以 `004/UI-01` 引用。
    Markdown 段落的 interface 是它所在的、標題以介面 ID 開頭的段落的介面 ID（子段落沿用上層的）。"""
    sections = []
    parts = doc.split("/")
    if suffix in {".yaml", ".yml"} and "components" in parts[:-2]:
        kind = parts[parts.index("components") + 1]
        singular = {"schemas": "schema", "parameters": "parameter", "responses": "response"}.get(kind, kind)
        stem = Path(doc).stem
        return [{"doc": doc, "prefix": prefix, "line": 1, "kind": singular, "name": f"components.{kind}.{stem}", "match": [stem]}]
    if suffix in {".yaml", ".yml"}:
        for operation in yaml_operations(lines, route):
            sections.append({"doc": doc, "prefix": prefix, "kind": "operation", **operation})
    in_schemas = False
    owners: list[tuple[int, str]] = []
    for line_no, line in enumerate(lines, start=1):
        base = {"doc": doc, "prefix": prefix, "line": line_no}
        if suffix == ".md":
            matched = MD_HEADING_PATTERN.match(line)
            if matched:
                level = len(matched.group(1))
                name = matched.group(2).strip()
                tokens = section_tokens(lines, line_no, level)
                owners = [(owner_level, owner) for owner_level, owner in owners if owner_level < level]
                head_id = ID_RANGE_PATTERN.match(name)
                if head_id:
                    tokens.insert(0, id_prefix + head_id.group(0))
                    owners.append((level, f"{head_id.group(1)}-{head_id.group(2)}"))
                sections.append({**base, "kind": f"h{level}", "name": name, "match": tokens, "interface": owners[-1][1] if owners else None})
        elif suffix in {".yaml", ".yml"}:
            if line.startswith("  schemas:"):
                in_schemas = True
                continue
            if in_schemas and line.strip() and not line.startswith("    "):
                in_schemas = False
            schema = SCHEMA_PATTERN.match(line) if in_schemas else None
            if schema:
                sections.append({**base, "kind": "schema", "name": f"components.schemas.{schema.group(1)}", "match": [schema.group(1)]})
        elif suffix == ".dbml":
            matched = DBML_PATTERN.match(line)
            if matched:
                name = f"{matched.group(1)} {matched.group(2)}".strip()
                sections.append({**base, "kind": matched.group(1).lower(), "name": name, "match": [matched.group(2)] if matched.group(2) else []})
        elif suffix == ".html":
            for testid in TESTID_PATTERN.findall(line):
                sections.append({**base, "kind": "testid", "name": testid, "match": [testid]})
        else:
            matched = DEFINITION_PATTERN.match(line)
            if matched:
                sections.append({**base, "kind": "definition", "name": f"{matched.group(1)} {matched.group(2)}", "match": [matched.group(2)]})
    return sections


def anchor_hits(section: dict, anchors: list[str]) -> bool:
    """truth-changes.md 的對象寫了「＞ 段落」時，只有那些段落算這次的異動。"""
    name = section["name"].replace("`", "")
    for anchor in anchors:
        text = anchor.replace("`", "")
        if name and (name == text or text.startswith(name + " ") or text.endswith(" " + name) or name in text.split()):
            return True
    return False


def mark_operation_changes(found: list[dict], base_lines: list[str] | None, route: str | None) -> None:
    """與基準 commit 的同一份檔案比對每個 operation 與回應：基準沒有的為 ADD，內容不同的為 MOD，相同的為 None。"""
    before = {item["name"]: item for item in yaml_operations(base_lines, route)} if base_lines is not None else {}
    for section in found:
        if section["kind"] != "operation":
            continue
        old = before.get(section["name"])
        if old is None:
            section["change"] = "ADD"
            for response in section["responses"]:
                response["change"] = "ADD"
            continue
        old_responses = {response["status"]: response for response in old["responses"]}
        for response in section["responses"]:
            previous = old_responses.get(response["status"])
            response["change"] = "ADD" if previous is None else ("MOD" if previous["text"] != response["text"] else None)
        section["change"] = "MOD" if old["block"] != section["block"] else None


def index_docs(plan_dir: Path, truth_dir: Path, endpoints: list[dict], routes: dict[str, str], show_base) -> tuple[list[dict], list[str]]:
    root = project_root(plan_dir)
    id_prefix = plan_dir.resolve().name[:3] + "/"
    sections, unindexed = [], []
    for endpoint in endpoints:
        in_plan = endpoint["record"] == "plan"
        base = plan_dir if in_plan else truth_dir
        for doc in endpoint["docs"]:
            path = base / doc["path"]
            if path.is_dir():
                children = sorted(child for child in path.rglob("*") if child.is_file() and child.suffix.lower() not in ASSET_SUFFIXES)
            else:
                children = [path] if path.is_file() else []
            for child in children:
                short = child.resolve().relative_to(base.resolve()).as_posix()
                if short == ENTRY_CONTRACT and routes:
                    continue  # 拆檔的入口檔只有 $ref 登記，段落在各路徑檔與元件檔
                route = routes.get(short) if not in_plan else None
                try:
                    found = index_text(child.read_text(encoding="utf-8").splitlines(), child.suffix, short, endpoint["prefix"], route, id_prefix)
                except UnicodeDecodeError:
                    continue
                if not in_plan and any(section["kind"] == "operation" for section in found):
                    base_text = show_base(short)
                    mark_operation_changes(found, base_text.splitlines() if base_text is not None else None, route)
                if not found and child.suffix not in KNOWN_DOC_SUFFIXES:
                    unindexed.append(display_path(child, root))
                for section in found:
                    section["file"] = display_path(child, root)
                    section["changed"] = doc["whole_file"] or anchor_hits(section, doc["anchors"])
                sections += found
    return sections, unindexed


def read_acceptance(plan_dir: Path) -> dict[str, dict]:
    """依 acceptance 每個 Example 上方最近的 `# 涵蓋：` 或 `# 開發發現：` 註解，取得每個 AC 涵蓋的使用者故事與需求。"""
    acs = {}
    for path in sorted((plan_dir / "features" / "acceptance").glob("*.feature")):
        pending: tuple[str, str] | None = None
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            cover = COVER_PATTERN.match(line)
            finding = FINDING_PATTERN.match(line)
            if cover or finding:
                pending = ("cover", cover.group(1)) if cover else ("finding", finding.group(1))
                continue
            example = EXAMPLE_PATTERN.match(line)
            if not example:
                continue
            matched = AC_PATTERN.search(example.group(1))
            if matched:
                kind, text = pending or ("cover", "")
                acs[matched.group(0)] = {
                    "file": f"features/acceptance/{path.name}",
                    "line": line_no,
                    "finding": kind == "finding",
                    "basis": text.strip() if kind == "finding" else None,
                    "stories": US_PATTERN.findall(text) if kind == "cover" else [],
                    "requirements": REQUIREMENT_REF_PATTERN.findall(text) if kind == "cover" else [],
                }
            pending = None
    return acs


def read_coverage(plan_dir: Path) -> tuple[list[dict], list[dict]]:
    """讀取 plan 涵蓋表的「AC 涵蓋表」與「補充案例」，每一列含端點、feature、Rule 與異動。"""
    path = plan_dir / COVERAGE
    ac_rows, supplement_rows = [], []
    for row in read_table(path, "## AC 涵蓋表"):
        ac_rows.append({"ac": AC_PATTERN.findall(row.get("AC", "")), "key": f"{strip_code(row.get('端點', ''))}/{strip_code(row.get('feature', ''))}",
                        "rule": strip_code(row.get("Rule", "")), "change": strip_code(row.get("異動", "")), "line": row["line"]})
    for row in read_table(path, "## 補充案例"):
        supplement_rows.append({"requirements": REQUIREMENT_REF_PATTERN.findall(row.get("來源需求", "")),
                                "key": f"{strip_code(row.get('端點', ''))}/{strip_code(row.get('feature', ''))}",
                                "rule": strip_code(row.get("Rule", "")), "change": strip_code(row.get("異動", "")), "line": row["line"]})
    return ac_rows, supplement_rows


def parse_scope(scope: str) -> tuple[str | None, str | None, list[int], list[str]]:
    """範疇的端點資料夾、feature、Rule 標題行號，以及以「＞ Rule「名稱」」定位的 Rule 名稱。"""
    path, _, located = scope.replace(">", "＞").partition("＞")
    matched = SCOPE_PATH_PATTERN.search(path.strip())
    if not matched:
        return None, None, [], []
    lines = [int(number) for number in matched.group(3).split(":") if number]
    names = [unit_name(name) for name in SCOPE_RULE_PATTERN.findall(located)]
    return matched.group(1), matched.group(2) or None, lines, names


def phase_kind(name: str) -> str:
    for prefix, kind in BASE_PHASES.items():
        if name.startswith(prefix):
            return kind
    return "feature" if FEATURE_PHASE_PATTERN.match(name) else "other"


def phases_mentioned(text: str) -> list[int]:
    """理由中提到的 Phase 編號：「Phase 3～9」展開成 3 到 9，「Phase 5、Phase 8」「Phase 5、8」各自列出。"""
    numbers: set[int] = set()
    for matched in PHASE_REF_PATTERN.finditer(text):
        last = int(matched.group(1))
        numbers.add(last)
        for separator, number in PHASE_REF_PART_PATTERN.findall(matched.group(2)):
            value = int(number)
            if separator in "、,，":
                numbers.add(value)
            else:
                numbers.update(range(min(last, value), max(last, value) + 1))
            last = value
    return sorted(numbers)


def anchor_entry(line_no: int, target: str, reason: str) -> dict:
    segments = [segment.strip() for segment in target.split("›")]
    return {"line": line_no, "file": segments[0], "segments": segments[1:], "reason": reason.strip(), "requirements": REQUIREMENT_REF_PATTERN.findall(target)}


def read_tasks(tasks_path: Path) -> tuple[list[dict], list[dict]]:
    phases = []
    tasks = []
    phase = None
    field = None
    current = None
    for line_no, line in enumerate(tasks_path.read_text(encoding="utf-8").splitlines(), start=1):
        matched_phase = PHASE_PATTERN.match(line)
        if matched_phase:
            name = matched_phase.group(2).strip()
            feature = FEATURE_PHASE_PATTERN.match(name)
            phase = {
                "number": int(matched_phase.group(1)),
                "name": name,
                "kind": phase_kind(name),
                "line": line_no,
                "endpoint": feature.group(2) if feature else None,
                "feature": feature.group(3) if feature else None,
                "fix": bool(feature and feature.group(1)),
                "acceptance": None,
                "nfr_constraints": [],
                "planned_files": "",
                "anchors": [],
                "no_task": [],
                "tasks": [],
            }
            phases.append(phase)
            field, current = None, None
            continue
        if phase is None:
            continue
        header = HEADER_PATTERN.match(line)
        if header:
            field, value = header.group(1), header.group(2).strip()
            if field == "驗收 AC":
                phase["acceptance"] = AC_PATTERN.findall(value)
            elif field == "NFR 約束":
                phase["nfr_constraints"] = REQUIREMENT_REF_PATTERN.findall(value)
            elif field == "預計修改":
                phase["planned_files"] = value
            current = None
            continue
        task = TASK_PATTERN.match(line)
        if task:
            body = task.group(3).strip()
            stage = STAGE_PATTERN.search(body)
            scope = SCOPE_PATTERN.search(body)
            endpoint, feature_file, scope_lines, scope_names = parse_scope(scope.group(1)) if scope else (None, None, [], [])
            current = {
                "id": task.group(2),
                "line": line_no,
                "done": task.group(1) != " ",
                "phase": phase["number"],
                "phase_name": phase["name"],
                "phase_kind": phase["kind"],
                "stage": stage.group(1) if stage else None,
                "scope": scope.group(1) if scope else None,
                "scope_endpoint": endpoint,
                "scope_feature": feature_file,
                "scope_lines": scope_lines,
                "scope_rule_names": scope_names,
                "body": body,
                "nfr_constraints": [],
                "anchors": [],
                "body_requirements": REQUIREMENT_REF_PATTERN.findall(body),
            }
            tasks.append(current)
            phase["tasks"].append(current["id"])
            field = None
            continue
        anchor = TASK_ANCHOR_PATTERN.match(line)
        if anchor and current is not None:
            current["anchors"].append(anchor_entry(line_no, anchor.group(1), anchor.group(2)))
            continue
        constraint = TASK_CONSTRAINT_PATTERN.match(line)
        if constraint and current is not None:
            current["nfr_constraints"] = REQUIREMENT_REF_PATTERN.findall(constraint.group(1))
            continue
        if field == "📎 必讀":
            header_anchor = HEADER_ANCHOR_PATTERN.match(line)
            if header_anchor:
                phase["anchors"].append(anchor_entry(line_no, header_anchor.group(1), header_anchor.group(2)))
        elif field == "不另列任務":
            no_task = NO_TASK_PATTERN.match(line)
            if no_task:
                phase["no_task"].append({
                    "line": line_no,
                    "requirements": REQUIREMENT_REF_PATTERN.findall(no_task.group(1)),
                    "reason": no_task.group(2).strip(),
                    "phases_mentioned": phases_mentioned(no_task.group(2)),
                })
    return phases, tasks


def anchor_matches(section: dict, anchor: dict) -> bool:
    if not anchor["segments"]:
        return False
    if anchor["file"] != section["doc"] and not section["doc"].endswith("/" + anchor["file"]) and anchor["file"] != section["file"]:
        return False
    for piece in (part.strip() for part in anchor["segments"][0].split("、")):
        if piece == section["name"] or piece in section.get("match", []):
            return True
        if section["kind"].startswith("h") and section["name"].startswith(piece):
            return True
        if section["kind"] == "operation" and piece.replace("`", "") in {f"{section.get('method', '')} {section.get('path', '')}".strip(), section["name"]}:
            return True
    return False


def contains_token(text: str, token: str) -> bool:
    return re.search(r"(?<![\w-])" + re.escape(token) + r"(?![\w-])", text) is not None


def contains_operation(text: str, section: dict) -> bool:
    route = re.escape(section.get("path", ""))
    if route and re.search(r"\b" + section.get("method", "") + r"\s+`?" + route + r"(?=[\s`?)）,，]|$)", text, re.MULTILINE):
        return True
    if route and re.search(r"(?<![\w/{}-])" + route + r"\?", text):
        return True
    return contains_token(text, section["name"])


def is_main(section: dict) -> bool:
    """主要段落：operation、Table、頂層定義、Markdown 的二級標題，以及任何層級中以介面 ID 開頭的標題。"""
    return section["kind"] in MAIN_SECTION_KINDS or (section["kind"].startswith("h") and ID_RANGE_PATTERN.match(section["name"]) is not None)


def section_hit(section: dict, text: str) -> bool:
    if section["kind"] == "operation":
        return contains_operation(text, section)
    return any(contains_token(text, token) for token in section.get("match", []))


def unit_name(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def read_dsl_rows(path: Path) -> list[dict]:
    """dsl.md 每個句型列：第一欄以反引號包住的句型、比對步驟用的正規式與整列文字；只有參數、沒有字面文字的列不算句型。"""
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        matched = DSL_ROW_PATTERN.match(line)
        if not matched:
            continue
        pieces = PARAM_PATTERN.split(matched.group(1).strip())
        if not "".join(pieces).strip():
            continue
        rows.append({"line": line_no, "pattern": matched.group(1).strip(),
                     "regex": re.compile("^" + STEP_VALUE.join(re.escape(piece) for piece in pieces) + "$"), "text": line})
    return rows


def read_units(path: Path) -> tuple[list[str], list[dict]]:
    """回傳 feature 第一條 Rule 之前的內容（含 Background）與每條 Rule 的內容；不在 Rule 底下的 Example 各自視為一個單位，與 feature_summary.py 的計法相同。"""
    preamble: list[str] = []
    units: list[dict] = []
    current = None
    in_doc = None
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        target = current["lines"] if current is not None else preamble
        if in_doc:
            target.append(line)
            if stripped.startswith(in_doc):
                in_doc = None
            continue
        if stripped.startswith(('"""', "```")):
            in_doc = stripped[:3]
            target.append(line)
            continue
        rule = RULE_PATTERN.match(line)
        if rule:
            current = {"name": unit_name(rule.group(1)), "line": line_no, "lines": [line], "rule": True}
            units.append(current)
            continue
        example = EXAMPLE_PATTERN.match(line)
        if example and (current is None or not current["rule"]):
            current = {"name": unit_name(example.group(1)), "line": line_no, "lines": [line], "rule": False}
            units.append(current)
            continue
        target.append(line)
    return preamble, units


def steps_of(lines: list[str]) -> list[str]:
    steps, in_doc = [], None
    for line in lines:
        stripped = line.strip()
        if in_doc:
            if stripped.startswith(in_doc):
                in_doc = None
            continue
        if stripped.startswith(('"""', "```")):
            in_doc = stripped[:3]
            continue
        if stripped.startswith(("#", "@", "|")):
            continue
        matched = STEP_PATTERN.match(line)
        if matched and not RULE_PATTERN.match(line) and not EXAMPLE_PATTERN.match(line):
            steps.append(matched.group(1))
    return steps


def endpoint_units(folder: Path, rows: list[dict]) -> tuple[list[dict], list[list[str]], int]:
    """端點資料夾每條 Rule 的內容與它的步驟（含 feature 的 Background）對到的 dsl.md 句型與帶入的參數值；另回傳每個句型被帶入過的所有參數值與沒對到任何句型的步驟數。"""
    cache: dict[str, list[tuple[int, list[str]]]] = {}
    values_by_row: list[list[str]] = [[] for _ in rows]
    unmatched = 0
    units: list[dict] = []
    for feature in sorted(folder.glob("*.feature")):
        preamble, found = read_units(feature)
        key = f"{folder.name}/{feature.name}"
        head_steps = steps_of(preamble)
        head_text = "\n".join(preamble)
        for unit in found:
            usages: list[tuple[int, list[str]]] = []
            for step in head_steps + steps_of(unit["lines"]):
                if step not in cache:
                    cache[step] = [(index, [value.strip('"') for value in matched.groups()])
                                   for index, row in enumerate(rows) if (matched := row["regex"].match(step))]
                    if not cache[step]:
                        unmatched += 1
                usages += cache[step]
            for index, values in usages:
                values_by_row[index] += [value for value in values if value not in values_by_row[index]]
            units.append({"key": key, "name": unit["name"], "line": unit["line"], "own": head_text + "\n" + "\n".join(unit["lines"]),
                          "usages": usages, "rows": {index for index, _ in usages}})
    return units, values_by_row, unmatched


def code_hit(unit: dict, code: str, rows: list[dict], values_by_row: list[list[str]]) -> bool:
    """Rule 自己的內容提到這個 code，或它用到的句型提到這個 code：句型中 code 所在的子句寫了某個參數值時（如「請輸入訊息內容對應 422 `chat_empty`」），只有帶入那個值的用法才算驗到。"""
    if contains_token(unit["own"], code):
        return True
    for index, values in unit["usages"]:
        text = rows[index]["text"]
        if not contains_token(text, code):
            continue
        clauses = [clause for clause in CLAUSE_SPLIT_PATTERN.split(text) if contains_token(clause, code)]
        bound = [value for value in values_by_row[index] if len(value) >= 2 and any(value in clause for clause in clauses)]
        if not bound or any(value in bound for value in values):
            return True
    return False


def response_hit(unit: dict, response: dict, rows: list[dict], values_by_row: list[list[str]]) -> bool:
    """呼叫端已確認 Rule 操作了這個 operation：有錯誤碼的回應看錯誤碼，2xx 隨 operation 算驗到，其他沒有錯誤碼的回應看狀態碼有沒有被提到。"""
    if response["codes"]:
        return any(code_hit(unit, code, rows, values_by_row) for code in response["codes"])
    if response["status"].startswith("2"):
        return True
    return contains_token(unit["own"], response["status"]) or any(contains_token(rows[index]["text"], response["status"]) for index in unit["rows"])


def link_sections(sections: list[dict], phases: list[dict], tasks: list[dict], truth_dir: Path, feature_endpoints: list[dict],
                  scope_names: dict[str, set[str]]) -> dict[str, dict]:
    """為每個段落寫入 anchored_by；這次異動的主要段落另寫入 rule_count、scoped_rules 與 tasks（以操作或查證它的 Rule 為準），operation 的每個回應與錯誤碼亦同。回傳各端點資料夾的 Rule 與句型。"""
    phase_by_number = {phase["number"]: phase for phase in phases}
    folder_by_prefix = {endpoint["prefix"]: endpoint["folder"] for endpoint in feature_endpoints}
    folders: dict[str, dict] = {}
    for endpoint in feature_endpoints:
        folder = truth_dir / "features" / endpoint["folder"]
        rows = read_dsl_rows(folder / "dsl.md")
        units, values_by_row, unmatched = endpoint_units(folder, rows) if folder.is_dir() else ([], [], 0)
        folders[endpoint["folder"]] = {"rows": rows, "units": units, "values": values_by_row}
        if unmatched:
            print(f"警告：{endpoint['folder']} 有 {unmatched} 個步驟沒有對到 dsl.md 的句型，這些步驟只以字面比對段落", file=sys.stderr)
    for section in sections:
        anchored = set()
        for task in tasks:
            anchors = task["anchors"] + phase_by_number[task["phase"]]["anchors"]
            if any(anchor_matches(section, anchor) for anchor in anchors):
                anchored.add(task["id"])
        section["anchored_by"] = sorted(anchored)
        if not section["changed"] or not is_main(section):
            continue
        data = folders.get(folder_by_prefix.get(section["prefix"], ""), {"rows": [], "units": [], "values": []})
        row_hits = {index for index, row in enumerate(data["rows"]) if section_hit(section, row["text"])}
        hit_units = [unit for unit in data["units"] if (unit["rows"] & row_hits) or section_hit(section, unit["own"])]
        scoped = [unit for unit in hit_units if unit["name"] in scope_names.get(unit["key"], set())]
        section["rule_count"] = len(hit_units)
        section["scoped_rule_count"] = len(scoped)
        section["scoped_rules"] = [f"{unit['key']} › {unit['name']}" for unit in scoped[:LISTED_RULES]]
        hit_keys = {(unit["key"], unit["name"]) for unit in hit_units}
        section["tasks"] = sorted(anchored | {task["id"] for task in tasks if task["scope_feature"] and any(
            (f"{task['scope_endpoint']}/{task['scope_feature']}", name) in hit_keys for name in task["scoped_rules"])})
        for response in section.get("responses", []):
            hits = [unit for unit in hit_units if response_hit(unit, response, data["rows"], data["values"])]
            in_scope = [unit for unit in hits if unit["name"] in scope_names.get(unit["key"], set())]
            response["rule_count"] = len(hits)
            response["scoped_rule_count"] = len(in_scope)
            response["scoped_rules"] = [f"{unit['key']} › {unit['name']}" for unit in in_scope[:LISTED_RESPONSE_RULES]]
            per_code = []
            for code in response["codes"]:
                code_units = [unit for unit in hits if code_hit(unit, code, data["rows"], data["values"])]
                per_code.append({"code": code, "rule_count": len(code_units),
                                 "scoped_rule_count": sum(1 for unit in code_units if unit["name"] in scope_names.get(unit["key"], set()))})
            response["codes"] = per_code
    return folders


def scoped_rules(task: dict, scope_by_key: dict[str, dict]) -> set[str]:
    """任務範疇內的 Rule：以 Rule 名稱定位的範疇（修正 Phase、[重跑]）取那些 Rule；行號範疇只取那些行的 Rule，整份 feature 取這次全部的 Rule。"""
    if not task["scope_feature"]:
        return set()
    if task["scope_rule_names"]:
        return set(task["scope_rule_names"])
    feature = scope_by_key.get(f"{task['scope_endpoint']}/{task['scope_feature']}")
    if feature is None:
        return set()
    rules = feature["rules"]
    if task["scope_lines"]:
        return {rule["name"] for rule in rules if rule["line"] in task["scope_lines"]}
    return {rule["name"] for rule in rules}


def trace_tasks(tasks: list[dict], phases: list[dict], acceptance: dict, ac_rows: list[dict], supplement_rows: list[dict],
                scope_by_key: dict[str, dict]) -> None:
    phase_by_number = {phase["number"]: phase for phase in phases}
    for task in tasks:
        phase = phase_by_number[task["phase"]]
        key = f"{task['scope_endpoint']}/{task['scope_feature']}" if task["scope_feature"] else None
        names = scoped_rules(task, scope_by_key)
        acs, via_ac, via_supplement = [], [], []
        if key:
            for row in ac_rows:
                if row["key"] == key and row["change"] in WORK_CHANGES and row["rule"] in names:
                    for ac in row["ac"]:
                        if ac not in acs:
                            acs.append(ac)
                        via_ac += [req for req in acceptance.get(ac, {}).get("requirements", []) if req not in via_ac]
            for row in supplement_rows:
                if row["key"] == key and row["change"] in WORK_CHANGES and row["rule"] in names:
                    via_supplement += [req for req in row["requirements"] if req not in via_supplement]
        constraint = sorted(set(task["nfr_constraints"]) | set(phase["nfr_constraints"]))
        direct = sorted(set(task["body_requirements"]) | {req for anchor in task["anchors"] for req in anchor["requirements"]})
        task["scoped_rules"] = sorted(names)
        task["acceptance"] = acs
        task["finding_acs"] = [ac for ac in acs if acceptance.get(ac, {}).get("finding")]
        task["requirement_sources"] = {"via_ac": via_ac, "via_supplement": via_supplement, "via_constraint": constraint, "direct": direct}
        del task["body_requirements"]


def link_tasks(tasks: list[dict], sections: list[dict]) -> None:
    """任務操作或查證（範疇內這次的 Rule）與必讀指向的這次異動的主要段落，以及由這些段落的標題得知的介面 ID。"""
    for task in tasks:
        touched = [section for section in sections if section["changed"] and task["id"] in section.get("tasks", [])]
        task["sections"] = sorted({f"{section['doc']} › {section['name']}" for section in touched if is_main(section)})
        task["interfaces"] = sorted({section["interface"] for section in touched if section.get("interface")})


def existing_coverage(acceptance: dict, ac_rows: list[dict], supplement_rows: list[dict]) -> dict[str, list[dict]]:
    """涵蓋表中異動為「無」的列：需求已由既有 Rule 驗證，不需要任務。"""
    covered: dict[str, list[dict]] = {}
    for row in ac_rows:
        if row["change"] != "無":
            continue
        for ac in row["ac"]:
            for req in acceptance.get(ac, {}).get("requirements", []):
                entry = {"feature": row["key"], "rule": row["rule"], "via": ac}
                if entry not in covered.setdefault(req, []):
                    covered[req].append(entry)
    for row in supplement_rows:
        if row["change"] != "無":
            continue
        for req in row["requirements"]:
            entry = {"feature": row["key"], "rule": row["rule"], "via": "補充案例"}
            if entry not in covered.setdefault(req, []):
                covered[req].append(entry)
    return covered


def requirement_stories(requirement: dict, acceptance: dict) -> list[str]:
    """需求所屬的故事：定義它的故事，加上涵蓋註解列出它的 AC 所屬的故事。"""
    found = [requirement["story"]] if requirement.get("story") else []
    for item in acceptance.values():
        if requirement["id"] in item["requirements"]:
            found += [story for story in item["stories"] if story not in found]
    return sorted(found, key=lambda story: int(story[2:]))


def trace_requirements(requirements: list[dict], stories: list[dict], inventory: list[dict], tasks: list[dict], interface_trace: list[dict],
                       covered: dict[str, list[dict]], acceptance: dict) -> list[dict]:
    priority_of = {story["id"]: story["priority"] for story in stories}
    interface_by_id = {item["id"]: item for item in interface_trace}
    traces = []
    for requirement in requirements:
        rid = requirement["id"]
        interfaces = [row["id"] for row in inventory if rid in row["requirement_ids"]]
        owned = requirement_stories(requirement, acceptance)
        priorities = sorted((priority_of[story] for story in owned if story in priority_of), key=lambda value: int(value[1:]))
        entry = {"id": rid, "stories": owned, "priority": priorities[0] if priorities else None, "interfaces": interfaces}
        for source in ("via_ac", "via_supplement", "via_constraint", "direct"):
            entry[source] = [task["id"] for task in tasks if rid in task["requirement_sources"][source]]
        mapped = [interface_by_id[item] for item in interfaces if item in interface_by_id and interface_by_id[item]["mapped"]]
        entry["via_interface"] = sorted({task_id for item in mapped for task_id in item["tasks"]})
        entry["unmapped_interfaces"] = [item for item in interfaces if item in interface_by_id and not interface_by_id[item]["mapped"]]
        entry["existing_rules"] = covered.get(rid, [])
        traces.append(entry)
    return traces


def trace_interfaces(inventory: list[dict], sections: list[dict]) -> list[dict]:
    """介面的 tasks 是標題以它的介面 ID 開頭的段落（含子段落）的負責任務；mapped 為 False 的介面（operation、Table 等沒有介面 ID 的段落）要依描述對應到段落。"""
    traces = []
    for row in inventory:
        checked = row["change"] in WORK_CHANGES or not row["change"]
        owned = [section for section in sections if section["changed"] and section.get("interface") == row["id"]]
        traces.append({
            "id": row["id"],
            "prefix": row["prefix"],
            "change": row["change"],
            "checked": checked,
            "mapped": bool(owned),
            "tasks": sorted({task_id for section in owned for task_id in section.get("tasks", [])}),
            "id_sections": [
                {"doc": section["file"], "name": section["name"], "anchored_by": section["anchored_by"],
                 "rule_count": section.get("rule_count", 0), "scoped_rule_count": section.get("scoped_rule_count", 0), "tasks": section.get("tasks", [])}
                for section in sections
                if checked and section["kind"].startswith("h") and section["name"].startswith(row["id"] + " ")
            ],
        })
    return traces


def shared_codes(endpoints: list[dict], truth_dir: Path, routes: dict[str, str], folders: dict[str, dict], folder_by_prefix: dict[str, str]) -> list[dict]:
    """同一個錯誤碼出現在本端點兩個以上 operation 的回應時列出：用到它的 operation 與狀態碼，以及本端點有沒有任何 Rule 驗到它。"""
    result = []
    for endpoint in endpoints:
        if endpoint["record"] == "plan" or not endpoint["doc_root"]:
            continue
        used: dict[str, dict[str, set[str]]] = {}
        for doc_root in re.split(r"[、,，]", endpoint["doc_root"]):
            base = truth_dir / doc_root.strip()
            files = sorted(path for path in base.rglob("*") if path.suffix in {".yaml", ".yml"}) if base.is_dir() else ([base] if base.is_file() else [])
            for path in files:
                short = path.resolve().relative_to(truth_dir.resolve()).as_posix()
                if (short == ENTRY_CONTRACT and routes) or "components" in short.split("/")[:-2]:
                    continue
                for operation in yaml_operations(path.read_text(encoding="utf-8").splitlines(), routes.get(short)):
                    for response in operation["responses"]:
                        for code in response["codes"]:
                            item = used.setdefault(code, {"operations": set(), "statuses": set()})
                            item["operations"].add(operation["name"])
                            item["statuses"].add(response["status"])
        data = folders.get(folder_by_prefix.get(endpoint["prefix"], ""), {"rows": [], "units": [], "values": []})
        for code, item in sorted(used.items()):
            if len(item["operations"]) < 2:
                continue
            hits = [unit for unit in data["units"] if code_hit(unit, code, data["rows"], data["values"])]
            result.append({"prefix": endpoint["prefix"], "code": code, "statuses": sorted(item["statuses"]), "operations": sorted(item["operations"]),
                           "rule_count": len(hits), "rules": [f"{unit['key']} › {unit['name']}" for unit in hits[:LISTED_RESPONSE_RULES]]})
    return result


def nfr_landing(requirements: list[dict], requirement_trace: list[dict], phases: list[dict], tasks: list[dict], verified: set[str]) -> list[dict]:
    no_task = {}
    constraint_by_phase = {phase["number"]: set(phase["nfr_constraints"]) for phase in phases}
    for task in tasks:
        constraint_by_phase.setdefault(task["phase"], set()).update(task["nfr_constraints"])
    for phase in phases:
        for entry in phase["no_task"]:
            for rid in entry["requirements"]:
                no_task[rid] = {
                    "line": entry["line"],
                    "reason": entry["reason"],
                    "phase_checks": [
                        {"phase": number, "in_constraint": rid in constraint_by_phase.get(number, set())}
                        for number in entry["phases_mentioned"]
                    ],
                }
    trace_by_id = {trace["id"]: trace for trace in requirement_trace}
    kind_by_task = {task["id"]: task["phase_kind"] for task in tasks}
    landing = []
    for requirement in requirements:
        if requirement["kind"] != "NFR":
            continue
        trace = trace_by_id[requirement["id"]]
        landing.append({
            "id": requirement["id"],
            "verified_by_rule": requirement["id"] in verified,
            "constraint_tasks": trace["via_constraint"],
            "refactor_tasks": [task_id for task_id in trace["direct"] if kind_by_task.get(task_id) == "nfr_refactor"],
            "no_task_entry": no_task.get(requirement["id"]),
        })
    return landing


def module_rows(lines: list[str]) -> list[dict]:
    """取出用語表「## 模組」底下第一張表格的列。"""
    rows, header, in_section = [], [], False
    for line in lines:
        if line.startswith("#"):
            if in_section and header:
                break
            in_section = line.strip() == "## 模組"
            continue
        text = line.strip()
        if not in_section or not text.startswith("|"):
            if in_section and header and text:
                break
            continue
        if re.fullmatch(r"\|[\s:|-]+\|?", text):
            continue
        cells = [cell.strip() for cell in text.strip("|").split("|")]
        if not header:
            header = cells
            continue
        rows.append(dict(zip(header, cells)))
    return rows


def read_modules(truth_dir: Path, base_glossary: str) -> dict[str, list[str]]:
    """truth 用語表「模組」表：每個模組的 feature（`端點/檔名.feature`），並加上基準時的模組表，讓這次刪除的 feature 仍對得到模組。"""
    modules: dict[str, list[str]] = {}
    glossary = truth_dir / GLOSSARY
    sources = [glossary.read_text(encoding="utf-8").splitlines()] if glossary.is_file() else []
    sources.append(base_glossary.splitlines())
    for lines in sources:
        for row in module_rows(lines):
            name = strip_code(row.get("模組", ""))
            listed = re.split(r"[（(]", row.get("feature", ""), maxsplit=1)[0]
            for item in re.split(r"[、,，]", listed):
                key = f"{item.strip().strip('`')}.feature"
                if "/" in item and key not in modules.setdefault(name, []):
                    modules[name].append(key)
    return modules


def trace_affected(affected: list[dict], modules: dict[str, list[str]], sections: list[dict], ac_rows: list[dict], supplement_rows: list[dict]) -> list[dict]:
    """「受影響的既有功能」的每一項：在 truth-changes.md 與涵蓋表中找到的修改或刪除。"""
    results = []
    for item in affected:
        features = modules.get(item["name"])
        prefixes = [f"features/{key}" for key in features or []] + [f"contracts/paths/{item['name']}/", f"data/{item['name']}.dbml"]
        changes = []
        for section in sections:
            for row in section["rows"]:
                if row["type"] not in {"ADD", "MOD", "DEL"}:
                    continue
                if any(file.startswith(prefix) for file in row["files"] for prefix in prefixes):
                    changes.append({"source": "truth-changes.md", "owner": section["owner"], "type": row["type"], "target": row["target"], "line": row["line"]})
        for row in ac_rows + supplement_rows:
            if row["change"] in WORK_CHANGES and features and row["key"] in features:
                changes.append({"source": "涵蓋表", "type": row["change"], "target": f"{row['key']} › {row['rule']}", "line": row["line"]})
        results.append({**item, "module_found": features is not None, "features": features or [], "changes": changes})
    return results


def public_section(section: dict) -> dict:
    """輸出用的段落：這次異動的主要段落列出全部欄位（回應去掉比對用的全文）；其他段落只列定位與必讀，不檢查涵蓋。"""
    if not section["changed"] or not is_main(section):
        brief = {key: section[key] for key in ("file", "kind", "name", "line", "changed", "anchored_by")}
        if section.get("interface"):
            brief["interface"] = section["interface"]
        return brief
    result = {key: value for key, value in section.items() if key not in {"match", "block", "doc"}}
    if "responses" in result:
        result["responses"] = [{key: value for key, value in response.items() if key != "text"} for response in result["responses"]]
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="解析進行中的 plan 與 specs/truth/，只追溯這個 plan 的異動，輸出需求（含所屬故事與優先順序）、受影響的既有功能、介面、介面文檔段落（含 operation 的每個回應）、Rule 與任務之間的追溯 JSON；段落與任務以操作或查證它的 Rule 對應，不以介面 ID 前綴推定。")
    parser.add_argument("plan_dir", help="進行中的 plan 資料夾路徑，例如 specs/plans/004-ranking")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    plan_dir = Path(args.plan_dir)
    truth_dir = plan_dir.resolve().parent.parent / "truth"
    if not plan_dir.is_dir() or plan_dir.resolve().parent.name != "plans" or not truth_dir.is_dir():
        print(f"錯誤：{plan_dir} 不是 <specs>/plans/<plan 資料夾>，或找不到 <specs>/truth/；請傳入 plan 資料夾，例如 specs/plans/004-ranking。", file=sys.stderr)
        return 1
    needed = [plan_dir / "spec.md", plan_dir / "plan.md", plan_dir / "tasks.md", plan_dir / COVERAGE, truth_dir / GLOSSARY]
    missing = [display_path(path, project_root(plan_dir)) for path in needed if not path.is_file()]
    if missing:
        print(f"錯誤：缺少 {'、'.join(missing)}，請先執行 collect_artifacts.py 確認必要產物齊全後再建立追溯模型。", file=sys.stderr)
        return 1
    try:
        context = load_context(str(plan_dir))
    except Abort as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1
    if context["changes"] is None:
        print(f"錯誤：{context['plan']} 的狀態是「{context['status'] or '未知'}」，不是進行中的 plan；已交付的 plan 唯讀，不做分析。"
              "請改為指定進行中的 plan，要開始新的迭代時以 /specify 開立新的 plan。", file=sys.stderr)
        return 1
    summary, problems = summarize(plan_dir)
    if summary is None:
        print("錯誤：無法取得這次的異動範圍：" + "；".join(item["message"] for item in problems), file=sys.stderr)
        return 1

    def show_base(relative: str) -> str | None:
        try:
            return git(context["root"], "show", f"{context['base']}:{context['truth_rel']}/{relative}")
        except Abort:
            return None

    requirements, stories, affected = read_spec(plan_dir / "spec.md")
    inventory = read_inventory(plan_dir / "plan.md")
    for row in inventory:
        row["requirement_ids"] = expand_ids(row["requirements"], REQUIREMENT_KINDS)
        row["finding_acs"] = AC_PATTERN.findall(row["requirements"])  # 依據需求引用的本 plan @開發發現 AC
        technical = TECHNICAL_BASIS_PATTERN.search(row["requirements"])
        row["technical"] = technical.group(1).strip() if technical else None  # 只因 PM 看不到差異的技術原因而異動
    feature_endpoints = read_feature_endpoints(truth_dir)
    folder_by_prefix = {endpoint["prefix"]: endpoint["folder"] for endpoint in feature_endpoints}
    records = read_truth_changes(plan_dir, truth_dir)
    endpoints = collect_endpoints(plan_dir, truth_dir, inventory, records)
    routes = read_routes(truth_dir)
    sections, unindexed_docs = index_docs(plan_dir, truth_dir, endpoints, routes, show_base)
    acceptance = read_acceptance(plan_dir)
    ac_rows, supplement_rows = read_coverage(plan_dir)
    scope_by_key = {feature["key"]: feature for feature in summary["features"]}
    scope_names = {key: {rule["name"] for rule in feature.get("rules", [])} for key, feature in scope_by_key.items()}
    phases, tasks = read_tasks(plan_dir / "tasks.md")
    trace_tasks(tasks, phases, acceptance, ac_rows, supplement_rows, scope_by_key)
    folders = link_sections(sections, phases, tasks, truth_dir, feature_endpoints, scope_names)
    link_tasks(tasks, sections)
    covered = existing_coverage(acceptance, ac_rows, supplement_rows)
    interface_trace = trace_interfaces(inventory, sections)
    requirement_trace = trace_requirements(requirements, stories, inventory, tasks, interface_trace, covered, acceptance)
    changed_sections = [section for section in sections if section["changed"]]
    print(f"需求 {len(requirements)}、介面 {len(inventory)}、這次異動的文檔段落 {len(changed_sections)}／{len(sections)}、"
          f"這次異動的 feature {len(scope_by_key)}、Phase {len(phases)}、任務 {len(tasks)}", file=sys.stderr)
    result = {
        "plan": summary["plan"],
        "requirements": requirements,
        "stories": stories,
        "affected_functions": trace_affected(affected, read_modules(truth_dir, base_text_of(context)), records, ac_rows, supplement_rows),
        "interfaces": inventory,
        "feature_endpoints": [{"prefix": endpoint["prefix"], "folder": endpoint["folder"]} for endpoint in feature_endpoints],
        "acceptance": acceptance,
        "acceptance_without_coverage": [
            {"ac": ac, "file": item["file"], "line": item["line"], "finding": item["finding"]}
            for ac, item in acceptance.items()
            if not any(ac in row["ac"] for row in ac_rows)
        ],
        "scope_features": [{key: feature.get(key) for key in ("key", "status", "scope", "acceptance", "requirements", "rules", "deleted_rules")} for feature in summary["features"]],
        "removed_features": summary.get("removed_features", []),
        "deleted_docs": [{"prefix": endpoint["prefix"], "planner": endpoint["planner"], "files": endpoint["deleted_docs"]} for endpoint in endpoints if endpoint["deleted_docs"]],
        "doc_sections": [public_section(section) for section in sections],
        "shared_codes": shared_codes(endpoints, truth_dir, routes, folders, folder_by_prefix),
        "phases": phases,
        "tasks": [{**{key: value for key, value in task.items() if key != "sections"}, "section_count": len(task["sections"])} for task in tasks],
        "requirement_trace": requirement_trace,
        "interface_trace": interface_trace,
        "nfr_landing": nfr_landing(requirements, requirement_trace, phases, tasks, set(summary.get("verified_nfrs", []))),
        "unanchored_sections": [
            {"doc": section["file"], "prefix": section["prefix"], "kind": section["kind"], "name": section["name"], "line": section["line"]}
            for section in changed_sections
            if is_main(section) and not section["anchored_by"] and not section.get("rule_count")
        ],
        "unindexed_docs": unindexed_docs,
        "tasks_without_requirement": [
            {"id": task["id"], "phase": task["phase"], "phase_kind": task["phase_kind"]}
            for task in tasks
            if task["phase_kind"] not in SUPPORT_KINDS and task["stage"] != "重跑" and (
                (task["phase_kind"] == "feature" and not task["requirement_sources"]["via_ac"] and not task["requirement_sources"]["via_supplement"] and not task["finding_acs"])
                or (task["phase_kind"] != "feature" and not any(task["requirement_sources"].values()) and not task["sections"]))
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def base_text_of(context: dict) -> str:
    """基準 commit 時的 truth 用語表；取不到時回傳空字串。"""
    if not context.get("base"):
        return ""
    try:
        return git(context["root"], "show", f"{context['base']}:{context['truth_rel']}/{GLOSSARY}")
    except (Abort, OSError):
        return ""


if __name__ == "__main__":
    sys.exit(main())
