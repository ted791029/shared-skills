# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""列出 plan 的 acceptance 每個 AC（起點、When 組與斷言）、plan.md 的介面前綴與異動、techstack.md 的測試工具與 spec.md 的需求編號，
比對或寫入產生紀錄：plan 的紀錄記 acceptance 與涵蓋表，truth 的紀錄記每個 Example。技術修正 plan 沒有 acceptance、plan.md 與 spec.md，
AC 視為沒有，仍比對與寫入 truth 的 Example 紀錄。"""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STEP = re.compile(r"^\s+(Given|When|Then|And|But) (.*)$")
BLOCK = re.compile(r"^\s+(Example|Scenario Outline): (.*)$")
RULE = re.compile(r"^\s+Rule: (.*)$")
AC_TITLE = re.compile(r"^(AC-\d{2,})\s+(.*)$")
START = re.compile(r'^\s+Given 系統處於 "([^"]+)"$')
DEFAULTS = re.compile(r"^\s*# 預設值：(.*)$")
SEPARATOR = re.compile(r"^\|[-:\s|]+\|$")
RECORD_NAME = ".dsl-refine.json"
COVERAGE_NAME = "涵蓋表.md"
PLAN_FILE = ".plan.json"
TECH_FIX = "技術修正"
INTERFACE_COLUMNS = {"介面 ID": "id", "介面ID": "id", "介面": "name", "所屬端點": "endpoint", "異動": "change", "依據需求": "requirements"}
COVERAGE_COLUMNS = {"AC": "ac", "When 組": "group", "端點": "endpoint", "feature": "feature", "Rule": "rule", "異動": "change"}


def digest(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    while lines and not lines[-1]:
        lines.pop()
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def parse_steps(body: list[str]) -> list[dict]:
    """把 Example 內文切成步驟，每個步驟帶自己的 Data Table 列。"""
    steps = []
    for line in body:
        match = STEP.match(line)
        if match:
            steps.append({"keyword": match.group(1), "text": match.group(2).strip(), "table": []})
        elif line.strip().startswith("|") and steps:
            steps[-1]["table"].append(split_row(line))
    return steps


def group_steps(steps: list[dict]) -> tuple[list[dict], list[dict]]:
    """依 When 分組：第一句 When 之前為 AC 的 Given，之後每句 When 開一組，And 依前一個關鍵字歸入 when 或 then。"""
    given, groups, mode = [], [], "given"
    for step in steps:
        keyword = step["keyword"]
        if keyword == "When":
            groups.append({"index": len(groups) + 1, "when": [step], "then": []})
            mode = "when"
        elif keyword == "Then":
            mode = "then"
            groups[-1]["then"].append(step)
        elif keyword in ("And", "But"):
            if mode == "given":
                given.append(step)
            elif mode == "when":
                groups[-1]["when"].append(step)
            else:
                groups[-1]["then"].append(step)
        else:
            given.append(step)
            mode = "given"
    return given, groups


def parse_acceptance(acceptance_dir: Path | None) -> list[dict]:
    """讀 acceptance 的每份 feature；技術修正 plan 沒有 acceptance（傳入 None）時回傳空清單。"""
    features = []
    if acceptance_dir is None:
        return features
    for path in sorted(acceptance_dir.glob("*.feature")):
        lines = path.read_text(encoding="utf-8").splitlines()
        feature = {"file": path.name, "name": path.stem, "start": None, "defaults": None, "acs": []}
        starts = [i for i, line in enumerate(lines) if BLOCK.match(line)]
        first_block = starts[0] if starts else len(lines)
        for i, line in enumerate(lines[:first_block]):
            if START.match(line) and feature["start"] is None:
                feature["start"] = START.match(line).group(1)
                for k in range(i - 1, -1, -1):
                    if DEFAULTS.match(lines[k]):
                        feature["defaults"] = DEFAULTS.match(lines[k]).group(1).strip()
                        break
                    if lines[k].strip():
                        break
        rule = None
        for n, start in enumerate(starts):
            for k in range(start - 1, -1, -1):
                if RULE.match(lines[k]):
                    rule = RULE.match(lines[k]).group(1).strip()
                    break
            end = starts[n + 1] if n + 1 < len(starts) else len(lines)
            for k in range(start + 1, end):
                if RULE.match(lines[k]):
                    end = k
                    break
            body = lines[start + 1:end]
            title = BLOCK.match(lines[start]).group(2).strip()
            ac = AC_TITLE.match(title)
            given, groups = group_steps(parse_steps(body))
            text = "\n".join([lines[start]] + body)
            feature["acs"].append({
                "id": ac.group(1) if ac else None, "title": ac.group(2) if ac else title, "rule": rule,
                "given": given, "groups": groups, "hash": digest(text), "text": text,
                "clarifications": sum("[NEED CLARIFICATION]" in line for line in body),
            })
        features.append(feature)
    return features


def parse_plan(plan_path: Path) -> dict:
    """讀 plan.md「介面盤點」表格，依表頭取介面 ID、介面、所屬端點、異動與依據需求；前綴取 ID 中第一個「-」之前。"""
    interfaces, in_table, header = [], False, None
    for line in plan_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### 介面盤點"):
            in_table = True
            continue
        if in_table and line.startswith("#"):
            break
        if not in_table or not line.startswith("|") or SEPARATOR.match(line.strip()):
            continue
        cells = split_row(line)
        if header is None:
            header = [INTERFACE_COLUMNS.get(cell) for cell in cells]
            continue
        row = {key: cell for key, cell in zip(header, cells) if key}
        if not row.get("id"):
            continue
        interfaces.append({"id": row["id"], "prefix": row["id"].split("-")[0], "name": row.get("name", ""),
                           "endpoint": row.get("endpoint", ""), "change": row.get("change", "").strip("`"),
                           "requirements": row.get("requirements", "")})
    prefixes = {}
    for item in interfaces:
        prefixes.setdefault(item["prefix"], item["endpoint"])
    return {"interfaces": interfaces, "prefixes": prefixes}


def parse_techstack(path: Path) -> list[dict]:
    rows, in_section, header = [], False, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line[3:].strip().startswith("測試")
            header = None
            continue
        if in_section and line.startswith("|") and not SEPARATOR.match(line.strip()):
            cells = split_row(line)
            if header is None:
                header = cells
                continue
            rows.append(dict(zip(header, cells)))
    return rows


def parse_spec(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    requirements = {}
    for match in re.finditer(r"\*\*((?:NFR|FR)-\d{3})\*\*[：:]?\s*(.*)", text):
        requirements.setdefault(match.group(1), match.group(2).strip())
    edge = re.search(r"(?ms)^### 邊界情況\s*\n(.*?)(?=^## |^### |\Z)", text)
    edge_cases = [line.strip().lstrip("-*0123456789. ").strip() for line in edge.group(1).splitlines() if line.strip()] if edge else []
    stories = re.findall(r"^### 使用者故事 (\d+) - (.*?)（", text, flags=re.MULTILINE)
    return {"requirements": requirements, "edge_cases": edge_cases, "stories": [f"US{n}：{t}" for n, t in stories]}


def parse_blocks(feature_path: Path, root: Path) -> list[dict]:
    """把端點 feature 切成 Example／Scenario Outline 區塊（含前置的標籤行），鍵為 檔案::Rule::標題。"""
    lines = feature_path.read_text(encoding="utf-8").splitlines()
    starts = [i for i, line in enumerate(lines) if BLOCK.match(line)]
    blocks, rule = [], None
    for n, start in enumerate(starts):
        for k in range(start - 1, -1, -1):
            if RULE.match(lines[k]):
                rule = RULE.match(lines[k]).group(1).strip()
                break
        begin = start
        while begin > 0 and lines[begin - 1].strip().startswith("@"):
            begin -= 1
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        for k in range(start + 1, end):
            if RULE.match(lines[k]):
                end = k
                break
        while end > start + 1 and lines[end - 1].strip().startswith("@"):
            end -= 1
        relative = feature_path.relative_to(root).as_posix()
        title = BLOCK.match(lines[start]).group(2).strip()
        blocks.append({"key": f"{relative}::{rule}::{title}", "file": relative, "rule": rule, "title": title,
                       "hash": digest("\n".join(lines[begin:end]))})
    return blocks


def all_blocks(truth_features: Path) -> list[dict]:
    if not truth_features.is_dir():
        return []
    return [block for path in sorted(truth_features.rglob("*.feature")) for block in parse_blocks(path, truth_features)]


def coverage_rows(plan_features: Path) -> list[dict]:
    """讀 plan 的涵蓋表「AC 涵蓋表」，依表頭取 AC、When 組、端點、feature、Rule 與異動（去掉反引號）。"""
    path = plan_features / COVERAGE_NAME
    if not path.is_file():
        return []
    section = re.search(r"(?ms)^## AC 涵蓋表\s*\n(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"))
    if not section:
        return []
    rows, header = [], None
    for line in section.group(1).splitlines():
        if not line.strip().startswith("|") or SEPARATOR.match(line.strip()):
            continue
        cells = [cell.strip("`") for cell in split_row(line)]
        if header is None:
            header = [COVERAGE_COLUMNS.get(cell) for cell in cells]
            continue
        row = {key: cell for key, cell in zip(header, cells) if key}
        if row.get("ac"):
            rows.append({key: row.get(key, "") for key in COVERAGE_COLUMNS.values()})
    return rows


def load_record(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def plan_kind(plan_dir: Path) -> str:
    """讀 plan 的 .plan.json 的種類（需求或技術修正）；沒有檔案或欄位時視為需求。"""
    path = plan_dir / PLAN_FILE
    if not path.is_file():
        return "需求"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("kind") or "需求"
    except json.JSONDecodeError:
        return "需求"


def locate(args: argparse.Namespace) -> tuple[Path, Path, Path | None, Path, bool] | None:
    """回傳（plan 資料夾、plan 的 features、acceptance、truth 資料夾、是否為技術修正 plan）；技術修正 plan 的 acceptance 為 None。
    輸入不齊時印出說明並回傳 None。"""
    plan_dir = Path(args.plan_dir)
    if not plan_dir.is_dir():
        print(f"錯誤：找不到 plan 資料夾 {plan_dir}。請傳入含 features/acceptance/ 的 plan 資料夾，例如 specs/plans/004-ranking", file=sys.stderr)
        return None
    plan_features = plan_dir / "features"
    acceptance = plan_features / "acceptance"
    technical = plan_kind(plan_dir) == TECH_FIX
    if technical:
        print(f"{plan_dir.name} 是技術修正 plan，沒有 acceptance，AC 視為沒有", file=sys.stderr)
        acceptance = None
    elif not acceptance.is_dir() or not any(acceptance.glob("*.feature")):
        print(f"錯誤：{acceptance} 底下沒有任何 .feature。請先執行 spec-by-example 產出驗收 feature，再傳入 plan 資料夾，例如 specs/plans/004-ranking；"
              f"只為技術修正的 plan 要以 plan-package open --kind 技術修正 開立", file=sys.stderr)
        return None
    truth = Path(args.truth) if args.truth else plan_dir.resolve().parent.parent / "truth"
    return plan_dir, plan_features, acceptance, truth, technical


def command_list(args: argparse.Namespace) -> int:
    located = locate(args)
    if located is None:
        return 1
    plan_dir, _, acceptance, truth, technical = located
    features = parse_acceptance(acceptance)
    for feature in features:
        for ac in feature["acs"]:
            ac.pop("text")
            ac.pop("hash")
    result = {"plan_kind": TECH_FIX if technical else "需求", "acceptance": features}
    missing = []
    for label, path, parser, key in (("plan.md", plan_dir / "plan.md", parse_plan, "plan"),
                                     ("specs/truth/techstack.md", truth / "techstack.md", parse_techstack, "test_tools"),
                                     ("spec.md", plan_dir / "spec.md", parse_spec, "spec")):
        if path.is_file():
            result[key] = parser(path)
        elif not (technical and label in ("plan.md", "spec.md")):
            missing.append(label)
    total_ac = sum(len(f["acs"]) for f in features)
    total_groups = sum(len(ac["groups"]) for f in features for ac in f["acs"])
    clarifications = sum(ac["clarifications"] for f in features for ac in f["acs"])
    print(f"讀取 {len(features)} 份驗收 feature、{total_ac} 個 AC、{total_groups} 組 When；殘留澄清標籤 {clarifications} 個", file=sys.stderr)
    if missing:
        print(f"警告：缺少 {missing}，請先執行產出它的上游 skill（specify、system-analysis 或 technical-research）", file=sys.stderr)
    result["missing_inputs"] = missing
    result["clarifications"] = clarifications
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_diff(args: argparse.Namespace) -> int:
    located = locate(args)
    if located is None:
        return 1
    _, plan_features, acceptance, truth, technical = located
    truth_features = truth / "features"
    plan_record = load_record(plan_features / RECORD_NAME)
    truth_record = load_record(truth_features / RECORD_NAME)
    new = {ac["id"]: ac for feature in parse_acceptance(acceptance) for ac in feature["acs"] if ac["id"]}
    result = {"has_record": plan_record is not None and "acceptance" in plan_record, "has_truth_record": truth_record is not None}
    if plan_record is not None and "acceptance" not in plan_record:
        result["legacy_record"] = True
        print(f"產生紀錄 {plan_features / RECORD_NAME} 是舊版格式，無法比對 AC，這個 plan 的 AC 全部視為新增", file=sys.stderr)
    if result["has_record"]:
        old = plan_record["acceptance"]
        coverage = plan_record.get("coverage", [])

        def rules_of(ac_id: str) -> list[dict]:
            return [{"endpoint": row["endpoint"], "feature": row["feature"], "rule": row["rule"], "change": row.get("change", "")}
                    for row in coverage if row["ac"] == ac_id]

        result["acceptance"] = {
            "added": [ac_id for ac_id in new if ac_id not in old],
            "changed": [{"id": ac_id, "before": old[ac_id]["text"], "after": new[ac_id]["text"], "rules": rules_of(ac_id)}
                        for ac_id in new if ac_id in old and old[ac_id]["hash"] != new[ac_id]["hash"]],
            "removed": [{"id": ac_id, "rules": rules_of(ac_id)} for ac_id in old if ac_id not in new],
        }
    else:
        if not technical:
            print(f"這個 plan 沒有產生紀錄 {plan_features / RECORD_NAME}，AC 全部視為新增", file=sys.stderr)
        result["acceptance"] = {"added": list(new), "changed": [], "removed": []}
    blocks = all_blocks(truth_features)
    if truth_record is not None:
        recorded = truth_record.get("examples", {})
        keys = {block["key"] for block in blocks}
        result["examples"] = {
            "hand_edited": [b["key"] for b in blocks if b["key"] in recorded and recorded[b["key"]]["hash"] != b["hash"]],
            "untracked": [b["key"] for b in blocks if b["key"] not in recorded],
            "missing": [key for key in recorded if key not in keys],
        }
    else:
        print(f"truth 沒有產生紀錄 {truth_features / RECORD_NAME}，既有的 {len(blocks)} 個 Example 都視為沒有手改；寫入紀錄後才開始偵測手改", file=sys.stderr)
        result["examples"] = {"hand_edited": [], "untracked": [b["key"] for b in blocks], "missing": []}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def command_record(args: argparse.Namespace) -> int:
    located = locate(args)
    if located is None:
        return 1
    _, plan_features, acceptance, truth, _ = located
    truth_features = truth / "features"
    if not truth_features.is_dir():
        print(f"錯誤：找不到 {truth_features}。請先產出各端點的 feature 與 dsl.md，或以 --truth 指定 truth 資料夾，例如 --truth specs/truth", file=sys.stderr)
        return 1
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    acs = [ac for feature in parse_acceptance(acceptance) for ac in feature["acs"] if ac["id"]]
    blocks = all_blocks(truth_features)
    plan_record = {
        "generated_at": generated_at,
        "acceptance": {ac["id"]: {"hash": ac["hash"], "text": ac["text"], "groups": len(ac["groups"])} for ac in acs},
        "coverage": coverage_rows(plan_features),
    }
    truth_record = {
        "generated_at": generated_at,
        "examples": {b["key"]: {"file": b["file"], "rule": b["rule"], "title": b["title"], "hash": b["hash"]} for b in blocks},
    }
    plan_path, truth_path = plan_features / RECORD_NAME, truth_features / RECORD_NAME
    plan_features.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan_record, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    truth_path.write_text(json.dumps(truth_record, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"已寫入 {len(plan_record['acceptance'])} 個 AC、{len(plan_record['coverage'])} 列 AC 涵蓋到 plan 的紀錄，{len(blocks)} 個 Example 到 truth 的紀錄", file=sys.stderr)
    print(json.dumps({"plan_record": plan_path.as_posix(), "truth_record": truth_path.as_posix()}, ensure_ascii=False, indent=2))
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="列出 plan 的 acceptance 每個 AC 與各產物的對照資訊，比對或寫入產生紀錄。")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, text in (("list", "以 JSON 列出每個 AC 的起點、Given、When 組與斷言，以及 plan.md 的介面前綴與異動、techstack.md 的測試工具與 spec.md 的需求"),
                       ("diff", "比對 acceptance 與 plan 的產生紀錄，列出新增、修改、刪除的 AC 與它們對應的 Rule；比對 truth 的產生紀錄，列出手改過的 Example"),
                       ("record", f"寫入產生紀錄：plan 的 features/{RECORD_NAME} 記每個 AC 的原文雜湊與涵蓋表，truth 的 features/{RECORD_NAME} 記每個 Example 的雜湊")):
        command = sub.add_parser(name, help=text)
        command.add_argument("plan_dir", help="plan 資料夾，內含 features/acceptance/（.plan.json 的種類為技術修正時不需要），例如 specs/plans/004-ranking")
        command.add_argument("--truth", help="truth 資料夾，預設為 plan 資料夾往上兩層的 truth/，例如 specs/truth")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    return {"list": command_list, "diff": command_diff, "record": command_record}[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
