# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""盤點進行中的 plan 與 specs/truth/ 的必要產物、truth 用語表「端點」表登記的端點資料夾，並依 plan.md 介面盤點的介面 ID 前綴找出各端點的介面文檔：Planner 寫在 plan 資料夾的（UI 的 ui/）必須存在，寫進 specs/truth/ 的以 truth-changes.md 中該 Planner 一節列出的對象為準；
列出這次有新增或修改介面、plan 的涵蓋表卻沒有任何一列落在其端點資料夾的端點（dsl-refine 沒有為它產出這次的案例），以及 wave-report.md 中每個 Planner 的狀態與「不能改」一節；另輸出 check_tasks.py 的 `--own-doc` 參數值（端點資料夾=介面文檔的位置）。"""

import argparse
import json
import re
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SKILLS_DIR / "truth-changes" / "scripts"))
from truth_changes import NO_CHANGE, TYPES, parse_sections  # noqa: E402

PLAN_ARTIFACTS = [
    ("spec.md", "specify"),
    ("research.md", "technical-research"),
    ("plan.md", "system-analysis"),
    ("tasks.md", "task"),
    ("truth-changes.md", "specify"),
    ("features/acceptance/", "spec-by-example"),
    ("features/涵蓋表.md", "dsl-refine"),
]
TRUTH_ARTIFACTS = [
    ("techstack.md", "technical-research"),
    ("features/用語表.md", "dsl-refine"),
]
GLOSSARY = "features/用語表.md"
COVERAGE = "features/涵蓋表.md"
COVERAGE_HEADINGS = ("## AC 涵蓋表", "## 補充案例")
TRUTH_CHANGES = "truth-changes.md"
WAVE_REPORT = "wave-report.md"
BLOCKED_HEADING = "## 不能改"
DONE_STATUS = "完成"
# dsl-refine 把 AC 的動作分派到有行為的畫面與 API 端點；儲存端點（DB、FS 等）只接儲存結構與約束的案例，沒有這類案例時不產生端點資料夾
BEHAVIOR_PREFIXES = {"UI", "API"}
CASE_CHANGES = {"ADD", "MOD", ""}
ENDPOINT_HEADING = "## 端點"
INVENTORY_HEADING = "### 介面盤點"
PLANNER_BY_PREFIX = {"UI": "ui-ux-plan", "API": "api-plan", "DB": "data-plan", "FS": "storage-plan"}
PLAN_DOCS = {"ui-ux-plan": ("ui/", ["ui/ui-contract.md", "ui/prototype/"])}
ANCHOR_MARK = "＞"
TABLE_ROW_PATTERN = re.compile(r"^\|(.+)\|\s*$")
TABLE_SEPARATOR_PATTERN = re.compile(r"^\|[\s:|-]+\|\s*$")
INTERFACE_ID_PATTERN = re.compile(r"^([A-Z]+)-(\d+)$")


def read_table(path: Path, heading: str) -> list[dict]:
    """讀取 Markdown 檔中指定標題底下第一張表格，回傳以表頭為鍵、含行號的列。"""
    rows = []
    header: list[str] = []
    in_section = False
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith("#"):
            if in_section and header:
                break
            in_section = line.strip() == heading
            continue
        if not in_section:
            continue
        matched = TABLE_ROW_PATTERN.match(line)
        if not matched:
            if header and line.strip():
                break
            continue
        if TABLE_SEPARATOR_PATTERN.match(line):
            continue
        cells = [cell.strip() for cell in matched.group(1).split("|")]
        if not header:
            header = cells
            continue
        row = {name: (cells[index] if index < len(cells) else "") for index, name in enumerate(header)}
        row["line"] = line_no
        rows.append(row)
    return rows


def strip_code(text: str) -> str:
    return text.strip().strip("`").strip()


def project_root(plan_dir: Path) -> Path:
    return plan_dir.resolve().parent.parent.parent


def display_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root).as_posix()


def read_inventory(plan_path: Path) -> list[dict]:
    """依表頭讀取 plan.md「介面盤點」的每一列：介面 ID、介面、所屬端點、異動、依據需求。"""
    rows = []
    for row in read_table(plan_path, INVENTORY_HEADING):
        interface_id = strip_code(row.get("介面 ID", ""))
        matched = INTERFACE_ID_PATTERN.match(interface_id)
        if not matched:
            continue
        rows.append({
            "id": interface_id,
            "prefix": matched.group(1),
            "name": row.get("介面", "").strip(),
            "endpoint": row.get("所屬端點", "").strip(),
            "change": strip_code(row.get("異動", "")),
            "requirements": row.get("依據需求", "").strip(),
            "line": row["line"],
        })
    return rows


def read_feature_endpoints(truth_dir: Path) -> list[dict]:
    """讀取 truth 用語表「端點」表登記的介面前綴與端點資料夾，並確認資料夾含 dsl.md 與 feature。"""
    glossary = truth_dir / GLOSSARY
    if not glossary.is_file():
        return []
    endpoints = []
    for row in read_table(glossary, ENDPOINT_HEADING):
        prefix = strip_code(row.get("介面前綴", ""))
        folder = strip_code(row.get("資料夾", ""))
        if not prefix or not folder:
            continue
        path = truth_dir / "features" / folder
        features = sorted(child.name for child in path.glob("*.feature")) if path.is_dir() else []
        endpoints.append({
            "prefix": prefix,
            "folder": folder,
            "line": row["line"],
            "exists": path.is_dir(),
            "has_dsl": (path / "dsl.md").is_file(),
            "features": features,
        })
    return endpoints


def read_truth_changes(plan_dir: Path, truth_dir: Path) -> list[dict]:
    """解析 plan 的 truth-changes.md，每個「## owner（路徑）」一節；檔案不存在時回傳空清單。"""
    record = plan_dir / TRUTH_CHANGES
    if not record.is_file():
        return []
    truth_rel = display_path(truth_dir, project_root(plan_dir))
    sections, _ = parse_sections(record.read_text(encoding="utf-8"), truth_dir.resolve(), truth_rel)
    return sections


