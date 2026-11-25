# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""檢查 specs/truth/techstack.md：研究紀錄欄的編號是否寫成 <plan>/R-xx 並存在於該 plan 的 research.md、技術類型是否合法、套件版本是否與這一列引用的 plan 中編號最大且寫到該套件的 research.md 一致、套件安裝清單與技術層級表格是否一致、技術層級表格是否重述了家在介面文檔或程式的識別碼（API 路徑、畫面路由、原始碼檔案與目錄、遷移版本、hook、函式、資料表、欄位、事件與設定變數的名稱），以及殘留樣板內容；以 --plan 指定這次的 plan 時，另檢查它的決策寫到的套件都已收錄。有問題時以 exit code 1 結束。"""

import argparse
import sys
import json
import re
from pathlib import Path

DECISION_PATTERN = re.compile(r"^## R-(\d{2}) ")
FIELD_PATTERN = re.compile(r"^- \*\*([^*]+)\*\*[：:]")
PACKAGE_PATTERN = re.compile(r"`(@?[^`@\s]+)@([^`\s]+)`")
PACKAGE_NAME_PATTERN = re.compile(r"`([^`]+)`")
DECISION_REF_PATTERN = re.compile(r"(?:(?<!\d)(\d{3})/)?(?<![A-Z-])R-(\d{2})(?!\d)")
PLAN_DIR_PATTERN = re.compile(r"^(\d{3})-")
LEFTOVER_PATTERN = re.compile(r"\{\{[^}]*\}\}|<!-- 重複(開始|結束)")
DIVIDER_PATTERN = re.compile(r"^\|[\s|:-]+\|$")
TECH_TYPES = ("套件", "內建", "自行實作")
RESEARCH_FILE = "research.md"

# 技術層級表格只寫技術與模組；以下是能機械辨識、家在介面文檔或程式的識別碼。元件與類別名稱、沒有底線的資料表名稱與數值無法可靠辨識，由撰寫者依技術堆疊撰寫規範判斷。
CODE_SPAN_PATTERN = re.compile(r"`([^`]+)`")
HTTP_ROUTE_PATTERN = re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/\S*")
MIGRATION_PATTERN = re.compile(r"^\d{3,}_\w+$")
HOOK_PATTERN = re.compile(r"^use[A-Z][A-Za-z0-9]*$")
SNAKE_PATTERN = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$")
CONSTANT_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)+$")
SOURCE_SUFFIXES = (".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".py", ".css", ".scss", ".less", ".html", ".vue",
                   ".svelte", ".sql", ".go", ".rs", ".java", ".kt", ".rb", ".php", ".cs", ".swift")
FRAMEWORK_HOOKS = {"useState", "useEffect", "useLayoutEffect", "useInsertionEffect", "useContext", "useReducer",
                   "useCallback", "useMemo", "useRef", "useImperativeHandle", "useDebugValue", "useDeferredValue",
                   "useTransition", "useId", "useSyncExternalStore", "useOptimistic", "useActionState", "useFormStatus"}
RESTATED_KINDS = {
    "api": ("API 路徑", "API 路徑以契約為準"),
    "route": ("畫面路由", "畫面路由以 UI 契約為準"),
    "file": ("原始碼檔案或目錄", "原始碼的檔案與目錄由程式決定"),
    "migration": ("遷移版本", "遷移版本由程式決定"),
    "hook": ("hook 名稱", "元件與 hook 的名稱由程式決定"),
    "identifier": ("程式或介面文檔的識別碼", "函式、變數、資料表、欄位與事件的名稱以程式與介面文檔為準"),
    "constant": ("設定變數", "設定變數的名稱由程式決定"),
}
RESTATED_COLUMNS = ("項目", "技術")


def read_research(lines: list[str]) -> tuple[set[int], dict[str, str]]:
    """只收集每個 R 區塊「決策」欄位（到同層下一個欄位或下一個 H2 為止）中的套件；理由、替代方案等欄位不算採用的技術。"""
    decisions = set()
    packages = {}
    in_decision = False
    for line in lines:
        decision = DECISION_PATTERN.match(line)
        if decision:
            decisions.add(int(decision.group(1)))
            in_decision = False
            continue
        if line.startswith("## "):
            in_decision = False
            continue
        if field := FIELD_PATTERN.match(line):
            in_decision = field.group(1) == "決策"
        if in_decision:
            for name, version in PACKAGE_PATTERN.findall(line):
                packages[name] = version
    return decisions, packages


