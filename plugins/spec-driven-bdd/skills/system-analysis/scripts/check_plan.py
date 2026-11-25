# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""檢查 plan.md 的介面 ID 唯一、每個介面的異動為 ADD、MOD、DEL 或 無、依據需求引用的編號存在於 spec.md 或本 plan 標 @開發發現 的 AC，或寫出「技術：<原因>」、每個介面恰好分入一個 Wave、委派與相依的端點一致、統計數字一致，以及殘留樣板內容。"""

import argparse
import sys
import json
import re
from pathlib import Path

REQUIREMENT_PATTERN = re.compile(r"\*\*((?:FR|NFR|SC)-\d{3})\*\*")
REQUIREMENT_REF_PATTERN = re.compile(r"((?:FR|NFR|SC)-\d{3}|AC-\d+)(?:～((?:FR|NFR|SC)-\d{3}|AC-\d+))?")
EXAMPLE_AC_PATTERN = re.compile(r"^\s*(?:Example|Scenario Outline|Scenario|例子|場景大綱|場景)\s*[:：]\s*(AC-\d+)(?!\d)")
FINDING_TAG = "@開發發現"
TECHNICAL_BASIS_PATTERN = re.compile(r"技術[：:]")
INTERFACE_REF_PATTERN = re.compile(r"([A-Z]+-\d{2})(?:～([A-Z]+-\d{2}))?")
WAVE_PATTERN = re.compile(r"^\*\*Wave (\d+) — (.+)\*\*$")
WAVE_ENDPOINT_PATTERN = re.compile(r"([^、（]+)（([^）]+)）")
DELEGATION_PATTERN = re.compile(r"^- 委派：開 (\d+) 個 sub-agent，分別分析(.+?)。?$")
DEPENDENCY_PATTERN = re.compile(r"^- 相依：(.+)$")
DEPENDENCY_REF_PATTERN = re.compile(r"Wave (\d+) ([^、]+?)的產出")
SUMMARY_PATTERN = re.compile(r"共盤點 (\d+) 個端點、(\d+) 個介面、(\d+) 個 Wave")
LEFTOVER_PATTERN = re.compile(r"\{\{[^}]*\}\}|<!-- 重複(開始|結束)|<TODO>")
DIVIDER_PATTERN = re.compile(r"^\|[\s|:-]+\|$")
CHANGE_TYPES = ("ADD", "MOD", "DEL", "無")


def problem(kind: str, line: int | None, message: str) -> dict:
    return {"type": kind, "line": line, "message": message}


def expand_range(start: str, end: str | None, pool: set[str]) -> list[str]:
    if not end:
        return [start]
    prefix, first = start.rsplit("-", 1)
    end_prefix, last = end.rsplit("-", 1)
    if prefix != end_prefix or int(last) < int(first):
        return [start, end]
    width = len(first)
    return [f"{prefix}-{number:0{width}d}" for number in range(int(first), int(last) + 1)]


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def split_basis(text: str) -> tuple[str, str | None]:
    """把依據需求拆成需求編號的部分與「技術：」之後的技術原因；沒有「技術：」時原因為 None。"""
    technical = TECHNICAL_BASIS_PATTERN.search(text)
    if not technical:
        return text, None
    return text[:technical.start()], text[technical.end():].strip()


def read_interfaces(lines: list[str]) -> tuple[list[tuple[int, dict]], list[dict]]:
    for index in range(len(lines) - 1):
        header = split_row(lines[index]) if lines[index].strip().startswith("|") else []
        if "介面 ID" in header and DIVIDER_PATTERN.match(lines[index + 1].strip()):
            rows = []
            row_index = index + 2
            while row_index < len(lines) and lines[row_index].strip().startswith("|"):
                rows.append((row_index + 1, dict(zip(header, split_row(lines[row_index])))))
                row_index += 1
            if "異動" not in header:
                return rows, [problem("structure", index + 1, "介面盤點表格缺少「異動」欄，請依樣板在「所屬端點」之後加上，每個介面填 ADD、MOD、DEL 或 無。")]
            return rows, []
    return [], [problem("structure", None, "找不到含「介面 ID」欄位的介面盤點表格，請依樣板在「### 介面盤點」撰寫表格。")]


