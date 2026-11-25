# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""從 specs/truth/features/.verify-result.json 讀出範疇與指定端點資料夾每個 Example 的上次結果，並判定範疇的結果可否沿用：範疇內每個 Example 都由結果檔記錄的最後一次執行產生，且目前的專案檔案清單摘要與該次執行結束時相同。"""

import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # 匯入同目錄的腳本時不在 skill 內留下 __pycache__
from run_suite import files_changed_after, project_snapshot  # noqa: E402
from verify_result import FeatureIndex, ReportError, scope_records  # noqa: E402

LISTED_LIMIT = 20


def location(item: dict) -> str:
    return f"{item['feature']}:{item['line']}"


def summarize(records: dict[str, dict], previous: dict[str, dict], run_id: str | None) -> dict:
    """依 Example key 對回上次結果，統計通過、失敗、沒有結果與不是最後一次執行產生的 Example。"""
    passed, failed, missing, stale = [], [], [], []
    for key, record in sorted(records.items(), key=lambda kv: (kv[1]["feature"], kv[1]["line"])):
        before = previous.get(key)
        if before is None:
            missing.append(location(record))
            continue
        if run_id is None or before.get("run") != run_id:
            stale.append(location(before))
        if before["status"] == "passed":
            passed.append(location(before))
        else:
            failed.append({"location": location(before), "rule": before["rule"], "title": before["title"],
                           "message": before.get("message")})
    return {
        "examples": len(records),
        "passed": len(passed),
        "failed": failed,
        "missing": missing,
        "not_from_last_run": stale[:LISTED_LIMIT],
        "not_from_last_run_count": len(stale),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="讀出範疇與端點資料夾每個 Example 的上次結果，並判定範疇的結果可否沿用（不執行任何測試、不寫任何檔案）。"
        "可沿用的條件：結果檔存在且有 last_run、範疇內每個 Example 都有結果且 run 等於 last_run 的代號、"
        "目前的專案檔案清單摘要與 last_run 結束時相同。任一條件不成立時 reusable 為 false 並列出理由；"
        "結果檔不存在、格式毀損或為舊版（沒有 last_run 或 run）時也只回報不可沿用，不以錯誤結束。"
    )
    parser.add_argument("scope", nargs="+",
                        help="範疇，格式同 resolve_scope.py：端點資料夾、feature 路徑、feature 路徑:行號[:行號…] 或 feature 路徑 ＞ Rule「名稱」[、Rule「名稱」…]"
                        "（含空白時整段以引號包成一個參數），相對於 --root，可多個")
    parser.add_argument("--folder", action="append", default=[], metavar="DIR",
                        help="另外讀出上次結果的端點資料夾（快速端點傳範疇所在的端點資料夾），相對於 --root；只回報，不影響可否沿用")
    parser.add_argument("--root", default=".", help="專案根目錄（預設為目前目錄）")
    parser.add_argument("--result", default="specs/truth/features/.verify-result.json", help="結果檔，相對於 --root（預設 specs/truth/features/.verify-result.json）")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"錯誤：--root {args.root} 不存在，請傳入專案根目錄（含 specs/ 的目錄）。", file=sys.stderr)
        return 1
    index = FeatureIndex(root)
    try:
        scope = scope_records(args.scope, index, "範疇")
        folder = scope_records(args.folder, index, "--folder") if args.folder else {}
    except ReportError as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1

    reasons: list[str] = []
    result_path = root / args.result
    previous: dict[str, dict] = {}
    last_run = None
    if not result_path.is_file():
        reasons.append(f"結果檔 {args.result} 不存在")
    else:
        try:
            data = json.loads(result_path.read_text(encoding="utf-8"))
            previous = {item["key"]: item for item in data["examples"]}
            last_run = data.get("last_run")
        except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError) as error:
            reasons.append(f"結果檔 {args.result} 格式不正確（{error}）")
        if not reasons and last_run is None:
            reasons.append("結果檔沒有 last_run（舊版結果檔，或上次存回時沒有以 --run 傳入執行紀錄）")

    run_id = last_run.get("run_id") if isinstance(last_run, dict) else None
    scope_view = summarize(scope, previous, run_id)
    if scope_view["missing"]:
        reasons.append(f"範疇內 {len(scope_view['missing'])} 個 Example 沒有上次結果（新增或從未執行）")
    if run_id is not None and scope_view["not_from_last_run_count"]:
        reasons.append(f"範疇內 {scope_view['not_from_last_run_count']} 個 Example 的結果不是最後一次執行（{run_id}）產生")

    snapshot_matches = None
    changed: list[str] = []
    if run_id is not None:
        recorded = last_run.get("snapshot") or {}
        now = project_snapshot(root)
        snapshot_matches = now["digest"] == recorded.get("digest")
        if not snapshot_matches:
            changed = files_changed_after(root, int(recorded.get("taken_at_ns", 0)))
            reasons.append(
                f"最後一次執行（{run_id}）結束後專案檔案有變動（檔案數 {recorded.get('files')} → {now['files']}；"
                f"較新的檔案：{changed or '無，可能是刪除'}）"
            )

    output = {
        "result_file": args.result,
        "result_exists": result_path.is_file(),
        "last_run": None if run_id is None else {
            "run_id": run_id, "finished_at": last_run.get("finished_at"), "ran_scope": last_run.get("ran_scope")},
        "snapshot_matches": snapshot_matches,
        "reusable": not reasons,
        "reasons": reasons,
        "scope": scope_view,
        "folder": None if not args.folder else summarize(folder, previous, run_id),
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
