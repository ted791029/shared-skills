# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""列出（預設）或結束（--kill）專案目錄底下由測試啟動而殘留的 uvicorn、node、python、瀏覽器行程。只處理指令列或執行檔位於專案根目錄內的行程，以及它們的後代；不處理專案外的行程，也不處理本腳本自己與其祖先行程。"""

import argparse
import json
import os
import signal
import subprocess
import sys
from pathlib import Path

# 行程名稱（去掉 .exe、小寫）白名單：只有這些名稱的行程才可能被列出
CANDIDATE_NAMES = {
    "py", "python", "pythonw", "python3", "uvicorn", "node", "npm", "npx", "chrome", "chromium", "msedge",
    "headless_shell", "chrome-headless-shell", "firefox", "playwright", "behave", "vitest",
}
# 指令列含這些片段的行程屬於工具與 agent 本身，不列出
SKILLS_ROOT = Path(__file__).resolve().parents[2].as_posix().lower() + "/"
PROTECTED_FRAGMENTS = ("/.claude/", SKILLS_ROOT, "cleanup_test_processes.py")


def list_processes() -> list[dict]:
    """列出所有行程（pid、ppid、name、exe、cmd）。Python 標準函式庫沒有列舉行程的功能，只能呼叫各平台的行程工具。"""
    if os.name == "nt":
        command = (
            "[Console]::OutputEncoding = [Text.Encoding]::UTF8; Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine "
            "| ConvertTo-Json -Compress"
        )
        output = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if output.returncode != 0 or not output.stdout.strip():
            raise RuntimeError(f"無法列出行程：{output.stderr.strip() or '沒有輸出'}。請確認 powershell 可用。")
        data = json.loads(output.stdout)
        data = data if isinstance(data, list) else [data]
        return [
            {"pid": int(p["ProcessId"]), "ppid": int(p["ParentProcessId"] or 0), "name": p["Name"] or "",
             "exe": p["ExecutablePath"] or "", "cmd": p["CommandLine"] or ""}
            for p in data
        ]
    output = subprocess.run(["ps", "-eo", "pid=,ppid=,comm=,args="], capture_output=True, text=True, errors="replace")
    if output.returncode != 0:
        raise RuntimeError(f"無法列出行程：{output.stderr.strip()}。請確認 ps 可用。")
    processes = []
    for line in output.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) >= 3 and parts[0].isdigit() and parts[1].isdigit():
            processes.append({"pid": int(parts[0]), "ppid": int(parts[1]), "name": parts[2],
                              "exe": "", "cmd": parts[3] if len(parts) > 3 else ""})
    return processes


def normalize(text: str) -> str:
    return text.replace("\\", "/").lower()


def short_name(name: str) -> str:
    name = Path(name).name.lower()
    return name[:-4] if name.endswith(".exe") else name


def ancestors_of(pid: int, by_pid: dict[int, dict]) -> set[int]:
    chain = set()
    while pid in by_pid and pid not in chain:
        chain.add(pid)
        pid = by_pid[pid]["ppid"]
    return chain


def find_residual(root: Path, processes: list[dict]) -> list[dict]:
    root_text = normalize(root.resolve().as_posix()).rstrip("/") + "/"
    by_pid = {p["pid"]: p for p in processes}
    excluded = ancestors_of(os.getpid(), by_pid)
    children: dict[int, list[int]] = {}
    for process in processes:
        children.setdefault(process["ppid"], []).append(process["pid"])

    def candidate(process: dict) -> bool:
        if process["pid"] in excluded or short_name(process["name"]) not in CANDIDATE_NAMES:
            return False
        return not any(fragment in normalize(process["cmd"]) for fragment in PROTECTED_FRAGMENTS)

    matched: dict[int, str] = {}
    for process in processes:
        if candidate(process) and root_text in normalize(process["cmd"] + " " + process["exe"]) + "/":
            matched[process["pid"]] = "指令列或執行檔位於專案目錄內"
    queue = list(matched)
    while queue:
        for child in children.get(queue.pop(), []):
            if child not in matched and candidate(by_pid[child]):
                matched[child] = "專案內殘留行程的後代"
                queue.append(child)
    return [
        {"pid": pid, "name": by_pid[pid]["name"], "reason": reason, "cmd": by_pid[pid]["cmd"][:200]}
        for pid, reason in sorted(matched.items())
    ]


def kill(pid: int) -> bool:
    try:
        if os.name == "nt":
            return subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True).returncode == 0
        os.kill(pid, signal.SIGKILL)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="列出（預設）或結束（--kill）專案目錄底下殘留的 uvicorn、node、python、瀏覽器測試行程；不處理專案外的行程。"
    )
    parser.add_argument("--root", default=".", help="專案根目錄（預設為目前目錄）")
    parser.add_argument("--kill", action="store_true", help="結束列出的行程；不傳時只列出")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"錯誤：專案根目錄 {root.as_posix()} 不存在，請以 --root 指定專案根目錄。", file=sys.stderr)
        return 1
    try:
        residual = find_residual(root, list_processes())
    except (RuntimeError, json.JSONDecodeError) as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1
    killed, failed = [], []
    if args.kill:
        for item in residual:
            (killed if kill(item["pid"]) else failed).append(item["pid"])
    print(f"專案內殘留測試行程 {len(residual)} 個" + (f"；已結束 {len(killed)}、失敗 {len(failed)}" if args.kill else "（未結束，加 --kill 才結束）"), file=sys.stderr)
    print(json.dumps({"root": root.as_posix(), "residual": residual, "killed": killed, "kill_failed": failed}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
