# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""依序（序列）執行呼叫者傳入的測試指令，各自設逾時並計時，輸出每個指令的結束碼、耗時、逾時與紀錄檔位置；全部結束後記錄專案檔案清單摘要，寫出執行紀錄供 verify_result.py 存回與 baseline.py 判定結果可否沿用。指令由呼叫者依專案測試設定決定，本腳本不判斷用哪個測試工具。"""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# 專案檔案清單摘要的排除項目：只在專案根目錄排除的資料夾（skill、備份、版本庫）與 Markdown 文件（說明與待辦清單不影響測試結果），任何深度都排除的套件安裝目錄；
# specs/ 底下只計 specs/truth 的 .feature（plan 的文件與驗收案例、dsl.md、用語表與結果檔不影響測試結果，勾選任務或新增驗收案例不會讓結果失效）
ROOT_EXCLUDED = {".claude", ".backup", ".git"}
ROOT_EXCLUDED_SUFFIXES = (".md",)
ANYWHERE_EXCLUDED = {"node_modules", ".venv"}
SPECS_DIR = "specs"
TRUTH_DIR = "truth"


def snapshot_entries(root: Path) -> list[tuple[str, int, int]]:
    """列出納入摘要的每個檔案（相對路徑、大小、修改時間 ns），依路徑排序。"""
    entries = []
    for current, dirs, files in os.walk(root):
        here = Path(current)
        rel_dir = here.relative_to(root)
        dirs[:] = sorted(
            d for d in dirs
            if d not in ANYWHERE_EXCLUDED and not (rel_dir == Path(".") and d in ROOT_EXCLUDED)
        )
        in_specs = rel_dir.parts[:1] == (SPECS_DIR,)
        in_truth = rel_dir.parts[:2] == (SPECS_DIR, TRUTH_DIR)
        at_root = rel_dir == Path(".")
        for name in files:
            if in_specs and not (in_truth and name.endswith(".feature")):
                continue
            if at_root and name.lower().endswith(ROOT_EXCLUDED_SUFFIXES):
                continue
            path = here / name
            try:
                stat = path.stat()
            except OSError:
                continue  # 列舉後立即被刪除的暫存檔
            entries.append(((rel_dir / name).as_posix(), stat.st_size, stat.st_mtime_ns))
    entries.sort()
    return entries


def project_snapshot(root: Path) -> dict:
    """專案檔案清單摘要：路徑、大小、修改時間的雜湊，能抓到修改、新增、刪除與時間倒退。"""
    entries = snapshot_entries(root)
    digest = hashlib.sha256()
    for path, size, mtime in entries:
        digest.update(f"{path}\t{size}\t{mtime}\n".encode("utf-8"))
    return {"digest": digest.hexdigest(), "files": len(entries), "taken_at_ns": time.time_ns()}


def files_changed_after(root: Path, since_ns: int, limit: int = 10) -> list[str]:
    """修改時間晚於 since_ns 的檔案（只作為摘要不同時的提示，刪除的檔案不會出現）。"""
    return [path for path, _, mtime in snapshot_entries(root) if mtime > since_ns][:limit]