def load_plans(plans_dir: Path) -> dict[str, dict]:
    """讀取每個 plan 的 research.md，鍵為 plan 資料夾名稱開頭的三位數編號。"""
    plans = {}
    for folder in sorted(plans_dir.iterdir()):
        match = PLAN_DIR_PATTERN.match(folder.name)
        research = folder / RESEARCH_FILE
        if not folder.is_dir() or not match or not research.is_file():
            continue
        decisions, packages = read_research(research.read_text(encoding="utf-8").splitlines())
        plans[match.group(1)] = {"name": folder.name, "decisions": decisions, "packages": packages}
    return plans


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def read_tables(lines: list[str]) -> list[dict]:
    tables = []
    index = 0
    while index < len(lines) - 1:
        line = lines[index].strip()
        if line.startswith("|") and DIVIDER_PATTERN.match(lines[index + 1].strip()):
            table = {"header": split_row(line), "rows": []}
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                table["rows"].append((index + 1, split_row(lines[index])))
                index += 1
            tables.append(table)
            continue
        index += 1
    return tables


def check_row_refs(line_no: int, cells: dict, plans: dict[str, dict]) -> tuple[list[dict], list[str]]:
    """回傳問題與這一列有效引用的 plan 編號。"""
    problems = []
    referenced = []
    refs = DECISION_REF_PATTERN.findall(cells["研究紀錄"])
    if not refs:
        problems.append({
            "type": "reference",
            "line": line_no,
            "message": f"「{cells.get('技術', '')}」缺少研究紀錄的編號，請填入選用此技術的決策，寫成 <plan>/R-xx，例如 004/R-03。",
        })
    for plan, number in refs:
        if not plan:
            problems.append({
                "type": "reference",
                "line": line_no,
                "message": f"R-{number} 沒有 plan 前綴，請寫成 <plan>/R-{number}（plan 是 plan 資料夾名稱開頭的三位數，例如 004/R-{number}）。",
            })
        elif plan not in plans:
            problems.append({
                "type": "reference",
                "line": line_no,
                "message": f"引用的 {plan}/R-{number} 找不到對應的 research.md；請確認 specs/plans/ 底下有編號 {plan} 的 plan 且已產出 research.md。",
            })
        elif int(number) not in plans[plan]["decisions"]:
            problems.append({
                "type": "reference",
                "line": line_no,
                "message": f"引用的 {plan}/R-{number} 不存在於 {plans[plan]['name']}/research.md，請改為該 research.md 已有的決策編號。",
            })
        else:
            referenced.append(plan)
    return problems, referenced


def check_package_row(line_no: int, cells: dict, plans: dict[str, dict], referenced: list[str]) -> tuple[list[dict], str | None]:
    name_match = PACKAGE_NAME_PATTERN.search(cells["技術"])
    if not name_match:
        return [{
            "type": "package",
            "line": line_no,
            "message": "類型為「套件」的列，技術欄必須以反引號寫出套件名稱，例如 `mysql2`。",
        }], None
    name = name_match.group(1)
    sources = [plan for plan in sorted(set(referenced), reverse=True) if name in plans[plan]["packages"]]
    if not sources:
        return [{
            "type": "package",
            "line": line_no,
            "message": f"套件 `{name}` 未在這一列引用的 research.md 中以 `{name}@版本範圍` 決策；請在研究紀錄欄補上決定它的編號，或先在這次的 research.md 補上決策。",
        }], name
    expected = plans[sources[0]]["packages"][name]
    if cells["版本"] != expected:
        return [{
            "type": "version",
            "line": line_no,
            "message": f"套件 `{name}` 的版本為 {cells['版本']}，與 {plans[sources[0]]['name']}/research.md 的 {expected} 不一致；多個 plan 寫到同一個套件時以編號最大的為準，請照抄它的版本範圍。",
        }], name
    return [], name


