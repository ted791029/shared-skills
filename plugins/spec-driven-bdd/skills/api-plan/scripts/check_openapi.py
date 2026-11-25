# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pyyaml>=6,<7",
# ]
# ///
"""檢查依模組拆檔的 OpenAPI 契約：每個 $ref 指到的檔案都存在、入口檔掛上每一個路徑檔與 components 底下的每一個檔案、路徑檔的檔名與資料夾符合路徑與第一個 tag、每個操作都有 x-inner-needs，以及沒有被任何操作引用的 schema 與參數檔。"""

import argparse
import json
import sys
from pathlib import Path

import yaml

METHODS = ("get", "put", "post", "delete", "patch", "options", "head", "trace")
ACCESS = ("read", "write", "delete")


def problem(kind: str, file: str, message: str) -> dict:
    return {"type": kind, "file": file, "message": message}


def load(path: Path, rel: str, problems: list[dict]):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        mark = getattr(error, "problem_mark", None)
        where = f"第 {mark.line + 1} 行" if mark else "內容"
        problems.append(problem("syntax", rel, f"{where}不是合法的 YAML：{getattr(error, 'problem', error)}。請修正縮排或引號。"))
        return None


def collect_refs(node, found: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "$ref" and isinstance(value, str):
                found.append(value)
            else:
                collect_refs(value, found)
    elif isinstance(node, list):
        for item in node:
            collect_refs(item, found)


def expected_file_name(api_path: str) -> str:
    return api_path.strip("/").replace("/", "_") + ".yaml"


def check_refs(root: Path, rel: str, document, problems: list[dict], referenced: set[str]) -> None:
    refs: list[str] = []
    collect_refs(document, refs)
    for ref in refs:
        if ref.startswith("#"):
            problems.append(problem("reference", rel, f"引用 {ref} 指向檔案內的 components，但契約已依模組拆檔。請改為相對路徑，例如 ../../components/schemas/<名稱>.yaml。"))
            continue
        target = ((root / rel).parent / ref.split("#", 1)[0]).resolve()
        try:
            target_rel = target.relative_to(root).as_posix()
        except ValueError:
            problems.append(problem("reference", rel, f"引用 {ref} 指到契約資料夾以外的位置。請改為指向 paths/ 或 components/ 底下的檔案。"))
            continue
        if not target.is_file():
            problems.append(problem("reference", rel, f"引用 {ref} 指到的檔案 {target_rel} 不存在。請建立該檔案，或改為既有的檔案。"))
            continue
        referenced.add(target_rel)


def check_inner_needs(rel: str, method: str, operation: dict, problems: list[dict]) -> None:
    needs = operation.get("x-inner-needs")
    if not isinstance(needs, dict):
        problems.append(problem("inner-needs", rel, f"{method.upper()} 操作缺少 x-inner-needs。請列出 data 與 files，沒有對象時寫空陣列。"))
        return
    for key in ("data", "files"):
        items = needs.get(key)
        if not isinstance(items, list):
            problems.append(problem("inner-needs", rel, f"{method.upper()} 操作的 x-inner-needs.{key} 必須是陣列，沒有對象時寫 []。"))
            continue
        names = []
        for item in items:
            if not isinstance(item, dict) or "name" not in item or item.get("access") not in ACCESS:
                problems.append(problem("inner-needs", rel, f"{method.upper()} 操作的 x-inner-needs.{key} 每一項必須有 name 與 access（read、write 或 delete）。"))
                continue
            if set(item) - {"name", "access"}:
                problems.append(problem("inner-needs", rel, f"{method.upper()} 操作的 x-inner-needs.{key} 的 {item['name']} 只能有 name 與 access，請刪除其他欄位。"))
            names.append(item["name"])
        for name in sorted({name for name in names if names.count(name) > 1}):
            problems.append(problem("inner-needs", rel, f"{method.upper()} 操作的 x-inner-needs.{key} 重複列出 {name}。同一個名稱只列一次，取最強的存取。"))


def check_contracts(root: Path) -> dict:
    problems: list[dict] = []
    referenced: set[str] = set()
    entry_rel = "openapi.yaml"
    entry = load(root / entry_rel, entry_rel, problems)
    if not isinstance(entry, dict):
        if not problems:
            problems.append(problem("structure", entry_rel, "入口檔不是 YAML 物件。請依樣板撰寫 openapi、info、tags 與 paths。"))
        return {"ok": False, "paths": 0, "operations": 0, "components": 0, "problems": problems}
    mounted_components: set[str] = set()
    components_entry = entry.get("components")
    for kind, items in (components_entry if isinstance(components_entry, dict) else {}).items():
        for name, item in (items if isinstance(items, dict) else {}).items():
            expected = f"components/{kind}/{name}.yaml"
            if not isinstance(item, dict) or set(item) != {"$ref"} or Path(str(item["$ref"])).as_posix() != expected:
                problems.append(problem("structure", entry_rel, f"components.{kind}.{name} 必須只有一行 $ref: {expected}，內容寫在該檔案，鍵與檔名相同。"))
                continue
            mounted_components.add(expected)
    tags = [item.get("name") for item in entry.get("tags") or [] if isinstance(item, dict)]
    mounted: dict[str, str] = {}
    for api_path, item in (entry.get("paths") or {}).items():
        ref = item.get("$ref") if isinstance(item, dict) else None
        if not isinstance(ref, str) or set(item) != {"$ref"}:
            problems.append(problem("structure", entry_rel, f"路徑 {api_path} 必須只有一行 $ref 指向 paths/<模組>/ 底下的檔案，操作寫在該檔案。"))
            continue
        target_rel = Path(ref).as_posix()
        if target_rel in mounted.values():
            problems.append(problem("structure", entry_rel, f"路徑 {api_path} 與其他路徑掛上同一個檔案 {target_rel}。一個路徑一個檔。"))
        mounted[api_path] = target_rel
    # 入口檔的掛載不算「被操作引用」；只有路徑檔的引用才算
    check_refs(root, entry_rel, entry, problems, set())

    operations = 0
    for api_path, rel in mounted.items():
        path = root / rel
        if not path.is_file():
            continue
        parts = Path(rel).parts
        if len(parts) != 3 or parts[0] != "paths":
            problems.append(problem("location", rel, f"路徑檔必須放在 paths/<模組>/ 底下，目前在 {rel}。"))
            continue
        if parts[2] != expected_file_name(api_path):
            problems.append(problem("location", rel, f"路徑 {api_path} 的檔名應為 {expected_file_name(api_path)}，目前是 {parts[2]}。請改檔名並更新入口檔。"))
        document = load(path, rel, problems)
        if not isinstance(document, dict):
            continue
        check_refs(root, rel, document, problems, referenced)
        methods = [method for method in METHODS if isinstance(document.get(method), dict)]
        if not methods:
            problems.append(problem("structure", rel, "路徑檔沒有任何操作。請以 HTTP 方法（get、post…）為最上層的鍵撰寫操作。"))
        for method in methods:
            operations += 1
            operation = document[method]
            operation_tags = operation.get("tags") or []
            first_tag = operation_tags[0] if operation_tags else None
            if first_tag != parts[1]:
                problems.append(problem("location", rel, f"{method.upper()} 操作的第一個 tag 是「{first_tag}」，檔案卻放在 paths/{parts[1]}/。請讓資料夾名稱與第一個 tag 相同。"))
            if first_tag is not None and first_tag not in tags:
                problems.append(problem("structure", rel, f"{method.upper()} 操作的 tag「{first_tag}」沒有列在入口檔的 tags。請在入口檔補上。"))
            check_inner_needs(rel, method, operation, problems)

    paths_dir = root / "paths"
    for path in sorted(paths_dir.rglob("*.yaml")) if paths_dir.is_dir() else []:
        rel = path.relative_to(root).as_posix()
        if rel not in mounted.values():
            problems.append(problem("unmounted", rel, "入口檔沒有掛上這個路徑檔。請在 openapi.yaml 的 paths 加上對應的路徑與 $ref，或刪除這個檔案。"))

    components_dir = root / "components"
    components = sorted(components_dir.rglob("*.yaml")) if components_dir.is_dir() else []
    pending = [path.relative_to(root).as_posix() for path in components]
    refs_of: dict[str, set[str]] = {}
    for rel in pending:
        refs_of[rel] = set()
        check_refs(root, rel, load(root / rel, rel, problems), problems, refs_of[rel])
    reachable = set(referenced)
    queue = list(reachable)
    while queue:
        for target in refs_of.get(queue.pop(), set()) - reachable:
            reachable.add(target)
            queue.append(target)
    for rel in pending:
        if rel not in mounted_components:
            problems.append(problem("unmounted", rel, "入口檔的 components 沒有掛上這個檔案。請在 openapi.yaml 的 components 加上與檔名相同的鍵與 $ref，或刪除這個檔案。"))
        if rel not in reachable:
            problems.append(problem("unused", rel, "沒有任何路徑檔直接或間接引用這個檔案。請刪除它與入口檔的那一項，或在使用它的操作加上引用。"))
    return {"ok": not problems, "paths": len(mounted), "operations": operations, "components": len(pending), "problems": problems}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查依模組拆檔的 OpenAPI 契約的引用、入口檔對路徑檔與 components 的掛載、檔名與 x-inner-needs。")
    parser.add_argument("contracts_dir", help="契約資料夾，例如 specs/truth/contracts")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    root = Path(args.contracts_dir).resolve()
    if not (root / "openapi.yaml").is_file():
        print(
            f"錯誤：{args.contracts_dir} 底下找不到入口檔 openapi.yaml。請傳入契約資料夾的路徑，例如 specs/truth/contracts。",
            file=sys.stderr,
        )
        return 1
    result = check_contracts(root)
    print(f"發現 {len(result['problems'])} 個問題", file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
