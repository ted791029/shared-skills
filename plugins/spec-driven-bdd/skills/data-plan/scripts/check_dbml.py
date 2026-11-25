# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""以官方的 DBML 工具（@dbml/cli）解析資料模型的入口檔與它匯入的模組檔，列出語法錯誤、找不到的資料表與檔案，以及入口檔沒有匯入的模組檔。"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REUSE_PATTERN = re.compile(r"^\s*reuse\s+.*?\bfrom\s+['\"]\./([^'\"]+)['\"]", re.MULTILINE)
TABLE_PATTERN = re.compile(r"^\s*Table\s+\S+", re.MULTILINE)
LOCATED_PATTERN = re.compile(r"^\s*(?P<file>[^()\n]+?\.dbml)\((?P<line>\d+),(?P<column>\d+)\):\s*(?P<message>.+)$")
MISSING_PATTERN = re.compile(r"ENOENT: no such file or directory, open '(?P<file>[^']+)'")
TIMESTAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z$")
TIMEOUT_SECONDS = 300


def problem(kind: str, file: str | None, line: int | None, message: str) -> dict:
    return {"type": kind, "file": file, "line": line, "message": message}


def unimported_modules(entry: Path) -> tuple[list[str], list[dict]]:
    imported = {name.removesuffix(".dbml") for name in REUSE_PATTERN.findall(entry.read_text(encoding="utf-8"))}
    modules = sorted(path.stem for path in entry.parent.glob("*.dbml") if path != entry)
    problems = [
        problem(
            "unimported", f"{name}.dbml", None,
            f"入口檔 {entry.name} 沒有匯入模組檔 {name}.dbml，這個檔案的資料表不會納入資料模型。請在入口檔加上一行 reuse * from './{name}'，或刪除這個檔案。",
        )
        for name in modules if name not in imported
    ]
    return modules, problems


def run_cli(entry: Path, npx: str) -> tuple[int, str, str, str]:
    """官方工具把錯誤寫進目前目錄的 dbml-error.log 且 exit code 仍為 0，因此在暫存目錄執行並讀回該檔。"""
    with tempfile.TemporaryDirectory() as workdir:
        process = subprocess.run(
            [npx, "-p", "@dbml/cli", "dbml2sql", str(entry), "--mysql"],
            cwd=workdir, capture_output=True, stdin=subprocess.DEVNULL, timeout=TIMEOUT_SECONDS,
        )
        log_path = Path(workdir) / "dbml-error.log"
        log = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
    return (
        process.returncode,
        process.stdout.decode("utf-8", errors="replace"),
        process.stderr.decode("utf-8", errors="replace"),
        log,
    )


def parse_log(log: str, entry: Path) -> list[dict]:
    problems = []
    seen = set()
    for raw in log.splitlines():
        line = raw.strip()
        if not line or TIMESTAMP_PATTERN.match(line) or line.startswith("at "):
            continue
        located = LOCATED_PATTERN.match(line)
        missing = MISSING_PATTERN.search(line)
        if located:
            name = Path(located.group("file")).name
            message = located.group("message").strip()
            kind = "reference" if "does not exist" in message or "contains errors" in message else "syntax"
            item = problem(kind, name, int(located.group("line")), f"{message}。請修正 {name} 第 {located.group('line')} 行。")
        elif missing:
            name = Path(missing.group("file").replace("\\", "/")).name
            item = problem("missing-file", name, None, f"找不到被匯入的檔案 {name}。請建立這個模組檔，或修正 use、reuse 的路徑。")
        else:
            item = problem("tool", entry.name, None, f"DBML 工具回報：{line}")
        key = (item["type"], item["file"], item["line"], item["message"])
        if key not in seen:
            seen.add(key)
            problems.append(item)
    return problems


def check_dbml(entry: Path, npx: str) -> dict:
    modules, problems = unimported_modules(entry)
    returncode, stdout, stderr, log = run_cli(entry, npx)
    problems.extend(parse_log(log, entry))
    tables = len(re.findall(r"^CREATE TABLE", stdout, re.MULTILINE))
    declared = sum(len(TABLE_PATTERN.findall(path.read_text(encoding="utf-8"))) for path in entry.parent.glob("*.dbml"))
    if returncode != 0:
        problems.append(problem("tool", entry.name, None, f"DBML 工具以 exit code {returncode} 結束：{stderr.strip()[:400]}"))
    elif tables == 0 and declared > 0 and not problems:
        problems.append(problem("tool", entry.name, None, f"DBML 工具沒有輸出任何資料表，也沒有回報錯誤，無法確認資料模型可以解析。工具的訊息：{stderr.strip()[:400]}"))
    return {"ok": not problems, "modules": modules, "tables": tables, "problems": problems}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="以官方的 DBML 工具解析資料模型的入口檔與它匯入的模組檔，列出語法錯誤、找不到的資料表與沒有被匯入的模組檔。")
    parser.add_argument("entry_path", help="資料模型的入口檔，例如 specs/truth/data/data-model.dbml")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    entry = Path(args.entry_path).resolve()
    if not entry.is_file():
        print(
            f"錯誤：找不到資料模型的入口檔 {args.entry_path}。請傳入入口檔的路徑，例如 specs/truth/data/data-model.dbml。",
            file=sys.stderr,
        )
        return 1
    npx = shutil.which("npx")
    if not npx:
        print(
            "錯誤：找不到 npx，無法執行官方的 DBML 工具 @dbml/cli。請先安裝 Node.js 18 以上的版本後重新執行。",
            file=sys.stderr,
        )
        return 1
    try:
        result = check_dbml(entry, npx)
    except subprocess.TimeoutExpired:
        print(
            f"錯誤：DBML 工具在 {TIMEOUT_SECONDS} 秒內沒有結束。第一次執行需要從 npm 下載 @dbml/cli，請確認網路後重新執行。",
            file=sys.stderr,
        )
        return 1
    print(f"發現 {len(result['problems'])} 個問題", file=sys.stderr)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