def classify_span(token: str) -> str | None:
    """判斷反引號內的一段文字是不是家在介面文檔或程式的識別碼，回傳 RESTATED_KINDS 的鍵。"""
    token = token.strip()
    if HTTP_ROUTE_PATTERN.search(token) or token.startswith("/"):
        return "api"
    if token.startswith("#/"):
        return "route"
    if " " not in token and (token.endswith("/") or token.lower().endswith(SOURCE_SUFFIXES)):
        return "file"
    if MIGRATION_PATTERN.match(token):
        return "migration"
    if HOOK_PATTERN.match(token) and token not in FRAMEWORK_HOOKS:
        return "hook"
    if CONSTANT_PATTERN.match(token):
        return "constant"
    if SNAKE_PATTERN.match(token):
        return "identifier"
    return None


def check_restated(line_no: int, cells: dict) -> list[dict]:
    """技術層級表格的項目欄與技術欄不得重述 API 路徑、畫面路由、原始碼檔案、遷移版本與程式中的名稱；套件列的第一段反引號是套件名稱，不檢查。"""
    problems = []
    for column in RESTATED_COLUMNS:
        text = cells.get(column, "")
        spans = CODE_SPAN_PATTERN.findall(text)
        if column == "技術" and cells.get("類型") == "套件":
            spans = spans[1:]
        found: dict[str, list[str]] = {}
        for span in spans:
            kind = classify_span(span)
            if kind:
                found.setdefault(kind, []).append(f"`{span.strip()}`")
        outside = CODE_SPAN_PATTERN.sub("", text)
        for route in HTTP_ROUTE_PATTERN.findall(outside):
            found.setdefault("api", []).append(route)
        if not found:
            continue
        restated = "、".join(f"{RESTATED_KINDS[kind][0]} {'、'.join(tokens)}" for kind, tokens in found.items())
        homes = "，".join(RESTATED_KINDS[kind][1] for kind in found)
        problems.append({
            "type": "restated",
            "line": line_no,
            "message": f"「{cells.get('項目', '')}」的{column}欄重述了以下內容：{restated}。techstack.md 只寫技術與模組，{homes}；請刪去這些內容，類型為自行實作的列依研究紀錄改寫成做法（例如「連線中斷後自動重連的 React hook」），只在列舉名稱、引用的決策也沒有寫出做法時才整列刪除；決策的細節經研究紀錄欄的編號回到 research.md 查閱。",
        })
    return problems


def check_techstack(lines: list[str], plans: dict[str, dict], current: str | None) -> list[dict]:
    problems = []
    for line_no, line in enumerate(lines, start=1):
        leftover = LEFTOVER_PATTERN.search(line)
        if leftover:
            problems.append({
                "type": "leftover",
                "line": line_no,
                "message": f"殘留樣板內容 {leftover.group(0)}，請填入實際內容或刪除該行。",
            })
    layer_versions: dict[str, str] = {}
    layer_lines: dict[str, int] = {}
    install_entries: list[tuple[int, str, str]] = []
    for table in read_tables(lines):
        header = table["header"]
        for line_no, row in table["rows"]:
            cells = dict(zip(header, row))
            referenced: list[str] = []
            if "研究紀錄" in cells:
                row_problems, referenced = check_row_refs(line_no, cells, plans)
                problems.extend(row_problems)
            if "類型" in cells:
                problems.extend(check_restated(line_no, cells))
                if cells["類型"] not in TECH_TYPES:
                    problems.append({
                        "type": "tech_type",
                        "line": line_no,
                        "message": f"類型「{cells['類型']}」不合法，只能填「套件」「內建」「自行實作」其中之一。",
                    })
                elif cells["類型"] == "套件":
                    row_problems, name = check_package_row(line_no, cells, plans, referenced)
                    problems.extend(row_problems)
                    if name:
                        layer_versions[name] = cells.get("版本", "")
                        layer_lines[name] = line_no
            if "套件與版本" in cells:
                install_entries.extend((line_no, name, version) for name, version in PACKAGE_PATTERN.findall(cells["套件與版本"]))
    installed = set()
    for line_no, name, version in install_entries:
        installed.add(name)
        if name not in layer_versions:
            problems.append({
                "type": "package",
                "line": line_no,
                "message": f"套件安裝清單的 `{name}` 沒有出現在任何技術層級表格；請補上一列類型為「套件」的技術，或從清單移除。",
            })
        elif version != layer_versions[name]:
            problems.append({
                "type": "version",
                "line": line_no,
                "related_line": layer_lines[name],
                "message": f"套件安裝清單的 `{name}@{version}` 與技術層級表格的版本 {layer_versions[name]} 不一致，請改為相同的版本範圍。",
            })
    for name in layer_versions:
        if name not in installed:
            problems.append({
                "type": "missing",
                "line": layer_lines[name],
                "message": f"技術層級表格的套件 `{name}` 沒有出現在套件安裝清單，請補到所屬 workspace 與相依類型的列。",
            })
    if current is not None:
        for name in plans[current]["packages"]:
            if name not in layer_versions:
                problems.append({
                    "type": "missing",
                    "line": None,
                    "message": f"{plans[current]['name']}/research.md 決策的套件 `{name}` 沒有出現在任何技術層級表格，請補上一列類型為「套件」的技術。",
                })
    return problems


