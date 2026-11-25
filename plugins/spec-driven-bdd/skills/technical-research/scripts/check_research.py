# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""檢查 research.md：R 編號是否依出現順序遞增且不重複（刪除決策留下的空號不補、不重用）、每項決策「對應需求」的引用是否存在（spec.md 的 FR、NFR、SC 與使用者故事，acceptance 中標 @開發發現 的 AC，技術項.md 的技術項）、「取代」欄引用的已交付 plan 決策是否存在，以及殘留樣板內容，並列出 spec.md 中未被任何決策引用的需求。技術修正 plan（.plan.json 的 kind 為技術修正）沒有 spec.md，對應需求只接受技術項或「跨領域」。有問題時以 exit code 1 結束。"""

import argparse
import sys
import json
import re
from pathlib import Path

SPEC_DEFINITION_PATTERN = re.compile(r"^- \*\*(FR|NFR|SC)-(\d{3})\*\*")
SPEC_STORY_PATTERN = re.compile(r"^### 使用者故事 (\d+) - ")
DECISION_PATTERN = re.compile(r"^## R-(\d{2}) ")
REQUIREMENT_LINE_PATTERN = re.compile(r"^- \*\*對應需求\*\*：(.*)$")
REPLACES_LINE_PATTERN = re.compile(r"^- \*\*取代\*\*：(.*)$")
REFERENCE_PATTERN = re.compile(r"(?<![A-Z])(FR|NFR|SC)-(\d{3})")
STORY_REFERENCE_PATTERN = re.compile(r"(?<![A-Z])US(\d+)")
AC_REFERENCE_PATTERN = re.compile(r"(?<![A-Za-z0-9])(AC-\d+)(?!\d)")
TECH_ITEM_REFERENCE_PATTERN = re.compile(r"技術項「([^」]+)」")
DECISION_REF_PATTERN = re.compile(r"(?<!\d)(\d{3})/R-(\d{2})(?!\d)")
PLAN_DIR_PATTERN = re.compile(r"^(\d{3})-")
LEFTOVER_PATTERN = re.compile(r"\{\{[^}]*\}\}|<!-- 重複(開始|結束)")
EXAMPLE_TITLE_PATTERN = re.compile(r"^(?:Example|Scenario Outline|Scenario Template|Scenario|例子|場景大綱|場景|劇本大綱|劇本)\s*[:：]\s*(AC-\d+)")
TECH_ITEM_LINE_PATTERN = re.compile(r"^[-*]\s+(\S.*)$")
FINDING_TAG = "@開發發現"
FIX_KIND = "技術修正"
DEFAULT_KIND = "需求"
PLAN_FILE = ".plan.json"
SPEC_FILE = "spec.md"
RESEARCH_FILE = "research.md"
TECH_ITEMS_FILE = "技術項.md"
ACCEPTANCE_DIR = ("features", "acceptance")


def read_spec(lines: list[str]) -> tuple[list[str], set[int]]:
    requirements = []
    stories = set()
    for line in lines:
        definition = SPEC_DEFINITION_PATTERN.match(line)
        if definition:
            requirements.append(f"{definition.group(1)}-{definition.group(2)}")
        story = SPEC_STORY_PATTERN.match(line)
        if story:
            stories.add(int(story.group(1)))
    return requirements, stories


def read_plan_kind(plan_dir: Path) -> str:
    plan_file = plan_dir / PLAN_FILE
    if not plan_file.is_file():
        return DEFAULT_KIND
    try:
        data = json.loads(plan_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"警告：{plan_file} 不是合法的 JSON，視為需求 plan。", file=sys.stderr)
        return DEFAULT_KIND
    return data.get("kind") or DEFAULT_KIND


def read_acceptance(plan_dir: Path) -> tuple[set[str], set[str]]:
    """回傳 acceptance 中所有 AC 編號與其中標 @開發發現 的 AC 編號；標籤寫在 Example 上方，中間可以有註解。"""
    all_acs: set[str] = set()
    finding_acs: set[str] = set()
    folder = plan_dir.joinpath(*ACCEPTANCE_DIR)
    if not folder.is_dir():
        return all_acs, finding_acs
    for feature in sorted(folder.glob("*.feature")):
        tags: list[str] = []
        for raw in feature.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("@"):
                tags.extend(line.split())
                continue
            title = EXAMPLE_TITLE_PATTERN.match(line)
            if title:
                all_acs.add(title.group(1))
                if FINDING_TAG in tags:
                    finding_acs.add(title.group(1))
            tags = []
    return all_acs, finding_acs


def read_tech_items(plan_dir: Path) -> list[str] | None:
    """回傳技術項.md 每一行的內容；檔案不存在時回傳 None。"""
    path = plan_dir / TECH_ITEMS_FILE
    if not path.is_file():
        return None
    items = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        matched = TECH_ITEM_LINE_PATTERN.match(raw.strip())
        if matched:
            items.append(matched.group(1))
    return items


