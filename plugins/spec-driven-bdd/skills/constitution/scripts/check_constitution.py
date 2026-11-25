# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""檢查憲法目錄的連結、產出物欄、條款 ID、共通條款引用、版本紀錄是否一致，以及是否殘留樣板佔位符。"""

import argparse
import sys
import json
import re
from pathlib import Path, PurePosixPath

LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)\s]+)\)")
CLAUSE_HEADING_PATTERN = re.compile(r"^## (C-[A-Z]+-\d{2}) -- ")
CLAUSE_ID_PATTERN = re.compile(r"C-[A-Z]+-\d{2}")
SHARED_PREFIX = "C-SH-"
REFERENCE_LINE_PATTERN = re.compile(r"^\*\*引用共通條款\*\*：(.*)$")
VERSION_LINE_PATTERN = re.compile(r"^\*\*版本\*\*：(\S+) ｜ \*\*最後修訂\*\*：(\S+)$")
SEMVER_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
LEFTOVER_PATTERN = re.compile(r"\{\{[^}]*\}\}|<!-- 重複(開始|結束)")
PRODUCT_TITLE_PATTERN = re.compile(r"^# (\S+) › (.+)$")
TRUTH_PREFIX = "specs/truth/"
PRODUCT_HINT = "產出物以位置表示：plan 的產出物寫 plan 資料夾內的路徑（例如 spec.md、ui/prototype/），truth 的產出物寫 specs/truth/ 起的路徑（例如 specs/truth/contracts/），資料夾以 / 結尾。"


def problem(kind: str, file: Path, line: int, message: str) -> dict:
    return {"type": kind, "file": file.as_posix(), "line": line, "message": message}


def parse_tables(lines: list[str]) -> dict[str, list[tuple[int, list[str]]]]:
    tables: dict[str, list[tuple[int, list[str]]]] = {}
    section = ""
    for line_no, line in enumerate(lines, start=1):
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if all(set(cell) <= {"-", " ", ":"} for cell in cells):
            continue
        tables.setdefault(section, []).append((line_no, cells))
    return {name: rows[1:] for name, rows in tables.items()}


def ids_in(text: str) -> list[str]:
    return CLAUSE_ID_PATTERN.findall(text)


def link_target(cell: str) -> str | None:
    match = LINK_PATTERN.search(cell)
    return match.group(2) if match else None