def kill_tree(process: subprocess.Popen) -> None:
    """逾時時結束指令與它啟動的子行程（npm、node、瀏覽器）。"""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
    else:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def run_step(name: str, cwd: Path, timeout: float, command: str, env: dict, log: Path) -> dict:
    started = time.monotonic()
    timed_out = False
    exit_code: int | None = None
    with log.open("w", encoding="utf-8", errors="replace") as handle:
        process = subprocess.Popen(
            command, shell=True, cwd=cwd, env=env, stdout=handle, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, start_new_session=(os.name != "nt"),
        )
        try:
            exit_code = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            kill_tree(process)
            process.wait()
    seconds = round(time.monotonic() - started, 1)
    print(f"[{name}] {'逾時' if timed_out else '結束碼 ' + str(exit_code)}，{seconds} 秒", file=sys.stderr)
    return {"name": name, "cwd": cwd.as_posix(), "command": command, "exit_code": exit_code, "timed_out": timed_out, "seconds": seconds, "log": log.as_posix()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="依序執行測試指令並輸出每個指令的結束碼與耗時。指令之間序列執行（它們共用同一個測試資料庫，不得同時執行）；"
        "測試失敗時結束碼非 0 是正常結果，只有逾時或無法啟動才讓本腳本以非零結束。"
        "全部指令結束後（含逾時）在 --out 寫出執行紀錄 run-<代號>.json：每個指令的結果與專案檔案清單摘要（路徑、大小、修改時間；"
        "排除根目錄的 .claude、.backup、.git 與 Markdown 文件（*.md），任何深度的 node_modules、.venv，以及 specs/ 底下 specs/truth 的 .feature 以外的檔案），"
        "stdout 的 run_record 是它的路徑，存回結果時以 verify_result.py --run 傳入。"
    )
    parser.add_argument("--out", required=True, help="報告與紀錄檔的輸出目錄（專案外的暫存目錄，會自動建立）；指令與環境變數值中的 {out} 會換成它的絕對路徑")
    parser.add_argument("--step", nargs=4, action="append", default=[], metavar=("NAME", "CWD", "TIMEOUT_SEC", "COMMAND"),
                        help="要執行的指令：名稱、工作目錄、逾時秒數、指令字串（整段以引號包住）；依出現順序執行，可重複")
    parser.add_argument("--root", default=".", help="專案根目錄（預設為目前目錄），全部指令結束後在此計算檔案清單摘要寫入執行紀錄")
    parser.add_argument("--env", nargs=2, action="append", default=[], metavar=("NAME", "KEY=VALUE"),
                        help="只給名稱為 NAME 的指令設定環境變數，例如 --env e2e PLAYWRIGHT_JSON_OUTPUT_NAME={out}/e2e.json；可重複")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    if not args.step:
        print("錯誤：沒有傳入任何 --step。\n用法：uv run scripts/run_suite.py --out $TMP/bdd-verify --step backend backend 600 \"uv run --no-sync python -m behave -D suite=api -f json -o {out}/backend.json\"", file=sys.stderr)
        return 1
    names = [step[0] for step in args.step]
    if len(set(names)) != len(names):
        print(f"錯誤：--step 的名稱不得重複（{names}）；名稱用來命名紀錄檔與對應 --env。", file=sys.stderr)
        return 1
    unknown = [name for name, _ in args.env if name not in names]
    if unknown:
        print(f"錯誤：--env 指定的名稱 {unknown} 不在 --step 的名稱 {names} 內，請改用相同名稱。", file=sys.stderr)
        return 1
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"錯誤：--root {args.root} 不存在，請傳入專案根目錄（含 specs/ 的目錄）。", file=sys.stderr)
        return 1
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    placeholder = out.as_posix()
    results = []
    failed_to_finish = False
    suite_started = time.monotonic()
    for name, cwd_text, timeout_text, command in args.step:
        cwd = Path(cwd_text).resolve()
        try:
            timeout = float(timeout_text)
        except ValueError:
            print(f"錯誤：--step {name} 的逾時 {timeout_text} 不是秒數，請傳入數字，例如 600。", file=sys.stderr)
            return 1
        if not cwd.is_dir():
            print(f"錯誤：--step {name} 的工作目錄 {cwd_text} 不存在，請傳入存在的目錄。", file=sys.stderr)
            return 1
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"  # Windows 下 Python 輸出含中文時避免 cp950 編碼錯誤
        for env_name, assignment in args.env:
            if env_name == name:
                key, sep, value = assignment.partition("=")
                if not sep:
                    print(f"錯誤：--env {env_name} {assignment} 缺少 =，請寫成 KEY=VALUE。", file=sys.stderr)
                    return 1
                env[key] = value.replace("{out}", placeholder)
        result = run_step(name, cwd, timeout, command.replace("{out}", placeholder), env, out / f"{name}.log")
        failed_to_finish |= result["timed_out"]
        results.append(result)
    finished = datetime.now(timezone.utc)
    run_id = finished.strftime("%Y%m%dT%H%M%S%fZ")
    record = {
        "run_id": run_id,
        "finished_at": finished.isoformat(),
        "root": root.as_posix(),
        "timed_out": failed_to_finish,
        "snapshot": project_snapshot(root),  # 全部指令結束後取樣：重建、bddgen、測試報告的變動都已含在內
        "steps": results,
    }
    record_path = out / f"run-{run_id}.json"
    record_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out_dir": placeholder, "run_record": record_path.as_posix(), "run_id": run_id, "total_seconds": round(time.monotonic() - suite_started, 1), "steps": results}, ensure_ascii=False, indent=2))
    if failed_to_finish:
        print("錯誤：有指令逾時被結束，其報告可能不存在或不完整；請加長逾時或先排查卡住的原因，不得把逾時當成測試通過。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
