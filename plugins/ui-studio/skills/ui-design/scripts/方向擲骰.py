# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""依方向候選.json 擲出視覺方向與挑戰者（roll），或記錄使用者在選擇頁選定的卡片（choose）。
擲骰結果與選定都寫回同一份 JSON；同一份候選與同一個種子必定得到相同結果。"""

import argparse
import json
import random
import secrets
import sys
from pathlib import Path

FAMILIARITY = ("熟悉", "中間", "大膽")
MODES = ("一般", "保守", "大膽")
MODE_FILTER = {"一般": None, "保守": "熟悉", "大膽": "大膽"}
MAX_CHALLENGERS = 3
KIND_ASSIGNED, KIND_PICK, KIND_CHALLENGER, KIND_STANDARD = "擲中", "推薦", "挑戰者", "標準做法"
STANDARD_ID = "standard"
EXIT_EXHAUSTED = 3


class InputError(Exception):
    pass


def load(path: Path) -> dict:
    if not path.is_file():
        raise InputError(f"找不到 {path}。請先依視覺方向規範把候選寫進這個檔案，或確認 --candidates 的路徑。")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise InputError(f"{path} 不是合法的 JSON（第 {error.lineno} 行第 {error.colno} 欄：{error.msg}），請修正後重試。")
    candidates = data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise InputError(f"{path} 的 candidates 必須是非空陣列，請依 templates/方向候選.json 補上候選。")
    if not isinstance(data.get("standard"), dict):
        raise InputError(f"{path} 缺少 standard（這類產品的標準做法），請依 templates/方向候選.json 補上。")
    seen = set()
    for index, candidate in enumerate(candidates, start=1):
        cid = candidate.get("id")
        if not cid or cid == STANDARD_ID:
            raise InputError(f"第 {index} 個候選的 id 必須是非空字串且不得為 {STANDARD_ID}。")
        if cid in seen:
            raise InputError(f"候選 id「{cid}」重複；追加候選時 id 必須接續編號，不得沿用既有 id。")
        seen.add(cid)
        if candidate.get("familiarity") not in FAMILIARITY:
            raise InputError(f"候選「{cid}」的 familiarity 必須是 {'、'.join(FAMILIARITY)} 其中之一，收到 {candidate.get('familiarity')!r}。")
        if not isinstance(candidate.get("batch"), int):
            raise InputError(f"候選「{cid}」缺少整數 batch（第幾批推導的候選，第一批為 1）。")
    picks = [c["id"] for c in candidates if c.get("pick") is True]
    if len(picks) > 1:
        raise InputError(f"最多只能有一個候選標為 pick，目前有 {len(picks)} 個：{'、'.join(picks)}。")
    data.setdefault("shown", [])
    data.setdefault("rounds", [])
    return data


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def roll(data: dict, mode: str, steer: str, seed: int, latest_batch: bool) -> dict:
    shown = set(data["shown"])
    pool = [c for c in data["candidates"] if c["id"] not in shown]
    if latest_batch:
        newest = max(c["batch"] for c in data["candidates"])
        pool = [c for c in pool if c["batch"] == newest]
    wanted = MODE_FILTER[mode]
    if wanted:
        filtered = [c for c in pool if c["familiarity"] == wanted] or [c for c in pool if c["familiarity"] == "中間"]
    else:
        filtered = pool
    if not filtered:
        raise LookupError(mode)

    rng = random.Random(seed)
    assigned = rng.choice(filtered)
    pick = next((c for c in data["candidates"] if c.get("pick") is True and c["id"] not in shown and c["id"] != assigned["id"]), None)
    rest = [c for c in filtered if c["id"] not in {assigned["id"], pick["id"] if pick else None}]
    challengers = rng.sample(rest, min(MAX_CHALLENGERS, len(rest)))

    kinds = [(KIND_ASSIGNED, assigned["id"])]
    if pick:
        kinds.append((KIND_PICK, pick["id"]))
    kinds += [(KIND_CHALLENGER, c["id"]) for c in challengers]
    kinds.append((KIND_STANDARD, STANDARD_ID))
    cards = [{"no": no, "kind": kind, "id": cid} for no, (kind, cid) in enumerate(kinds, start=1)]

    record = {"round": len(data["rounds"]) + 1, "mode": mode, "steer": steer, "seed": seed,
              "latest_batch": latest_batch, "cards": cards, "chosen": None}
    data["rounds"].append(record)
    data["shown"] += [card["id"] for card in cards if card["id"] != STANDARD_ID]
    return record


def choose(data: dict, card_no: int, round_no: int | None, note: str) -> dict:
    if not data["rounds"]:
        raise InputError("還沒有任何擲骰紀錄，請先執行 roll。")
    target = data["rounds"][-1] if round_no is None else next((r for r in data["rounds"] if r["round"] == round_no), None)
    if target is None:
        raise InputError(f"找不到第 {round_no} 輪，現有輪次：{', '.join(str(r['round']) for r in data['rounds'])}。")
    card = next((c for c in target["cards"] if c["no"] == card_no), None)
    if card is None:
        raise InputError(f"第 {target['round']} 輪沒有第 {card_no} 張卡片，可選 1～{len(target['cards'])}。")
    for other in data["rounds"]:
        other["chosen"] = None
    target["chosen"] = {"no": card["no"], "kind": card["kind"], "id": card["id"], "note": note}
    detail = data["standard"] if card["id"] == STANDARD_ID else next(c for c in data["candidates"] if c["id"] == card["id"])
    return {"round": target["round"], **target["chosen"], "candidate": detail}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="擲出視覺方向與挑戰者，或記錄使用者選定的卡片；結果寫回方向候選.json。")
    sub = parser.add_subparsers(dest="command", required=True)
    roll_parser = sub.add_parser("roll", help="擲出這一輪的方向與挑戰者")
    roll_parser.add_argument("--candidates", required=True, help="方向候選.json 的路徑")
    roll_parser.add_argument("--mode", default="一般", choices=MODES, help="一般：不限熟悉度；保守：只抽熟悉；大膽：只抽大膽（沒有時改抽中間）")
    roll_parser.add_argument("--steer", default="", help="使用者在選擇頁寫的調整，只記錄不影響抽籤；改變外觀時應先追加一批候選並加上 --latest-batch")
    roll_parser.add_argument("--latest-batch", action="store_true", help="只從最新一批候選抽，用於依調整追加候選之後")
    roll_parser.add_argument("--seed", type=int, help="亂數種子；省略時隨機產生並寫入紀錄")
    choose_parser = sub.add_parser("choose", help="記錄使用者選定的卡片")
    choose_parser.add_argument("--candidates", required=True, help="方向候選.json 的路徑")
    choose_parser.add_argument("--card", type=int, required=True, help="使用者回覆的卡片編號，例如「選 2」填 2")
    choose_parser.add_argument("--round", type=int, help="卡片所在的輪次；省略時為最新一輪")
    choose_parser.add_argument("--note", default="", help="使用者選定時附帶的小調整，例如「字再圓一點」")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    path = Path(args.candidates)
    try:
        data = load(path)
        if args.command == "roll":
            seed = args.seed if args.seed is not None else secrets.randbits(32)
            try:
                result = roll(data, args.mode, args.steer, seed, args.latest_batch)
            except LookupError:
                scope = "最新一批" if args.latest_batch else "全部"
                print(f"候選已用完：{scope}候選中沒有尚未展示、符合「{args.mode}」模式的候選。"
                      "請依視覺方向規範排除已展示的候選，追加一批新的候選（id 接續編號、batch 加 1），再加上 --latest-batch 重擲。",
                      file=sys.stderr)
                return EXIT_EXHAUSTED
        else:
            result = choose(data, args.card, args.round, args.note)
    except InputError as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1
    save(path, data)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