def read_decisions(plans_dir: Path, plan_number: str) -> tuple[str, set[int]] | None:
    """回傳編號為 plan_number 的 plan 資料夾名稱與它 research.md 的決策編號；找不到 plan 或 research.md 時回傳 None。"""
    if not plans_dir.is_dir():
        return None
    for folder in sorted(plans_dir.iterdir()):
        matched = PLAN_DIR_PATTERN.match(folder.name)
        research = folder / RESEARCH_FILE
        if folder.is_dir() and matched and matched.group(1) == plan_number and research.is_file():
            numbers = {int(found.group(1)) for found in map(DECISION_PATTERN.match, research.read_text(encoding="utf-8").splitlines()) if found}
            return folder.name, numbers
    return None


def check_requirement_refs(line_no: int, refs: str, context: dict, referenced: set[str]) -> list[dict]:
    problems = []
    fix_plan = context["kind"] == FIX_KIND
    for prefix, number in REFERENCE_PATTERN.findall(refs):
        ref = f"{prefix}-{number}"
        referenced.add(ref)
        if fix_plan:
            problems.append({"type": "reference", "line": line_no, "message": f"技術修正 plan 沒有 spec.md，不能引用 {ref}；請改寫成 技術項「<技術項.md 中的問題>」，無直接對應時寫「跨領域」。"})
        elif ref not in context["requirements"]:
            problems.append({"type": "reference", "line": line_no, "message": f"引用的 {ref} 不存在於 spec.md，請改為 spec.md 已定義的編號。"})
    for number in STORY_REFERENCE_PATTERN.findall(refs):
        if fix_plan:
            problems.append({"type": "reference", "line": line_no, "message": f"技術修正 plan 沒有 spec.md，不能引用 US{number}；請改寫成 技術項「<技術項.md 中的問題>」，無直接對應時寫「跨領域」。"})
        elif int(number) not in context["stories"]:
            problems.append({"type": "reference", "line": line_no, "message": f"引用的 US{number} 不存在於 spec.md，請改為 spec.md 已定義的使用者故事編號。"})
    for ac in AC_REFERENCE_PATTERN.findall(refs):
        if fix_plan:
            problems.append({"type": "reference", "line": line_no, "message": f"技術修正 plan 沒有 acceptance，不能引用 {ac}；請改寫成 技術項「<技術項.md 中的問題>」。"})
        elif ac in context["finding_acs"]:
            continue
        elif ac in context["all_acs"]:
            problems.append({"type": "reference", "line": line_no, "message": f"{ac} 是 PM 提出的 AC，不是標 {FINDING_TAG} 的 AC；請改引用它涵蓋的 FR、NFR 或驗收情境。"})
        else:
            problems.append({"type": "reference", "line": line_no, "message": f"引用的 {ac} 不存在於這個 plan 的 features/acceptance/，請改為標 {FINDING_TAG} 的 AC 編號。"})
    for item in TECH_ITEM_REFERENCE_PATTERN.findall(refs):
        if context["tech_items"] is None:
            problems.append({"type": "reference", "line": line_no, "message": f"引用了 技術項「{item}」，但這個 plan 沒有 {TECH_ITEMS_FILE}；請確認技術項已由 dev-finding 記錄，或改引用其他需求。"})
        elif not any(item in line for line in context["tech_items"]):
            problems.append({"type": "reference", "line": line_no, "message": f"技術項「{item}」不在 {TECH_ITEMS_FILE} 中；請照抄該行「（」之前的問題文字。"})
    return problems


def check_replaces(line_no: int, refs: str, context: dict) -> list[dict]:
    found = DECISION_REF_PATTERN.findall(refs)
    if not found:
        return [{"type": "replaces", "line": line_no, "message": "「取代」欄沒有寫出被取代的決策；請寫成 <plan 編號>/R-<編號> 的「<被取代的部分>」，例如 001/R-07 的「長邊 400px」。"}]
    problems = []
    for plan, number in found:
        if plan == context["plan_number"]:
            problems.append({"type": "replaces", "line": line_no, "message": f"{plan}/R-{number} 是這個 plan 自己的決策；本 plan 的決策直接改寫那一項，不另立決策取代它。"})
            continue
        decisions = read_decisions(context["plans_dir"], plan)
        if decisions is None:
            problems.append({"type": "replaces", "line": line_no, "message": f"「取代」欄的 {plan}/R-{number} 找不到對應的 research.md；請確認 specs/plans/ 底下有編號 {plan} 的 plan 且已產出 research.md。"})
        elif int(number) not in decisions[1]:
            problems.append({"type": "replaces", "line": line_no, "message": f"「取代」欄的 {plan}/R-{number} 不存在於 {decisions[0]}/research.md，請改為該 research.md 已有的決策編號。"})
    return problems