def required_exists(base: Path, name: str) -> bool:
    path = base / name
    if name.endswith("/"):
        return path.is_dir() and any(path.glob("*.feature"))
    return path.is_file()


def output_exists(base: Path, output: str) -> bool:
    path = base / output
    if output.endswith("/"):
        return path.is_dir() and any(path.iterdir())
    return path.is_file()


def anchor_of(target: str) -> str | None:
    """取出對象中「＞」之後的段落說明（例如 Table `rooms`）；整份檔案的對象回傳 None。"""
    if ANCHOR_MARK not in target:
        return None
    return target.split(ANCHOR_MARK, 1)[1].strip()


def truth_docs(section: dict, truth_dir: Path) -> tuple[list[dict], list[str]]:
    """把該 Planner 一節中異動為 ADD、MOD 的對象整理成介面文檔清單，DEL 的對象另外列出。"""
    docs: dict[str, dict] = {}
    deleted: list[str] = []
    for row in section["rows"]:
        if row["type"] not in TYPES:
            continue
        for file in row["files"]:
            if row["type"] == "DEL":
                if file not in deleted:
                    deleted.append(file)
                continue
            doc = docs.setdefault(file, {"path": file, "root": "truth", "exists": output_exists(truth_dir, file), "changes": [], "anchors": [], "whole_file": False})
            if row["type"] not in doc["changes"]:
                doc["changes"].append(row["type"])
            anchor = anchor_of(row["target"])
            if anchor is None:
                doc["whole_file"] = True
            elif anchor not in doc["anchors"]:
                doc["anchors"].append(anchor)
    return list(docs.values()), [file for file in deleted if file not in docs]


def record_state(section: dict | None) -> str:
    if section is None:
        return "missing"
    if not section["rows"]:
        return "empty"
    if all(row["type"] == NO_CHANGE for row in section["rows"]):
        return "no_change"
    return "recorded"