def read_clause_file(path: Path) -> tuple[list[str], list[str] | None, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    clauses = [m.group(1) for m in map(CLAUSE_HEADING_PATTERN.match, lines) if m]
    references = None
    for line in lines:
        match = REFERENCE_LINE_PATTERN.match(line)
        if match:
            references = ids_in(match.group(1))
    return clauses, references, lines


def check_links_and_leftovers(path: Path, lines: list[str]) -> list[dict]:
    problems = []
    for line_no, line in enumerate(lines, start=1):
        leftover = LEFTOVER_PATTERN.search(line)
        if leftover:
            problems.append(problem("leftover", path, line_no, f"殘留樣板內容 {leftover.group(0)}，請填入實際內容或刪除該行。"))
        if line.startswith("```"):
            continue
        for _, target in LINK_PATTERN.findall(line):
            if "://" in target or target.startswith("#"):
                continue
            resolved = (path.parent / target.split("#")[0]).resolve()
            if not resolved.exists():
                problems.append(problem("link", path, line_no, f"連結 {target} 指向不存在的檔案，請修正相對路徑或補上該檔案。"))
    return problems


def product_stem(product: str) -> str:
    name = product.rstrip("/").rsplit("/", 1)[-1]
    return name if product.endswith("/") else PurePosixPath(name).stem


def unusable_product(index: Path, line_no: int, product: str) -> dict | None:
    if not product or product == "—":
        return problem("product", index, line_no, f"目錄列的產出物不得空白。{PRODUCT_HINT}")
    if "`" in product:
        return problem("product", index, line_no, f"產出物「{product}」不加反引號，寫法要與條款檔標題相同。{PRODUCT_HINT}")
    if "\\" in product or product.startswith(("/", "./", "../")) or re.match(r"^[A-Za-z]:", product):
        return problem("product", index, line_no, f"產出物「{product}」必須是以 / 分隔的相對路徑。{PRODUCT_HINT}")
    return None


def check_product_format(index: Path, line_no: int, product: str) -> list[dict]:
    problems = []
    if product.startswith("specs/") and not product.startswith(TRUTH_PREFIX):
        problems.append(problem("product", index, line_no, f"產出物「{product}」不是 truth 的路徑；plan 的產出物寫 plan 資料夾內的路徑，不含 specs/plans/<plan>/。{PRODUCT_HINT}"))
    last = product.rstrip("/").rsplit("/", 1)[-1]
    if not product.endswith("/") and "." not in last:
        problems.append(problem("product", index, line_no, f"產出物「{product}」沒有副檔名：是資料夾時必須以 / 結尾，是檔案時寫出副檔名。"))
    return problems


def check_product_file(index: Path, line_no: int, product: str, target: str, lines: list[str]) -> list[dict]:
    problems = []
    parts = PurePosixPath(target).parts
    title_line = next((line for line in lines if line.startswith("# ")), "")
    match = PRODUCT_TITLE_PATTERN.match(title_line)
    if not match:
        problems.append(problem("product", index, line_no, f"{target} 的標題必須寫成「# <產出 skill> › {product}」，目前是「{title_line or '（沒有標題）'}」。"))
    else:
        title_skill, title_product = match.groups()
        if title_product != product:
            problems.append(problem("product", index, line_no, f"目錄的產出物「{product}」與 {target} 標題的「{title_product}」寫法不同，兩者必須相同；請以條款實際約束的產出物位置統一兩邊的寫法。{PRODUCT_HINT}"))
        if len(parts) == 3 and title_skill != parts[1]:
            problems.append(problem("product", index, line_no, f"{target} 標題的產出 skill「{title_skill}」與所在的資料夾 skills/{parts[1]}/ 不同，條款檔必須放在產出它的 skill 的資料夾。"))
    expected = product_stem(product)
    if len(parts) != 3 or parts[0] != "skills" or PurePosixPath(parts[2]).stem != expected:
        skill = parts[1] if len(parts) >= 2 else "<產出 skill>"
        problems.append(problem("product", index, line_no, f"產出物「{product}」的條款檔應為 skills/{skill}/{expected}.md（放在產出 skill 的資料夾，以產出物的檔名去掉副檔名或資料夾名命名），目前是 {target}。"))
    return problems


def check_index(root: Path) -> list[dict]:
    index = root / "CONSTITUTION.md"
    lines = index.read_text(encoding="utf-8").splitlines()
    tables = parse_tables(lines)
    problems = check_links_and_leftovers(index, lines)
    defined: dict[str, Path] = {}
    listed_files: set[Path] = set()

    shared_rows = tables.get("共通條款", [])
    shared_listed = set()
    for line_no, cells in shared_rows:
        if len(cells) < 2:
            continue
        clause_id, target = cells[0], link_target(cells[1])
        shared_listed.add(clause_id)
        if not clause_id.startswith(SHARED_PREFIX):
            problems.append(problem("shared", index, line_no, f"共通條款 {clause_id} 必須使用 {SHARED_PREFIX} 前綴。"))
        if not target or not (root / target).is_file():
            continue
        path = (root / target).resolve()
        listed_files.add(path)
        clauses, _, _ = read_clause_file(path)
        if clause_id not in clauses:
            problems.append(problem("clause", index, line_no, f"{clause_id} 未定義在 {target}，請改為該檔實際的條款標題 ID 或補上條款。"))

    seen_products: dict[str, int] = {}
    for line_no, cells in tables.get("目錄", []):
        if len(cells) < 4:
            problems.append(problem("table", index, line_no, "目錄列必須有產出物、憲法檔、條款、引用共通條款四欄。"))
            continue
        product = cells[0]
        unusable = unusable_product(index, line_no, product)
        if unusable:
            problems.append(unusable)
        else:
            problems += check_product_format(index, line_no, product)
        if product in seen_products:
            problems.append(problem("product", index, line_no, f"產出物「{product}」已列在第 {seen_products[product]} 行，每份產出物只能有一列，請把條款合併到同一個條款檔。"))
        else:
            seen_products[product] = line_no
        target = link_target(cells[1])
        if not target or not (root / target).is_file():
            continue
        path = (root / target).resolve()
        listed_files.add(path)
        clauses, references, clause_lines = read_clause_file(path)
        if not unusable:
            problems += check_product_file(index, line_no, product, target, clause_lines)
        listed_clauses = ids_in(cells[2])
        if sorted(listed_clauses) != sorted(clauses):
            problems.append(problem("clause", index, line_no, f"目錄列的條款 {listed_clauses or '—'} 與 {target} 定義的條款 {clauses or '—'} 不一致，請以憲法檔為準更新目錄。"))
        listed_refs = ids_in(cells[3])
        if sorted(listed_refs) != sorted(references or []):
            problems.append(problem("shared", index, line_no, f"目錄列的引用共通條款 {listed_refs or '—'} 與 {target} 的「引用共通條款」{references or '—'} 不一致；沒有引用時兩邊都不得出現。"))
        for ref in listed_refs:
            if ref not in shared_listed:
                problems.append(problem("shared", index, line_no, f"引用的 {ref} 不在共通條款表中，請補上共通條款或移除引用。"))

    for path in sorted((root / "skills").rglob("*.md")) + sorted((root / "shared").rglob("*.md")):
        resolved = path.resolve()
        clauses, _, file_lines = read_clause_file(resolved)
        problems += check_links_and_leftovers(path, file_lines)
        if resolved not in listed_files:
            problems.append(problem("unlisted", path, 1, "此條款檔沒有列在 CONSTITUTION.md 的目錄或共通條款表，請補上對應列或刪除此檔。"))
        is_shared = (root / "shared") in path.parents
        for clause_id in clauses:
            if clause_id.startswith(SHARED_PREFIX) != is_shared:
                problems.append(problem("shared", path, 1, f"{clause_id} 的前綴與所在位置不符：{SHARED_PREFIX} 只能用於 shared/ 底下的共通條款。"))
            if clause_id in defined:
                problems.append(problem("duplicate", path, 1, f"{clause_id} 已定義在 {defined[clause_id].as_posix()}，條款 ID 必須唯一。"))
            defined[clause_id] = path

    problems += check_versions(index, lines, tables.get("修訂紀錄", []))
    return problems


def check_versions(index: Path, lines: list[str], revisions: list[tuple[int, list[str]]]) -> list[dict]:
    header = next((VERSION_LINE_PATTERN.match(line) for line in lines if VERSION_LINE_PATTERN.match(line)), None)
    if not header:
        return [problem("version", index, 1, "標題下缺少「**版本**：X.Y.Z ｜ **最後修訂**：YYYY-MM-DD」一行。")]
    if not revisions:
        return [problem("version", index, 1, "修訂紀錄表沒有任何一列，每次增量都必須新增一列。")]
    problems = []
    previous = None
    for line_no, cells in revisions:
        match = SEMVER_PATTERN.match(cells[0])
        if not match:
            problems.append(problem("version", index, line_no, f"版本 {cells[0]} 必須是 主版號.次版號.修訂號 格式。"))
            continue
        current = tuple(int(part) for part in match.groups())
        if previous and current <= previous:
            problems.append(problem("version", index, line_no, f"版本 {cells[0]} 必須大於上一列，修訂紀錄依版本由舊到新排列。"))
        previous = current
    last_line, last = revisions[-1]
    if header.group(1) != last[0] or header.group(2) != last[1]:
        problems.append(problem("version", index, last_line, f"標題的版本與最後修訂 {header.group(1)}／{header.group(2)} 必須等於修訂紀錄最後一列 {last[0]}／{last[1]}。"))
    return problems


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查憲法目錄的連結、產出物欄的寫法、條款 ID、共通條款引用與版本紀錄的一致性。")
    parser.add_argument("constitution_dir", help="憲法目錄路徑，例如 .claude/constitution")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    root = Path(args.constitution_dir)
    if not (root / "CONSTITUTION.md").is_file():
        print(
            f"錯誤：找不到 {root / 'CONSTITUTION.md'}。請傳入憲法目錄路徑，例如 .claude/constitution",
            file=sys.stderr,
        )
        return 1
    problems = check_index(root)
    print(f"發現 {len(problems)} 個問題", file=sys.stderr)
    print(json.dumps({"ok": not problems, "problems": problems}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