def find_plan_folder(plans_dir: Path, wanted: str) -> Path | None:
    """以 plan 資料夾名稱、路徑或開頭的三位數編號找出 plan 資料夾，不要求它有 research.md。"""
    name = Path(wanted.replace("\\", "/").rstrip("/")).name
    match = PLAN_DIR_PATTERN.match(name + "-") if name.isdigit() else PLAN_DIR_PATTERN.match(name)
    if not match:
        return None
    for folder in sorted(plans_dir.iterdir()):
        found = PLAN_DIR_PATTERN.match(folder.name)
        if folder.is_dir() and found and found.group(1) == match.group(1):
            return folder
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查 techstack.md 的研究紀錄編號（<plan>/R-xx）、技術類型、套件版本與各 plan 的 research.md 是否一致、技術層級表格重述的識別碼，以及殘留佔位符；有問題時以 exit code 1 結束。")
    parser.add_argument("techstack_path", help="要檢查的 techstack.md 路徑，例如 specs/truth/techstack.md")
    parser.add_argument("--plans", help="plan 資料夾所在的目錄；省略時使用 techstack.md 上兩層的 plans/（specs/truth/techstack.md 對應 specs/plans/）")
    parser.add_argument("--plan", help="這次的 plan 資料夾名稱或編號，例如 004-ranking 或 004；它有 research.md 時另檢查決策寫到的套件都已收錄（技術修正 plan 沒有 research.md 時略過這項）")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    techstack_path = Path(args.techstack_path).resolve()
    if not techstack_path.is_file():
        print(f"錯誤：找不到 techstack.md 檔案 {techstack_path}。請傳入 techstack.md 的路徑，例如 specs/truth/techstack.md。", file=sys.stderr)
        return 1
    plans_dir = Path(args.plans).resolve() if args.plans else techstack_path.parent.parent / "plans"
    if not plans_dir.is_dir():
        print(f"錯誤：找不到 plan 資料夾所在的目錄 {plans_dir}。techstack.md 不在 specs/truth/ 底下時，請以 --plans 指定 specs/plans 的路徑。", file=sys.stderr)
        return 1
    plans = load_plans(plans_dir)
    current = None
    if args.plan:
        folder = find_plan_folder(plans_dir, args.plan)
        if folder is None:
            print(f"錯誤：--plan {args.plan} 在 {plans_dir} 底下找不到對應的 plan 資料夾。請傳入 plan 資料夾名稱或開頭的三位數編號，例如 004-ranking 或 004。", file=sys.stderr)
            return 1
        number = PLAN_DIR_PATTERN.match(folder.name).group(1)
        if number in plans:
            current = number
        else:
            print(f"{folder.name} 沒有 research.md（技術修正 plan 沒有研究決策時不寫），略過「這次決策的套件都已收錄」的檢查。", file=sys.stderr)
    problems = check_techstack(techstack_path.read_text(encoding="utf-8").splitlines(), plans, current)
    print(f"對照 {len(plans)} 個 plan 的 research.md，發現 {len(problems)} 個問題", file=sys.stderr)
    print(json.dumps({"ok": not problems, "plans": [plan["name"] for plan in plans.values()], "problems": problems}, ensure_ascii=False, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
