# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""依 SKILL.md 的 SOP 逐 Step 把關執行並記錄：init 建立執行紀錄；next 只給出下一個待執行 Step 並印出它掛載的 skill 內部 Markdown 部件全文；
done 只接受目前的 Step，ASK 必須附上提問與使用者回覆原文，掛載樣板骨架的 WRITE 必須附上含骨架全部 H2 的產出檔；--mode 把另一模式專屬的 Phase 標為不適用；
skip 必須附上跳過理由、提問與使用者同意的回覆原文；back 把指定 Step 及其後的 Step 退回待執行；report 輸出每個 Step 的執行狀態表，仍有待執行 Step 時以非零結束。"""

import argparse
import json
import re
import sys
from pathlib import Path

PHASE_PATTERN = re.compile(r"^###\s+Phase\s+(\d+)\s+---\s+(.+?)\s*$")
STEP_PATTERN = re.compile(r"^(\d+)\.\s+([A-Z]+)\s+(.*)$")
LINK_PATTERN = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
MODE_ONLY = {"新建": "僅優化", "優化": "僅新建"}
PENDING, DONE, SKIPPED, NA = "待執行", "已執行", "跳過（經同意）", "不適用"
COMMANDS = ("init", "next", "done", "skip", "back", "report")


class GateError(Exception):
    pass


def parse_sop(skill_dir: Path) -> list[dict]:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise GateError(f"找不到 {skill_md}。--skill 必須是含 SKILL.md 的 skill 目錄，例如 .claude/skills/skill-engineering")
    steps, phase, title = [], None, ""
    for line in skill_md.read_text(encoding="utf-8").splitlines():
        if match := PHASE_PATTERN.match(line):
            phase, title = int(match.group(1)), match.group(2)
            continue
        if phase and (match := STEP_PATTERN.match(line)):
            mounts = [href for href in LINK_PATTERN.findall(line) if "://" not in href]
            steps.append({"id": f"{phase}.{match.group(1)}", "phase_title": title, "verb": match.group(2),
                          "text": match.group(3), "mounts": mounts, "status": PENDING, "record": {}})
    if not steps:
        raise GateError(f"{skill_md} 沒有可解析的 SOP Step。Phase 標題須為「### Phase N --- 名稱」，Step 須為「N. 動詞 行為」")
    return steps


def load(log: Path) -> dict:
    if not log.is_file():
        raise GateError(f"找不到執行紀錄 {log}。請先執行 init --skill <skill 目錄> --log {log}")
    return json.loads(log.read_text(encoding="utf-8"))


def save(log: Path, state: dict) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def current(state: dict) -> dict | None:
    return next((step for step in state["steps"] if step["status"] == PENDING), None)


def require_current(state: dict, step_id: str) -> dict:
    step = current(state)
    if step is None:
        raise GateError("所有 Step 都已處理完畢，請執行 report 輸出狀態表")
    if step["id"] != step_id:
        raise GateError(f"目前應處理 Step {step['id']}（{step['verb']} {step['text']}），不得記錄 {step_id}。"
                        f"請先執行 next 取得 Step {step['id']} 並完成它")
    return step


def require_reply(question: str | None, reply: str | None) -> None:
    if not question or not reply:
        raise GateError("必須以 --question 附上這次向使用者提出的問題，並以 --reply 附上使用者針對該問題的回覆原文")


def skeleton_headings(skill_dir: Path, mounts: list[str]) -> list[str]:
    headings = []
    for href in mounts:
        if href.startswith("templates/") and href.endswith(".md") and not href.endswith(".example.md"):
            text = (skill_dir / href).read_text(encoding="utf-8")
            headings += [line.strip() for line in text.splitlines() if line.startswith("## ")]
    return headings


def cmd_init(args: argparse.Namespace) -> None:
    skill_dir = Path(args.skill).resolve()
    steps = parse_sop(skill_dir)
    save(Path(args.log), {"skill": str(skill_dir), "mode": None, "steps": steps})
    print(f"已建立執行紀錄 {args.log}，共 {len(steps)} 個 Step；請執行 next 取得第一個 Step", file=sys.stderr)


def cmd_next(args: argparse.Namespace) -> None:
    state = load(Path(args.log))
    step = current(state)
    if step is None:
        print("所有 Step 都已處理完畢，請執行 report 輸出狀態表", file=sys.stderr)
        return
    skill_dir = Path(state["skill"])
    print(f"## 下一個 Step：{step['id']}（Phase：{step['phase_title']}）\n{step['verb']} {step['text']}\n")
    for href in step["mounts"]:
        target = (skill_dir / href).resolve()
        if target.name == "SKILL.md":
            print(f"---------- 掛載 skill：{target.parent.name}（必須以 Skill 工具載入並依其 SOP 執行）")
        elif target.is_relative_to(skill_dir) and target.suffix == ".md" and target.is_file():
            print(f"---------- 掛載部件全文：{href}\n{target.read_text(encoding='utf-8')}")
        else:
            print(f"---------- 掛載檔案：{href}")


def cmd_done(args: argparse.Namespace) -> None:
    log = Path(args.log)
    state = load(log)
    step = require_current(state, args.step)
    if not args.evidence:
        raise GateError("必須以 --evidence 寫出本 Step 的產出位置或結論")
    if step["verb"] == "ASK":
        require_reply(args.question, args.reply)
    headings = skeleton_headings(Path(state["skill"]), step["mounts"])
    if step["verb"] == "WRITE" and headings:
        if not args.file or not Path(args.file).is_file():
            raise GateError("本 Step 掛載樣板，必須以 --file 指向依樣板產出的檔案")
        content = Path(args.file).read_text(encoding="utf-8")
        missing = [heading for heading in headings if heading not in content]
        if missing:
            raise GateError(f"產出檔 {args.file} 缺少樣板章節 {missing}，請依樣板補齊後重新記錄")
    if args.mode:
        state["mode"] = args.mode
        for other in state["steps"]:
            if MODE_ONLY[args.mode] in other["phase_title"]:
                other["status"], other["record"] = NA, {"evidence": f"模式為{args.mode}"}
    step["status"] = DONE
    step["record"] = {key: value for key, value in {"evidence": args.evidence, "file": args.file,
                                                    "question": args.question, "reply": args.reply}.items() if value}
    save(log, state)
    print(f"已記錄 Step {step['id']}；請執行 next 取得下一個 Step", file=sys.stderr)


def cmd_skip(args: argparse.Namespace) -> None:
    log = Path(args.log)
    state = load(log)
    step = require_current(state, args.step)
    if not args.reason:
        raise GateError("必須以 --reason 寫出跳過理由")
    require_reply(args.question, args.reply)
    step["status"] = SKIPPED
    step["record"] = {"evidence": args.reason, "question": args.question, "reply": args.reply}
    save(log, state)
    print(f"已記錄跳過 Step {step['id']}；請執行 next 取得下一個 Step", file=sys.stderr)


def cmd_back(args: argparse.Namespace) -> None:
    log = Path(args.log)
    state = load(log)
    ids = [step["id"] for step in state["steps"]]
    if args.step not in ids:
        raise GateError(f"找不到 Step {args.step}。可用的 Step：{'、'.join(ids)}")
    for step in state["steps"][ids.index(args.step):]:
        if step["status"] != NA:
            step["status"], step["record"] = PENDING, {}
    save(log, state)
    print(f"已退回 Step {args.step}，其後的 Step 改為待執行；請執行 next", file=sys.stderr)


def cell(text: str) -> str:
    return text.replace("|", "／").replace("\n", " ")


def cmd_report(args: argparse.Namespace) -> int:
    state = load(Path(args.log))
    print("| Step | 動作 | 狀態 | 證據 | 提問 | 使用者回覆 |\n|---|---|---|---|---|---|")
    for step in state["steps"]:
        record = step["record"]
        print(f"| {step['id']} | {cell(step['verb'] + ' ' + step['text'])} | {step['status']} | "
              f"{cell(record.get('evidence', ''))} | {cell(record.get('question', ''))} | {cell(record.get('reply', ''))} |")
    pending = [step["id"] for step in state["steps"] if step["status"] == PENDING]
    if pending:
        print(f"錯誤：仍有待執行的 Step：{'、'.join(pending)}。請補做，或經使用者同意後以 skip 記錄", file=sys.stderr)
        return 1
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="依 SKILL.md 的 SOP 逐 Step 把關執行並記錄。")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        command = sub.add_parser(name)
        command.add_argument("--log", required=True, help="執行紀錄 JSON 檔路徑")
        if name == "init":
            command.add_argument("--skill", required=True, help="要依其 SOP 執行的 skill 目錄（含 SKILL.md）")
        if name in ("done", "skip", "back"):
            command.add_argument("step", help="Step 編號，格式為 Phase.Step，例如 2.3")
        if name in ("done", "skip"):
            command.add_argument("--question", help="ASK 或跳過時向使用者提出的問題")
            command.add_argument("--reply", help="使用者針對該問題的回覆原文")
        if name == "done":
            command.add_argument("--evidence", help="本 Step 的產出位置或結論")
            command.add_argument("--file", help="掛載樣板的 WRITE Step 依樣板產出的檔案")
            command.add_argument("--mode", choices=list(MODE_ONLY), help="判定模式後設定，另一模式專屬的 Phase 標為不適用")
        if name == "skip":
            command.add_argument("--reason", help="跳過理由")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    try:
        result = globals()[f"cmd_{args.command}"](args)
    except GateError as error:
        print(f"拒絕：{error}", file=sys.stderr)
        return 1
    return result or 0


if __name__ == "__main__":
    sys.exit(main())