def check_research(lines: list[str], context: dict) -> tuple[list[dict], set[str]]:
    problems = []
    referenced = set()
    decisions = []
    for line_no, line in enumerate(lines, start=1):
        leftover = LEFTOVER_PATTERN.search(line)
        if leftover:
            problems.append({
                "type": "leftover",
                "line": line_no,
                "message": f"殘留樣板內容 {leftover.group(0)}，請填入實際內容或刪除該行。",
            })
        decision = DECISION_PATTERN.match(line)
        if decision:
            decisions.append({"line": line_no, "number": int(decision.group(1)), "has_requirement": False})
            continue
        requirement_line = REQUIREMENT_LINE_PATTERN.match(line)
        replaces_line = REPLACES_LINE_PATTERN.match(line)
        if not requirement_line and not replaces_line:
            continue
        if not decisions:
            field = "對應需求" if requirement_line else "取代"
            problems.append({
                "type": "requirement" if requirement_line else "replaces",
                "line": line_no,
                "message": f"「{field}」出現在任何 R-xx 決策之前，請移到所屬決策的標題下方。",
            })
            continue
        if replaces_line:
            problems.extend(check_replaces(line_no, replaces_line.group(1), context))
            continue
        decisions[-1]["has_requirement"] = True
        problems.extend(check_requirement_refs(line_no, requirement_line.group(1), context, referenced))
    previous = 0
    for decision in decisions:
        if decision["number"] <= previous:
            problems.append({
                "type": "numbering",
                "line": decision["line"],
                "message": f"R-{decision['number']:02d} 出現在 R-{previous:02d} 之後；R 編號必須依出現順序遞增且不重複，刪除的決策留下的編號不補也不重用，新的決策取既有最大編號加一。",
            })
        previous = max(previous, decision["number"])
    for decision in decisions:
        if not decision["has_requirement"]:
            problems.append({
                "type": "requirement",
                "line": decision["line"],
                "message": f"R-{decision['number']:02d} 缺少「- **對應需求**：」欄位，請補上對應的 FR、NFR、SC、US、邊界情況、標 {FINDING_TAG} 的 AC 或技術項，無直接對應時寫「跨領域」。",
            })
    return problems, referenced


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查 research.md 的 R 編號、對應需求與取代欄的引用、殘留佔位符，並列出未被引用的需求；有問題時以 exit code 1 結束。")
    parser.add_argument("research_path", help="要檢查的 research.md 路徑，例如 specs/plans/<plan 資料夾>/research.md")
    parser.add_argument("--spec", help="對照的 spec.md 路徑；省略時使用 research.md 同資料夾的 spec.md（技術修正 plan 沒有 spec.md）")
    parser.add_argument("--plans", help="plan 資料夾所在的目錄，用來查「取代」欄引用的決策；省略時使用 research.md 所在 plan 資料夾的上一層")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    research_path = Path(args.research_path)
    if not research_path.is_file():
        print(f"錯誤：找不到 research.md 檔案 {research_path}。請傳入 research.md 的路徑，例如 specs/plans/<plan 資料夾>/research.md。", file=sys.stderr)
        return 1
    plan_dir = research_path.resolve().parent
    kind = read_plan_kind(plan_dir)
    spec_path = Path(args.spec) if args.spec else plan_dir / SPEC_FILE
    requirements, stories, has_spec = [], set(), spec_path.is_file()
    if has_spec:
        requirements, stories = read_spec(spec_path.read_text(encoding="utf-8").splitlines())
    elif kind != FIX_KIND:
        print(
            f"錯誤：找不到 spec.md 檔案 {spec_path}。需求 plan 的 research.md 要對照同資料夾的 spec.md；"
            f"spec.md 不在同資料夾時以 --spec 指定，沒有 spec.md 的技術修正 plan 要在 {PLAN_FILE} 寫明 \"kind\": \"{FIX_KIND}\"。",
            file=sys.stderr,
        )
        return 1
    all_acs, finding_acs = read_acceptance(plan_dir)
    plan_match = PLAN_DIR_PATTERN.match(plan_dir.name)
    context = {
        "kind": kind,
        "requirements": requirements,
        "stories": stories,
        "all_acs": all_acs,
        "finding_acs": finding_acs,
        "tech_items": read_tech_items(plan_dir),
        "plan_number": plan_match.group(1) if plan_match else None,
        "plans_dir": Path(args.plans).resolve() if args.plans else plan_dir.parent,
    }
    problems, referenced = check_research(research_path.read_text(encoding="utf-8").splitlines(), context)
    unreferenced = [ref for ref in requirements if ref not in referenced]
    print(f"{kind} plan：發現 {len(problems)} 個問題、{len(unreferenced)} 條未被引用的需求", file=sys.stderr)
    print(json.dumps({"ok": not problems, "kind": kind, "problems": problems, "unreferenced": unreferenced}, ensure_ascii=False, indent=2))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
