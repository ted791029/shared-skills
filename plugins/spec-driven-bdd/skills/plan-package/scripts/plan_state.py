# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""管理 plan package 的狀態：open 以既有最大編號加一開立 plan 資料夾並寫入 .plan.json（狀態、種類、基準 commit），不是 git 倉庫、已有進行中的 plan 或 truth 有未 commit 的修改時拒絕；check 確認目標是進行中的 plan，輸出路徑、基準、種類、待補跑的擁有者與呼叫者自己的輸入差異，沒有待補跑時一併執行交叉檢查；abandon 只輸出還原步驟；files 列出交付時會被 commit 的檔案；deliver 在沒有待補跑且交付階段的交叉檢查通過時，把進行中的 plan 標為已交付並以指定的訊息建立單一 commit，不推送。"""

import argparse
import datetime
import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cross_check  # noqa: E402
import plan_trace  # noqa: E402

PLAN_DIR_PATTERN = re.compile(r"^(\d{3})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OWNER_PATTERN = re.compile(r"^##\s+(.+?)\s*[（(]\s*(.+?)\s*[）)]\s*$")
PLAN_FILE = ".plan.json"
IN_PROGRESS = "進行中"
DELIVERED = "已交付"
KINDS = ("需求", "技術修正")
NEXT_OPEN = "以 /specify 開立新的 plan；只為技術修正時以 plan-package open --kind 技術修正 開立"


class Abort(Exception):
    """無法繼續執行的環境或輸入錯誤。"""


class Refused(Exception):
    """腳本拒絕執行；每一項含原因與下一步。"""

    def __init__(self, refusals: list[dict]):
        super().__init__("refused")
        self.refusals = refusals


def run_git(cwd: Path, *args: str, stdin: bytes | None = None) -> tuple[int, str, str]:
    try:
        result = subprocess.run(["git", "-c", "core.quotepath=false", *args], cwd=cwd, input=stdin, capture_output=True)
    except FileNotFoundError:
        raise Abort("找不到 git 指令。plan 的基準與交付都以 git 為準，請先安裝 git。")
    return result.returncode, result.stdout.decode("utf-8", errors="replace"), result.stderr.decode("utf-8", errors="replace").strip()


def git(cwd: Path, *args: str) -> str:
    code, out, err = run_git(cwd, *args)
    if code != 0:
        raise Abort(f"git {' '.join(args[:2])} 執行失敗：{err}")
    return out


def repo_root(specs_dir: Path) -> Path | None:
    code, out, _ = run_git(specs_dir, "rev-parse", "--show-toplevel")
    return Path(out.strip()) if code == 0 else None


def repo_relative(specs_dir: Path, *parts: str) -> str:
    prefix = git(specs_dir, "rev-parse", "--show-prefix").strip().strip("/")
    return "/".join([part for part in (prefix, *parts) if part])


def load_plans(plans_dir: Path) -> list[dict]:
    plans = []
    if not plans_dir.is_dir():
        return plans
    for folder in sorted(plans_dir.iterdir()):
        match = PLAN_DIR_PATTERN.match(folder.name)
        if not folder.is_dir() or not match:
            continue
        plan = {"name": folder.name, "number": int(match.group(1)), "dir": folder, "data": None}
        plan_file = folder / PLAN_FILE
        if plan_file.is_file():
            try:
                data = json.loads(plan_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                data = None
            if isinstance(data, dict) and data.get("status") in (IN_PROGRESS, DELIVERED):
                plan["data"] = data
        plans.append(plan)
    return plans


def in_progress(plans: list[dict]) -> list[dict]:
    return [plan for plan in plans if plan["data"] and plan["data"]["status"] == IN_PROGRESS]


def load_ignore(truth_dir: Path) -> list[str]:
    ignore_file = truth_dir / ".truthignore"
    if not ignore_file.is_file():
        return []
    lines = ignore_file.read_text(encoding="utf-8").splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]


def is_ignored(path: str, patterns: list[str]) -> bool:
    parts = path.split("/")
    if any(part.startswith(".") for part in parts):
        return True
    return any(fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(parts[-1], pattern) for pattern in patterns)


def working_changes(root: Path, pathspec: str | None = None) -> list[dict]:
    """工作區相對於 HEAD 的變更（含尚未加入 git 的新檔），路徑相對於倉庫根目錄。"""
    args = ["status", "--porcelain", "--no-renames", "-z", "--untracked-files=all"]
    if pathspec:
        args += ["--", pathspec]
    changes = []
    for entry in git(root, *args).split("\0"):
        if len(entry) < 4:
            continue
        code, path = entry[:2], entry[3:]
        status = "ADD" if "?" in code or "A" in code else "DEL" if "D" in code else "MOD"
        changes.append({"status": status, "path": path})
    return changes


def single_in_progress(plans: list[dict]) -> dict:
    current = in_progress(plans)
    if not current:
        raise Refused([{"reason": "沒有進行中的 plan", "next": NEXT_OPEN}])
    if len(current) > 1:
        names = "、".join(plan["name"] for plan in current)
        raise Refused([{"reason": f"同時有多個進行中的 plan：{names}", "next": "一次只能有一個進行中的 plan；請先交付或放棄多出來的 plan"}])
    return current[0]


def previous_owners(plans: list[dict]) -> list[dict]:
    """沿用編號最大的既有 plan 在 truth-changes.md 中的各節標題。"""
    for plan in sorted(plans, key=lambda item: item["number"], reverse=True):
        record = plan["dir"] / "truth-changes.md"
        if not record.is_file():
            continue
        owners = []
        for line in record.read_text(encoding="utf-8").splitlines():
            match = OWNER_PATTERN.match(line)
            if match:
                owners.append({"owner": match.group(1).strip("` "), "paths": match.group(2)})
        if owners:
            return owners
    return []


def run_open(specs_dir: Path, name: str, kind: str) -> dict:
    if kind not in KINDS:
        raise Abort(f"--kind 只接受 {'、'.join(KINDS)}，收到 {kind}。用法：plan_state.py open specs --name ranking --kind 技術修正")
    if not NAME_PATTERN.match(name):
        raise Abort(f"--name 只接受小寫英數與連字號的英文短名，收到 {name}。用法：plan_state.py open specs --name ranking")
    plans_dir, truth_dir = specs_dir / "plans", specs_dir / "truth"
    root = repo_root(specs_dir)
    if root is None:
        raise Refused([{"reason": "這個專案不是 git 倉庫，無法記錄 truth 的基準", "next": "在專案根目錄執行 git init 並建立第一個 commit 後，再開立 plan"}])
    code, head, _ = run_git(root, "rev-parse", "--verify", "--quiet", "HEAD")
    if code != 0:
        raise Refused([{"reason": "倉庫還沒有任何 commit，無法記錄 truth 的基準", "next": "先把目前的專案內容建立第一個 commit，再開立 plan"}])
    plans = load_plans(plans_dir)
    refusals = []
    for plan in in_progress(plans):
        refusals.append({"reason": f"已有進行中的 plan {plan['name']}", "next": "先完成並交付它（plan-package deliver），或放棄它（plan-package abandon）"})
    for plan in plans:
        if plan["data"] is None:
            refusals.append({"reason": f"{plan['name']} 沒有 {PLAN_FILE}，或其中的狀態無法辨識", "next": f"確認它是已交付還是進行中的 plan；不是 plan 的資料夾請移出 {plans_dir.name}/"})
    truth_rel = repo_relative(specs_dir, "truth")
    patterns = load_ignore(truth_dir)
    all_changes = working_changes(root)
    dirty = [item for item in all_changes if item["path"].startswith(truth_rel + "/") and not is_ignored(item["path"][len(truth_rel) + 1:], patterns)]
    if dirty:
        refusals.append({
            "reason": f"truth 有 {len(dirty)} 個未 commit 的修改，不屬於任何 plan",
            "files": dirty,
            "next": "請使用者決定 commit 或還原這些修改後，再開立 plan",
        })
    if refusals:
        raise Refused(refusals)
    number = max((plan["number"] for plan in plans), default=0) + 1
    plan_name = f"{number:03d}-{name}"
    plan_dir = plans_dir / plan_name
    plan_dir.mkdir(parents=True)
    data = {
        "id": plan_name,
        "status": IN_PROGRESS,
        "kind": kind,
        "base": head.strip(),
        "opened": datetime.date.today().isoformat(),
    }
    (plan_dir / PLAN_FILE).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    warnings = []
    others = [item for item in all_changes if item not in dirty]
    if others:
        warnings.append(f"工作區另有 {len(others)} 個未 commit 的變更，交付這個 plan 時會一併 commit：" + "、".join(item["path"] for item in others))
    return {
        "ok": True, "plan": plan_name, "path": repo_relative(specs_dir, "plans", plan_name),
        "status": IN_PROGRESS, "kind": kind, "base": data["base"], "truth_owners": previous_owners(plans), "warnings": warnings,
    }


def run_check(specs_dir: Path, target: str | None, owner: str | None) -> dict:
    plans = load_plans(specs_dir / "plans")
    if target is None:
        plan = single_in_progress(plans)
    else:
        name = Path(target.replace("\\", "/").rstrip("/")).name
        matched = [item for item in plans if item["name"] == name]
        if not matched:
            raise Refused([{"reason": f"找不到 plan {name}", "next": NEXT_OPEN}])
        plan = matched[0]
        if plan["data"] is None:
            raise Refused([{"reason": f"{name} 沒有 {PLAN_FILE}，或其中的狀態無法辨識", "next": "plan 必須由 plan-package 的 open 開立"}])
        if plan["data"]["status"] == DELIVERED:
            raise Refused([{"reason": f"{name} 已交付，已交付的 plan 唯讀", "next": NEXT_OPEN}])
    data = plan["data"]
    plan_path = specs_dir / "plans" / plan["name"]
    result = {
        "ok": True, "plan": plan["name"], "path": plan_path.as_posix(),
        "status": data["status"], "kind": data.get("kind") or KINDS[0], "base": data.get("base", ""), "warnings": [],
    }
    try:
        status = plan_trace.run_status(str(plan_path), owner)
    except plan_trace.Abort as error:
        if owner and "不是相依表中的擁有者" in str(error):
            raise Abort(str(error))
        result["trace_error"] = str(error)
        result["warnings"].append(f"無法判定待補跑：{error}")
        return result
    result["pending"] = status["pending"]
    if owner:
        result["self"] = status["self"]
        result["upstream_pending"] = status["upstream_pending"]
        plan_trace.mark_started(str(plan_path), owner)
    if status["pending"]:
        result["warnings"].append("待補跑：" + "、".join(item["owner"] for item in status["pending"]))
        result["cross_check"] = None
    else:
        try:
            result["cross_check"] = cross_check.run(str(plan_path), "round")
        except plan_trace.Abort as error:
            result["cross_check"] = {"ok": False, "error": str(error)}
        if not result["cross_check"].get("ok"):
            result["warnings"].append("沒有待補跑，但交叉檢查未通過")
        if result["cross_check"].get("warnings"):
            result["warnings"].append(f"交叉檢查另有 {len(result['cross_check']['warnings'])} 個先前 plan 留下的問題（不擋交付，見 cross_check.warnings）")
    return result


def run_abandon(specs_dir: Path) -> dict:
    plan = single_in_progress(load_plans(specs_dir / "plans"))
    root = repo_root(specs_dir)
    if root is None:
        raise Abort("這個專案不是 git 倉庫，無法列出還原步驟。")
    base = plan["data"].get("base", "")
    truth_rel = repo_relative(specs_dir, "truth")
    plan_rel = repo_relative(specs_dir, "plans", plan["name"])
    specs_rel = repo_relative(specs_dir)
    changes = working_changes(root)
    outside = [item for item in changes if not item["path"].startswith(specs_rel + "/")]
    steps = [
        f"還原 truth 中被修改與刪除的檔案：git restore --source={base[:12]} --staged --worktree -- \"{truth_rel}\"",
        f"刪除 truth 中這次新增的檔案：先以 git clean -nd -- \"{truth_rel}\" 預覽，確認後執行 git clean -fd -- \"{truth_rel}\"",
        f"刪除 plan 資料夾：\"{plan_rel}\"",
    ]
    if outside:
        steps.append(f"還原這次修改的程式：{specs_rel}/ 以外有 {len(outside)} 個未 commit 的變更，逐一確認後以 git restore <路徑> 還原，新增的檔案自行刪除")
    commits = git(root, "rev-list", "--count", f"{base}..HEAD").strip() if base else "0"
    warnings = []
    if commits != "0":
        warnings.append(f"基準之後已有 {commits} 個 commit，上述步驟不會移除它們，請自行決定是否保留")
    return {
        "ok": True, "plan": plan["name"], "base": base, "steps": steps, "changed_outside_specs": outside, "warnings": warnings,
        "note": "以上步驟只供使用者自行執行，本指令沒有修改任何檔案",
    }


def run_files(specs_dir: Path) -> dict:
    plan = single_in_progress(load_plans(specs_dir / "plans"))
    root = repo_root(specs_dir)
    if root is None:
        raise Abort("這個專案不是 git 倉庫，無法列出將被 commit 的檔案。")
    files = working_changes(root)
    return {"ok": True, "plan": plan["name"], "count": len(files), "files": files}


def delivery_blockers(plan_path: Path) -> list[dict]:
    """交付前的防呆：仍有待補跑的擁有者，或交付階段的交叉檢查未通過時拒絕。"""
    refusals = []
    status = plan_trace.run_status(str(plan_path), None)
    if status["pending"]:
        names = "、".join(item["owner"] for item in status["pending"])
        refusals.append({"reason": f"仍有待補跑的擁有者：{names}", "next": "依 check 列出的順序補跑這些擁有者，結果是改了或不用改時記錄後再交付"})
    checked = cross_check.run(str(plan_path), "deliver")
    if not checked["ok"]:
        refusals.append({"reason": f"交付階段的交叉檢查有 {len(checked['problems'])} 個問題", "files": checked["problems"],
                         "next": "依每個問題寫明的交辦對象修正後再交付"})
    return refusals


def run_deliver(specs_dir: Path, message_file: Path) -> dict:
    plan = single_in_progress(load_plans(specs_dir / "plans"))
    root = repo_root(specs_dir)
    if root is None:
        raise Abort("這個專案不是 git 倉庫，無法交付。")
    try:
        blockers = delivery_blockers(specs_dir / "plans" / plan["name"])
    except plan_trace.Abort as error:
        raise Abort(f"無法確認交付條件：{error}")
    if blockers:
        raise Refused(blockers)
    if not message_file.is_file():
        raise Abort(f"找不到 commit 訊息檔 {message_file}。請先把訊息寫進檔案，再以 --message-file 傳入。")
    try:
        message_file.resolve().relative_to(root.resolve())
        raise Abort(f"commit 訊息檔 {message_file} 位於倉庫內，會被一併 commit。請放到倉庫以外的暫存目錄。")
    except ValueError:
        pass
    message = message_file.read_text(encoding="utf-8-sig").strip() + "\n"
    subject = message.splitlines()[0]
    if not re.match(rf"^deliver\({re.escape(plan['name'])}\): \S", subject):
        raise Abort(f"commit 訊息的第一行必須是「deliver({plan['name']}): 標題」，目前是「{subject}」。")
    plan_file = plan["dir"] / PLAN_FILE
    original = plan_file.read_text(encoding="utf-8")
    data = dict(plan["data"], status=DELIVERED, delivered=datetime.date.today().isoformat())
    plan_file.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    code, _, err = run_git(root, "add", "-A")
    if code == 0:
        code, _, err = run_git(root, "commit", "-F", "-", stdin=message.encode("utf-8"))
    if code != 0:
        plan_file.write_text(original, encoding="utf-8", newline="\n")
        run_git(root, "reset", "-q")
        raise Refused([{"reason": f"git commit 失敗：{err}", "next": f"plan 維持{IN_PROGRESS}，沒有建立 commit；排除原因後重新交付，不要略過 commit hook"}])
    commit = git(root, "rev-parse", "HEAD").strip()
    return {
        "ok": True, "plan": plan["name"], "status": DELIVERED, "commit": commit, "subject": subject,
        "clean": not working_changes(root), "pushed": False,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="管理 plan package 的狀態：開立、檢查、放棄、列出交付檔案與交付。")
    commands = parser.add_subparsers(dest="command", required=True)
    specs_help = "specs 資料夾（其下有 plans/ 與 truth/），例如 specs"
    open_parser = commands.add_parser("open", help="開立新的 plan 資料夾與 .plan.json；條件不符時拒絕且不建立任何檔案")
    open_parser.add_argument("specs_dir", help=specs_help)
    open_parser.add_argument("--name", required=True, help="英文短名（小寫英數與連字號），例如 ranking")
    open_parser.add_argument("--kind", default="需求", help="plan 的種類：需求（預設，由 specify 開立）或 技術修正（沒有需求、只為技術修正 truth 或程式）")
    check = commands.add_parser("check", help="確認目標是進行中的 plan，輸出路徑、基準、種類、待補跑，沒有待補跑時一併執行交叉檢查")
    check.add_argument("specs_dir", help=specs_help)
    check.add_argument("--plan", help="目標 plan 的資料夾名稱或路徑，例如 004-ranking；省略時採用唯一進行中的 plan")
    check.add_argument("--owner", help="呼叫者的 skill 名稱（相依表中的擁有者，例如 api-plan）；有帶時另輸出它自己的輸入差異與上游的待補跑，不是擁有者的 skill 不帶")
    abandon = commands.add_parser("abandon", help="輸出放棄進行中 plan 的還原步驟，不修改任何檔案")
    abandon.add_argument("specs_dir", help=specs_help)
    files = commands.add_parser("files", help="列出交付時會被 commit 的檔案")
    files.add_argument("specs_dir", help=specs_help)
    deliver = commands.add_parser("deliver", help="把進行中的 plan 標為已交付並建立單一 commit，不推送")
    deliver.add_argument("specs_dir", help=specs_help)
    deliver.add_argument("--message-file", required=True, help="commit 訊息檔的路徑，必須放在倉庫以外；第一行為 deliver(NNN-短名): 標題")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    specs_dir = Path(args.specs_dir)
    if not specs_dir.is_dir():
        print(f"錯誤：找不到 specs 資料夾 {specs_dir}。請傳入其下有 plans/ 與 truth/ 的資料夾，例如 specs", file=sys.stderr)
        return 2
    try:
        if args.command == "open":
            result = run_open(specs_dir, args.name, args.kind)
        elif args.command == "check":
            result = run_check(specs_dir, args.plan, args.owner)
        elif args.command == "abandon":
            result = run_abandon(specs_dir)
        elif args.command == "files":
            result = run_files(specs_dir)
        else:
            result = run_deliver(specs_dir, Path(args.message_file))
    except Refused as refused:
        print(json.dumps({"ok": False, "refusals": refused.refusals}, ensure_ascii=False, indent=2))
        for item in refused.refusals:
            print(f"拒絕：{item['reason']}。下一步：{item['next']}", file=sys.stderr)
        return 1
    except Abort as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    for warning in result.get("warnings", []):
        print(f"提醒：{warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
