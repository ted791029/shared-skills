# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""把方向候選.json 某一輪的卡片與每張卡片的示範畫面填進 templates/方向選擇頁.html，產出可直接用瀏覽器開啟的靜態選擇頁。
示範畫面取自示範資料夾的 <卡片 id>.html（標準做法為 standard.html），以 iframe srcdoc 嵌入，任何一張缺少就不產頁。
所有文字都做 HTML 跳脫；頁面不連任何伺服器，按鈕只把回覆文字複製到剪貼簿。"""

import argparse
import html
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

TEMPLATE = Path(__file__).resolve().parent.parent / "templates" / "方向選擇頁.html"
CARD_START = "<!-- 重複開始：每張卡片一組 -->"
SWATCH_START = "<!-- 重複開始：每個色票一個 -->"
REPEAT_END = "<!-- 重複結束 -->"
HEX = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
STANDARD_ID = "standard"
REQUIRED_TEXT = ("name", "metaphor", "first_view", "why", "risk")
DEMO_DIR_NAME = "方向示範"


class InputError(Exception):
    pass


def split_blocks(template: str) -> tuple[str, str, str, str, str]:
    """回傳（卡片前、卡片前段、色票、卡片後段、卡片後）。"""
    card_at = template.find(CARD_START)
    swatch_at = template.find(SWATCH_START, card_at)
    swatch_end = template.find(REPEAT_END, swatch_at)
    card_end = template.find(REPEAT_END, swatch_end + len(REPEAT_END))
    if min(card_at, swatch_at, swatch_end, card_end) < 0:
        raise InputError(f"{TEMPLATE} 缺少卡片或色票的重複標記，請依 skill 隨附的原版樣板還原。")
    return (template[:card_at],
            template[card_at + len(CARD_START):swatch_at],
            template[swatch_at + len(SWATCH_START):swatch_end],
            template[swatch_end + len(REPEAT_END):card_end],
            template[card_end + len(REPEAT_END):])


def fill(fragment: str, values: dict) -> str:
    for key, value in values.items():
        fragment = fragment.replace("{{" + key + "}}", value)
    return fragment


def screen_values(data: dict) -> dict:
    screen = data.get("screen")
    if not isinstance(screen, dict):
        raise InputError("方向候選.json 缺少 screen（每張卡片共用的代表畫面），請依視覺方向規範補上 name、content、width、height。")
    missing = [key for key in ("name", "content") if not str(screen.get(key, "")).strip()]
    sizes = [key for key in ("width", "height") if not isinstance(screen.get(key), int) or screen[key] <= 0]
    if missing or sizes:
        raise InputError(f"screen 的 {'、'.join(missing + sizes)} 不完整：name、content 必須是白話文字，width、height 必須是正整數（示範畫面的設計寬高，單位 px）。")
    return {"screen_name": html.escape(screen["name"]), "screen_content": html.escape(screen["content"]),
            "screen_width": str(screen["width"]), "screen_height": str(screen["height"])}


def card_values(card: dict, detail: dict) -> tuple[dict, list[str]]:
    missing = [field for field in REQUIRED_TEXT if not str(detail.get(field, "")).strip()]
    if missing:
        raise InputError(f"卡片「{detail.get('id', card['id'])}」缺少 {'、'.join(missing)}，請在方向候選.json 補上白話內容。")
    swatches = detail.get("swatches") or []
    bad = [s for s in swatches if not isinstance(s, str) or not HEX.match(s)]
    if len(swatches) < 2 or bad:
        raise InputError(f"卡片「{detail.get('name')}」的 swatches 必須是至少 2 個 #RRGGBB 色碼（依序為底色、主色、強調色），收到 {swatches}。")
    values = {
        "card_number": str(card["no"]), "card_kind": html.escape(card["kind"]),
        "card_name": html.escape(detail["name"]), "card_metaphor": html.escape(detail["metaphor"]),
        "card_first_view": html.escape(detail["first_view"]), "card_why": html.escape(detail["why"]),
        "card_risk": html.escape(detail["risk"]),
    }
    return values, swatches


def demo_values(path: Path, out_dir: Path) -> dict | None:
    content = path.read_text(encoding="utf-8") if path.is_file() else ""
    if not content.strip():
        return None
    href = Path(os.path.relpath(path.resolve(), out_dir.resolve())).as_posix()
    return {"demo_srcdoc": html.escape(content, quote=True), "demo_href": html.escape(quote(href), quote=True)}


def render(data: dict, round_no: int | None, demos: Path, out_dir: Path) -> tuple[str, dict, list[str]]:
    rounds = data.get("rounds") or []
    if not rounds:
        raise InputError("方向候選.json 還沒有擲骰紀錄，請先執行 方向擲骰.py roll。")
    target = rounds[-1] if round_no is None else next((r for r in rounds if r.get("round") == round_no), None)
    if target is None:
        raise InputError(f"找不到第 {round_no} 輪，現有輪次：{', '.join(str(r.get('round')) for r in rounds)}。")
    page_values = {"product_name": html.escape(str(data.get("product", "這個產品"))),
                   "round_number": str(target["round"]), "round_mode": html.escape(target.get("mode", "一般")),
                   **screen_values(data)}
    by_id = {c["id"]: c for c in data.get("candidates", [])}
    before, card_head, swatch, card_tail, after = split_blocks(TEMPLATE.read_text(encoding="utf-8"))
    cards, missing_demos, used = [], [], []
    for card in target["cards"]:
        detail = data.get("standard") if card["id"] == STANDARD_ID else by_id.get(card["id"])
        if not detail:
            raise InputError(f"第 {target['round']} 輪的卡片 {card['no']} 指向不存在的候選「{card['id']}」，請勿手動修改 rounds。")
        values, swatches = card_values(card, detail)
        demo_path = demos / f"{card['id']}.html"
        demo = demo_values(demo_path, out_dir)
        if demo is None:
            missing_demos.append(f"第 {card['no']} 張「{detail['name']}」→ {demo_path}")
            continue
        used.append(str(demo_path.resolve()))
        values.update(demo)
        values.update(page_values)
        swatch_html = "".join(fill(swatch, {"swatch_color": s}) for s in swatches)
        cards.append(fill(card_head, values) + swatch_html + fill(card_tail, values))
    if missing_demos:
        raise InputError("以下卡片還沒有示範畫面，請依視覺方向規範為每張卡片畫出套上該方向的代表畫面後重試：\n  "
                         + "\n  ".join(missing_demos))
    page = fill(before, page_values) + "".join(cards) + fill(after, page_values)
    leftover = sorted(set(re.findall(r"\{\{(\w+)\}\}", page)))
    if leftover:
        raise InputError(f"樣板仍有未填入的欄位 {leftover}，請確認樣板與本腳本的欄位名稱一致。")
    return page, target, used


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="依方向候選.json 與每張卡片的示範畫面產出方向選擇頁（靜態 HTML）。")
    parser.add_argument("--candidates", required=True, help="方向候選.json 的路徑")
    parser.add_argument("--out", required=True, help="輸出的方向選擇頁.html 路徑")
    parser.add_argument("--demos", help=f"示範畫面資料夾，內含 <卡片 id>.html；省略時為方向候選.json 同層的 {DEMO_DIR_NAME}/")
    parser.add_argument("--round", type=int, help="要呈現的輪次；省略時為最新一輪")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    source = Path(args.candidates)
    out = Path(args.out)
    demos = Path(args.demos) if args.demos else source.parent / DEMO_DIR_NAME
    try:
        if not source.is_file():
            raise InputError(f"找不到 {source}，請確認 --candidates 的路徑。")
        try:
            data = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise InputError(f"{source} 不是合法的 JSON（第 {error.lineno} 行：{error.msg}）。")
        page, target, used = render(data, args.round, demos, out.parent)
    except InputError as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8", newline="\n")
    print(json.dumps({"out": str(out.resolve()), "round": target["round"],
                      "cards": target["cards"], "demos": used}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