def collect_endpoints(plan_dir: Path, truth_dir: Path, inventory: list[dict], sections: list[dict]) -> list[dict]:
    endpoints: list[dict] = []
    for row in inventory:
        endpoint = next((item for item in endpoints if item["prefix"] == row["prefix"]), None)
        if endpoint is None:
            planner = PLANNER_BY_PREFIX.get(row["prefix"], f"{row['prefix'].lower()}-plan")
            endpoint = {
                "prefix": row["prefix"],
                "endpoint": row["endpoint"],
                "planner": planner,
                "planner_found": (SKILLS_DIR / planner / "SKILL.md").is_file(),
                "interface_ids": [],
                "interface_changes": {},
                "doc_root": None,
                "record": None,
                "docs": [],
                "deleted_docs": [],
            }
            if planner in PLAN_DOCS:
                root, outputs = PLAN_DOCS[planner]
                endpoint["doc_root"] = root
                endpoint["record"] = "plan"
                endpoint["docs"] = [{"path": output, "root": "plan", "exists": output_exists(plan_dir, output), "changes": [], "anchors": [], "whole_file": True} for output in outputs]
            else:
                section = next((item for item in sections if item["owner"] == planner), None)
                endpoint["record"] = record_state(section)
                if section is not None:
                    endpoint["doc_root"] = "、".join(section["paths"])
                    endpoint["docs"], endpoint["deleted_docs"] = truth_docs(section, truth_dir)
            endpoints.append(endpoint)
        endpoint["interface_ids"].append(row["id"])
        endpoint["interface_changes"][row["id"]] = row["change"]
    return endpoints


def read_wave_report(plan_dir: Path) -> dict | None:
    """wave-report.md 第一張表每個端點的 Planner 與狀態（完成、不能改、未完成、未執行），以及「不能改」一節列出的擋住對象與應交給的對象；檔案不存在時回傳 None。"""
    path = plan_dir / WAVE_REPORT
    if not path.is_file():
        return None
    rows: list[dict] = []
    header: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.startswith("#"):
            if header:
                break
            continue
        if TABLE_SEPARATOR_PATTERN.match(line):
            continue
        matched = TABLE_ROW_PATTERN.match(line)
        if not matched:
            if header and line.strip():
                break
            continue
        cells = [cell.strip() for cell in matched.group(1).split("|")]
        if not header:
            header = cells
            continue
        row = dict(zip(header, cells))
        rows.append({"endpoint": row.get("端點", ""), "planner": strip_code(row.get("Planner", "")), "status": row.get("狀態", ""), "line": line_no})
    blocked = [{"endpoint": row.get("端點", ""), "blocking": row.get("擋住的規則、條款或上游事實", ""), "handover": row.get("應交給", ""), "line": row["line"]}
               for row in read_table(path, BLOCKED_HEADING)]
    return {"rows": rows, "not_done": [row for row in rows if row["status"] != DONE_STATUS], "blocked": blocked}


def coverage_rows_by_folder(plan_dir: Path) -> dict[str, int] | None:
    """plan 涵蓋表的 AC 涵蓋表與補充案例中，每個端點資料夾的列數；涵蓋表不存在時回傳 None。"""
    path = plan_dir / COVERAGE
    if not path.is_file():
        return None
    counts: dict[str, int] = {}
    for heading in COVERAGE_HEADINGS:
        for row in read_table(path, heading):
            folder = strip_code(row.get("端點", ""))
            if folder:
                counts[folder] = counts.get(folder, 0) + 1
    return counts


