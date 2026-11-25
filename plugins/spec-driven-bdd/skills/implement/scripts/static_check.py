# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""以呼叫者指定的指令對檔案執行語法檢查與 lint，JSON 與 Python 未指定指令時使用內建檢查，並列出沒有任何檢查涵蓋的檔案。"""

import argparse
import sys
import json
import py_compile
import shlex
import shutil
import subprocess
from pathlib import Path

OUTPUT_LIMIT = 4000
FILE_PLACEHOLDER = "{file}"


def run(command: list[str], cwd: Path) -> tuple[bool, str]:
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode == 0, output[-OUTPUT_LIMIT:]


def resolve(template: str, file: Path | None = None) -> tuple[list[str] | None, str]:
    tokens = shlex.split(template)
    if not tokens:
        return None, "指令為空字串"
    executable = shutil.which(tokens[0])
    if executable is None:
        return None, f"找不到 {tokens[0]} 指令，請安裝 techstack.md 指定的工具或改用已安裝的指令"
    tokens[0] = executable
    if file is not None:
        tokens = [token.replace(FILE_PLACEHOLDER, str(file)) for token in tokens]
    return tokens, ""


def parse_syntax(specs: list[str]) -> dict[str, str]:
    commands = {}
    for spec in specs:
        extensions, separator, template = spec.partition("=")
        if not separator or not template.strip():
            raise ValueError(f"--syntax「{spec}」格式錯誤，應為「副檔名=指令」，例如 \".js,.mjs=node --check {{file}}\"")
        if FILE_PLACEHOLDER not in template:
            raise ValueError(f"--syntax「{spec}」的指令缺少 {{file}}，請以 {{file}} 標示要代入檔案路徑的位置")
        for extension in extensions.split(","):
            extension = extension.strip().lower()
            commands[extension if extension.startswith(".") else f".{extension}"] = template.strip()
    return commands


def builtin_check(path: Path) -> tuple[str, bool, str] | None:
    suffix = path.suffix.lower()
    if suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
            return "json", True, ""
        except json.JSONDecodeError as error:
            return "json", False, f"JSON 格式錯誤：第 {error.lineno} 行第 {error.colno} 欄，{error.msg}"
    if suffix == ".py":
        try:
            py_compile.compile(str(path), doraise=True)
            return "py_compile", True, ""
        except py_compile.PyCompileError as error:
            return "py_compile", False, str(error)
    return None


def check_file(path: Path, root: Path, commands: dict[str, str]) -> dict:
    result = {"path": str(path), "check": None, "ok": None, "reason": "", "output": ""}
    if not path.is_file():
        result.update(check="exists", ok=False, output=f"找不到檔案 {path}，請確認任務是否已建立該檔案。")
        return result
    template = commands.get(path.suffix.lower())
    if template is None:
        builtin = builtin_check(path)
        if builtin is None:
            result["reason"] = f"沒有 {path.suffix or '無副檔名'} 檔案的語法檢查指令"
            return result
        check, ok, output = builtin
        result.update(check=check, ok=ok, output=output)
        return result
    command, reason = resolve(template, path)
    result["check"] = template
    if command is None:
        result["reason"] = reason
        return result
    ok, output = run(command, root)
    result.update(ok=ok, output=output)
    return result


def check_lint(template: str, root: Path) -> dict:
    result = {"command": template, "ran": False, "ok": None, "reason": "", "output": ""}
    command, reason = resolve(template)
    if command is None:
        result["reason"] = reason
        return result
    ok, output = run(command, root)
    result.update(ran=True, ok=ok, output=output)
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="以指定的指令對檔案執行語法檢查與 lint，並列出沒有任何檢查涵蓋的檔案。")
    parser.add_argument("files", nargs="+", help="任務建立或修改的檔案路徑")
    parser.add_argument("--root", default=".", help="專案根目錄，指令在此目錄執行，預設為目前目錄")
    parser.add_argument(
        "--syntax",
        action="append",
        default=[],
        help="副檔名=指令，指令以 {file} 代入檔案路徑，可重複指定，例如 \".js,.mjs=node --check {file}\"",
    )
    parser.add_argument("--lint", action="append", default=[], help="在專案根目錄執行的 lint 指令，可重複指定，例如 \"npm run lint\"")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"錯誤：找不到專案根目錄 {root}，請以 --root 指定 repo 根目錄。", file=sys.stderr)
        return 1
    try:
        commands = parse_syntax(args.syntax)
    except ValueError as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1
    files = [check_file(Path(name), root, commands) for name in args.files]
    lint = [check_lint(template, root) for template in args.lint]
    unchecked = [{"path": item["path"], "reason": item["reason"]} for item in files if item["ok"] is None]
    failed = any(item["ok"] is False for item in files) or any(item["ok"] is False for item in lint)
    print(json.dumps({
        "passed": not failed,
        "files": files,
        "lint": lint,
        "unchecked": unchecked,
        "lint_ran": any(item["ran"] for item in lint),
    }, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