def check_interfaces(rows: list[tuple[int, dict]], requirements: set[str]) -> tuple[dict[str, str], list[dict]]:
    problems = []
    endpoints_by_id = {}
    for line_no, cells in rows:
        interface_id = cells.get("介面 ID", "")
        if interface_id in endpoints_by_id:
            problems.append(problem("duplicate", line_no, f"介面 ID {interface_id} 重複，請改為唯一編號。"))
            continue
        endpoints_by_id[interface_id] = cells.get("所屬端點", "")
        change = cells.get("異動")
        if change is not None and change.strip("` ") not in CHANGE_TYPES:
            problems.append(problem("change", line_no, f"介面 {interface_id} 的異動為「{change}」，只能是 ADD、MOD、DEL 或 無；請對照 specs/truth/ 的現況改正。"))
        requirement_text, technical_reason = split_basis(cells.get("依據需求", ""))
        refs = REQUIREMENT_REF_PATTERN.findall(requirement_text)
        if technical_reason == "":
            problems.append(problem("reference", line_no, f"介面 {interface_id} 的依據需求寫了「技術：」卻沒有原因，請寫出技術項的問題，或「依憲法 <條款 ID> 改正」。"))
        elif not refs and technical_reason is None:
            problems.append(problem("reference", line_no, f"介面 {interface_id} 缺少依據需求，請填入 spec.md 的 FR、NFR 或 SC 編號；只因技術原因而異動、沒有需求可引用的介面，在依據需求最後寫「技術：<原因>」。"))
        for start, end in refs:
            for ref in expand_range(start, end, requirements):
                if ref.startswith("AC-") and ref not in requirements:
                    problems.append(problem("reference", line_no, f"介面 {interface_id} 引用的 {ref} 不是本 plan acceptance 中標 {FINDING_TAG} 的 AC；依據需求只能引用 spec.md 的需求編號或本 plan 的開發發現 AC。"))
                elif ref not in requirements:
                    problems.append(problem("reference", line_no, f"介面 {interface_id} 引用的 {ref} 不存在於 spec.md，請改為 spec.md 已有的需求編號。"))
    return endpoints_by_id, problems


def read_waves(lines: list[str]) -> list[dict]:
    waves = []
    for line_no, line in enumerate(lines, start=1):
        wave = WAVE_PATTERN.match(line.strip())
        if wave:
            waves.append({"line": line_no, "number": int(wave.group(1)), "heading": wave.group(2), "delegation": None, "dependency": None})
            continue
        if not waves:
            continue
        delegation = DELEGATION_PATTERN.match(line.strip())
        if delegation:
            waves[-1]["delegation"] = (line_no, int(delegation.group(1)), [name.strip() for name in delegation.group(2).split("、")])
        dependency = DEPENDENCY_PATTERN.match(line.strip())
        if dependency:
            waves[-1]["dependency"] = (line_no, dependency.group(1).strip())
    return waves


def check_dependency(wave: dict, endpoints_by_wave: dict[int, set[str]]) -> list[dict]:
    if not wave["dependency"]:
        return [problem("dependency", wave["line"], f"Wave {wave['number']} 缺少「- 相依：Wave N <端點>的產出」一行，沒有前置 Wave 時寫「無」。")]
    line_no, text = wave["dependency"]
    if text == "無":
        if wave["number"] != 1:
            return [problem("dependency", line_no, f"Wave {wave['number']} 的相依為「無」，Wave 1 之後的 Wave 必須列出前置 Wave 端點的產出。")]
        return []
    refs = DEPENDENCY_REF_PATTERN.findall(text)
    if not refs:
        return [problem("dependency", line_no, f"Wave {wave['number']} 的相依必須寫成「Wave N <端點>的產出」，多項以「、」分隔，沒有前置 Wave 時寫「無」。")]
    problems = []
    for number_text, endpoint in refs:
        number = int(number_text)
        if number >= wave["number"]:
            problems.append(problem("dependency", line_no, f"Wave {wave['number']} 相依 Wave {number}，相依只能指向前置 Wave。"))
        elif endpoint.strip() not in endpoints_by_wave.get(number, set()):
            problems.append(problem("dependency", line_no, f"Wave {wave['number']} 相依「Wave {number} {endpoint.strip()}」，但 Wave {number} 沒有此端點，請改正。"))
    return problems


def check_waves(waves: list[dict], endpoints_by_id: dict[str, str]) -> list[dict]:
    problems = []
    assigned = {}
    endpoints_by_wave = {}
    for expected, wave in enumerate(waves, start=1):
        if wave["number"] != expected:
            problems.append(problem("wave", wave["line"], f"Wave 編號為 {wave['number']}，預期為 {expected}，請從 1 開始連續編號。"))
        endpoints = WAVE_ENDPOINT_PATTERN.findall(wave["heading"])
        endpoint_names = [endpoint.strip() for endpoint, _ in endpoints]
        if not endpoints:
            problems.append(problem("wave", wave["line"], "Wave 標題必須寫成「端點（介面 ID～介面 ID）」，多個端點以「、」分隔。"))
        for endpoint, id_text in endpoints:
            endpoint = endpoint.strip()
            for start, end in INTERFACE_REF_PATTERN.findall(id_text):
                for interface_id in expand_range(start, end, set(endpoints_by_id)):
                    if interface_id not in endpoints_by_id:
                        problems.append(problem("wave", wave["line"], f"Wave {wave['number']} 的 {interface_id} 不在介面盤點表格中，請補上該介面或改正編號。"))
                    elif endpoints_by_id[interface_id] != endpoint:
                        problems.append(problem("wave", wave["line"], f"{interface_id} 在表格中屬於「{endpoints_by_id[interface_id]}」，Wave {wave['number']} 卻列在「{endpoint}」下，請改為一致。"))
                    if interface_id in assigned:
                        problems.append(problem("wave", wave["line"], f"{interface_id} 同時出現在 Wave {assigned[interface_id]} 與 Wave {wave['number']}，每個介面只能分入一個 Wave。"))
                    assigned.setdefault(interface_id, wave["number"])
        problems.extend(check_dependency(wave, endpoints_by_wave))
        endpoints_by_wave[wave["number"]] = set(endpoint_names)
        if not wave["delegation"]:
            problems.append(problem("delegation", wave["line"], f"Wave {wave['number']} 缺少「- 委派：開 N 個 sub-agent，分別分析<端點>、<端點>。」一行。"))
            continue
        line_no, agent_count, delegated = wave["delegation"]
        if agent_count != len(endpoints):
            problems.append(problem("delegation", line_no, f"Wave {wave['number']} 有 {len(endpoints)} 個端點，卻開 {agent_count} 個 sub-agent，請改為每個端點一個 sub-agent。"))
        if sorted(delegated) != sorted(endpoint_names):
            problems.append(problem("delegation", line_no, f"Wave {wave['number']} 委派分析「{'、'.join(delegated)}」，與標題的端點「{'、'.join(endpoint_names)}」不一致，請改為一致。"))
    for interface_id in endpoints_by_id:
        if interface_id not in assigned:
            problems.append(problem("wave", None, f"介面 {interface_id} 沒有被分入任何 Wave，請加到其所屬端點的 Wave 標題。"))
    return problems