def endpoints_without_cases(endpoints: list[dict], feature_endpoints: list[dict], counts: dict[str, int]) -> list[dict]:
    """這次有新增或修改介面（介面盤點沒有異動欄時視為有）、涵蓋表卻沒有任何一列落在其端點資料夾的端點；behavior 為 True 的是畫面或 API 端點，dsl-refine 必須為它產出案例。"""
    folder_by_prefix = {item["prefix"]: item["folder"] for item in feature_endpoints}
    result = []
    for endpoint in endpoints:
        changed = [interface_id for interface_id, change in endpoint["interface_changes"].items() if change in CASE_CHANGES]
        folder = folder_by_prefix.get(endpoint["prefix"])
        if not changed or (folder and counts.get(folder)):
            continue
        result.append({
            "prefix": endpoint["prefix"],
            "folder": folder,
            "interfaces": changed,
            "behavior": endpoint["prefix"] in BEHAVIOR_PREFIXES,
            "reason": f"涵蓋表沒有任何一列的端點是 {folder}" if folder else f"truth 用語表的端點表沒有登記 {endpoint['prefix']} 前綴的端點資料夾",
        })
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="盤點進行中的 plan 與 specs/truth/ 的必要產物、truth 用語表登記的端點資料夾、各端點的介面文檔（plan 的 ui/，或 truth-changes.md 中該 Planner 一節列出的對象）、這次有異動介面、涵蓋表卻沒有任何一列落在其端點資料夾的端點，以及 wave-report.md 中每個 Planner 的狀態與不能改的原因。")
    parser.add_argument("plan_dir", help="plan 資料夾路徑，例如 specs/plans/004-ranking")
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
    root = project_root(plan_dir)
    required = [
        {"path": display_path(plan_dir / name, root) + ("/" if name.endswith("/") else ""), "exists": required_exists(plan_dir, name), "upstream_skill": skill}
        for name, skill in PLAN_ARTIFACTS
    ] + [
        {"path": display_path(truth_dir / name, root) + ("/" if name.endswith("/") else ""), "exists": required_exists(truth_dir, name), "upstream_skill": skill}
        for name, skill in TRUTH_ARTIFACTS
    ]
    plan_path = plan_dir / "plan.md"
    inventory = read_inventory(plan_path) if plan_path.is_file() else []
    if plan_path.is_file() and not inventory:
        print("警告：plan.md 找不到「### 介面盤點」表格，無法推得介面文檔。", file=sys.stderr)
    sections = read_truth_changes(plan_dir, truth_dir)
    endpoints = collect_endpoints(plan_dir, truth_dir, inventory, sections)
    missing = [f"{item['path']}（{item['upstream_skill']}）" for item in required if not item["exists"]]
    feature_endpoints = read_feature_endpoints(truth_dir)
    if (truth_dir / GLOSSARY).is_file() and not feature_endpoints:
        print("警告：truth 用語表找不到「## 端點」表格，無法盤點端點資料夾。", file=sys.stderr)
    for item in feature_endpoints:
        if not item["exists"] or not item["has_dsl"] or not item["features"]:
            missing.append(f"{display_path(truth_dir / 'features', root)}/{item['folder']}/（dsl-refine，用語表端點表 {item['prefix']}：需含 dsl.md 與至少一份 feature）")
    for endpoint in endpoints:
        if not endpoint["planner_found"]:
            missing.append(f"Planner {endpoint['planner']}（{endpoint['prefix']} 端點）")
            continue
        changed = any(change != "無" for change in endpoint["interface_changes"].values())
        if endpoint["record"] in {"missing", "empty"} and changed:
            missing.append(f"truth-changes.md 中 {endpoint['planner']} 的紀錄（{endpoint['prefix']} 端點有新增、修改或刪除的介面，請先執行 {endpoint['planner']}）")
        base = plan_dir if endpoint["record"] == "plan" else truth_dir
        missing += [display_path(base / doc["path"], root) + ("/" if doc["path"].endswith("/") else "") + f"（{endpoint['planner']}）"
                    for doc in endpoint["docs"] if not doc["exists"]]
    counts = coverage_rows_by_folder(plan_dir)
    without_cases = endpoints_without_cases(endpoints, feature_endpoints, counts) if counts is not None else []
    for item in without_cases:
        print(f"警告：{item['prefix']} 端點這次有異動的介面（{'、'.join(item['interfaces'])}），但{item['reason']}", file=sys.stderr)
    roots_by_prefix = {endpoint["prefix"]: endpoint["doc_root"] for endpoint in endpoints if endpoint["doc_root"]}
    own_doc_args = [
        f"{item['folder']}={doc_root}"
        for item in feature_endpoints
        for doc_root in re.split(r"[、,，]", roots_by_prefix.get(item["prefix"], ""))
        if doc_root
    ]
    result = {
        "plan": plan_dir.resolve().name,
        "plan_dir": display_path(plan_dir, root),
        "truth_dir": display_path(truth_dir, root),
        "required": required,
        "endpoints": endpoints,
        "feature_endpoints": feature_endpoints,
        "endpoints_without_cases": without_cases,
        "wave_report": read_wave_report(plan_dir),
        "own_doc_args": own_doc_args,
        "missing": missing,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