def check_summary(lines: list[str], endpoints_by_id: dict[str, str], waves: list[dict]) -> list[dict]:
    for line_no, line in enumerate(lines, start=1):
        summary = SUMMARY_PATTERN.search(line)
        if not summary:
            continue
        expected = (len(set(endpoints_by_id.values())), len(endpoints_by_id), len(waves))
        actual = tuple(int(value) for value in summary.groups())
        if actual != expected:
            return [problem("summary", line_no, f"統計為 {actual[0]} 個端點、{actual[1]} 個介面、{actual[2]} 個 Wave，實際為 {expected[0]} 個端點、{expected[1]} 個介面、{expected[2]} 個 Wave，請改正數字。")]
        return []
    return [problem("summary", None, "找不到「共盤點 N 個端點、N 個介面、N 個 Wave」統計行，請依樣板補上。")]


def check_plan(lines: list[str], requirements: set[str]) -> list[dict]:
    problems = []
    for line_no, line in enumerate(lines, start=1):
        leftover = LEFTOVER_PATTERN.search(line)
        if leftover:
            problems.append(problem("leftover", line_no, f"殘留樣板內容 {leftover.group(0)}，請填入實際內容或刪除該行。"))
    rows, table_problems = read_interfaces(lines)
    problems.extend(table_problems)
    endpoints_by_id, interface_problems = check_interfaces(rows, requirements)
    problems.extend(interface_problems)
    waves = read_waves(lines)
    if not waves:
        problems.append(problem("wave", None, "找不到「**Wave N — …**」標題，請依樣板在「### 分析 Wave」撰寫每個 Wave。"))
    problems.extend(check_waves(waves, endpoints_by_id))
    problems.extend(check_summary(lines, endpoints_by_id, waves))
    return problems


def finding_acs(plan_dir: Path) -> set[str]:
    """plan 的 features/acceptance/ 中標 @開發發現 的 AC 編號；它們和 spec.md 的需求一樣可以作為依據需求。"""
    found: set[str] = set()
    acceptance = plan_dir / "features" / "acceptance"
    for path in sorted(acceptance.glob("*.feature")) if acceptance.is_dir() else []:
        lines = path.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            matched = EXAMPLE_AC_PATTERN.match(line)
            above = index
            while matched and above > 0 and lines[above - 1].strip().startswith(("#", "@")):
                above -= 1
                if FINDING_TAG in lines[above].split():
                    found.add(matched.group(1))
    return found


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查 plan.md 的介面 ID、異動、依據需求（spec.md 的需求編號、本 plan 標 @開發發現 的 AC 或「技術：<原因>」）、Wave 分配、委派與統計數字是否一致，以及殘留佔位符。")
    parser.add_argument("plan_path", help="要檢查的 plan.md 路徑，例如 specs/plans/<plan 資料夾>/plan.md")
    parser.add_argument("--spec", help="對照的 spec.md 路徑；省略時使用 plan.md 同資料夾的 spec.md")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    plan_path = Path(args.plan_path)
    spec_path = Path(args.spec) if args.spec else plan_path.parent / "spec.md"
    for label, path in (("plan.md", plan_path), ("spec.md", spec_path)):
        if not path.is_file():
            print(
                f"錯誤：找不到 {label} 檔案 {path}。請傳入 plan.md 的路徑，"
                "例如 specs/plans/<plan 資料夾>/plan.md；spec.md 不在同資料夾時以 --spec 指定。",
                file=sys.stderr,
            )
            return 1
    requirements = set(REQUIREMENT_PATTERN.findall(spec_path.read_text(encoding="utf-8"))) | finding_acs(plan_path.parent)
    problems = check_plan(plan_path.read_text(encoding="utf-8").splitlines(), requirements)
    print(f"發現 {len(problems)} 個問題", file=sys.stderr)
    print(json.dumps({"ok": not problems, "problems": problems}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
