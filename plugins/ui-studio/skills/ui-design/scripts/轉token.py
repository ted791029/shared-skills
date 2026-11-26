# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""把 DESIGN.md 的色彩、字體、間距與版面、圓角、陰影、動態表格轉成 tokens.css（CSS 變數）與 tokens.json（W3C DTCG）。
值為 var(--x) 時在 DTCG 轉為別名 {x}；色彩的暗色值輸出到 prefers-color-scheme: dark。stdout 輸出摘要 JSON。
結束碼：0 成功；1 參數或檔案錯誤；2 DESIGN.md 是舊格式或有無法解析的列（stderr 列出行號與修正方式）。"""

import argparse
import json
import re
import sys
from pathlib import Path

SECTIONS = {
    "色彩": "color",
    "字體": "typography",
    "間距與版面": "dimension",
    "圓角": "dimension",
    "陰影": "shadow",
    "動態": "motion",
}
HEADERS = {
    "color": ["token", "值", "暗色值", "用途"],
    "typography": ["token", "角色", "字型", "字級", "字重", "行高", "用途"],
    "dimension": ["token", "值", "用途"],
    "shadow": ["token", "值", "用途"],
    "motion": ["token", "值", "用途"],
}
OLD_SECTIONS = {"形狀與層次"}
TOKEN = re.compile(r"^`?(--[a-z0-9-]+)`?$")
VAR = re.compile(r"^var\((--[a-z0-9-]+)\)$")
CUBIC = re.compile(r"^cubic-bezier\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)$")
DURATION = re.compile(r"^([\d.]+)(ms|s)$")
EMPTY = {"", "—", "-", "–"}
TEXT_FIELDS = {"用途", "角色"}


class FormatError(Exception):
    pass


def cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def clean(value: str) -> str:
    return value.strip().strip("`").strip()


def parse(text: str) -> tuple[list[dict], list[str]]:
    rows, problems = [], []
    section, kind, header_seen = None, None, False
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            section = line[3:].strip()
            kind = SECTIONS.get(section)
            header_seen = False
            if section in OLD_SECTIONS:
                problems.append(f"第 {number} 行：「## {section}」是舊格式，請拆成「## 圓角」與「## 陰影」兩個表格（token、值、用途）")
            continue
        if kind is None or not line.lstrip().startswith("|"):
            continue
        parts = cells(line)
        if not header_seen:
            header_seen = True
            if [part.lower() for part in parts] != [h.lower() for h in HEADERS[kind]]:
                problems.append(f"第 {number} 行：「## {section}」的表頭應為 | {' | '.join(HEADERS[kind])} |，目前是 | {' | '.join(parts)} |")
                kind = None
            continue
        if set("".join(parts)) <= set("-: "):
            continue
        match = TOKEN.match(parts[0])
        if not match or len(parts) != len(HEADERS[kind]):
            problems.append(f"第 {number} 行：「## {section}」的列必須有 {len(HEADERS[kind])} 欄，第一欄是以反引號包住的 token（例如 `--color-ink`）")
            continue
        fields = dict(zip(HEADERS[kind], parts))
        rows.append({"kind": kind, "section": section, "line": number, "token": match.group(1),
                     "fields": {key: value if key in TEXT_FIELDS else clean(value) for key, value in fields.items()}})
    for name, kind in SECTIONS.items():
        if kind == "motion" and f"## {name}" in text and not any(row["kind"] == "motion" for row in rows):
            problems.append(f"「## {name}」沒有 token 表：請改為 | token | 值 | 用途 | 表格（例如 `--duration-feedback` 150ms、`--ease-out` cubic-bezier(0.16, 1, 0.3, 1)），原有的說明文字可留在表格下方")
    return rows, problems


def dtcg_value(raw: str, kind: str, token: str) -> dict:
    alias = VAR.match(raw)
    if alias:
        return {"$value": "{" + alias.group(1)[2:] + "}"}
    if kind == "color":
        return {"$type": "color", "$value": raw}
    if kind == "dimension":
        return {"$type": "dimension", "$value": raw}
    if kind == "motion":
        cubic = CUBIC.match(raw)
        if cubic:
            return {"$type": "cubicBezier", "$value": [float(item) for item in cubic.groups()]}
        duration = DURATION.match(raw)
        if duration:
            amount = float(duration.group(1)) * (1000 if duration.group(2) == "s" else 1)
            return {"$type": "duration", "$value": f"{amount:g}ms"}
        return {"$value": raw}
    return {"$value": raw}


def convert(rows: list[dict]) -> tuple[str, dict]:
    light, dark, tokens = [], [], {}
    for row in rows:
        name, fields, kind = row["token"], row["fields"], row["kind"]
        key = name[2:]
        usage = fields.get("用途", "")
        if kind == "typography":
            parts = {"font-family": fields["字型"], "font-size": fields["字級"], "font-weight": fields["字重"], "line-height": fields["行高"]}
            for suffix, value in parts.items():
                light.append(f"  {name}-{suffix}: {value};")
            tokens[key] = {"$type": "typography", "$description": f"{fields['角色']}：{usage}",
                           "$value": {"fontFamily": fields["字型"], "fontSize": fields["字級"],
                                      "fontWeight": int(fields["字重"]) if fields["字重"].isdigit() else fields["字重"],
                                      "lineHeight": float(fields["行高"]) if re.fullmatch(r"[\d.]+", fields["行高"]) else fields["行高"]}}
            continue
        value = fields["值"]
        light.append(f"  {name}: {value};")
        entry = {**dtcg_value(value, kind, name), "$description": usage}
        night = fields.get("暗色值", "")
        if kind == "color" and night not in EMPTY:
            dark.append(f"  {name}: {night};")
            entry["$extensions"] = {"ui-design.dark": dtcg_value(night, kind, name)["$value"]}
        tokens[key] = entry
    css = ["/* 由 ui-design 的 轉token.py 依 DESIGN.md 產生，請改 DESIGN.md 後重新轉出，不要直接編輯 */", ":root {", *light, "}"]
    if dark:
        css += ["", "@media (prefers-color-scheme: dark) {", "  :root {", *["  " + item for item in dark], "  }", "}"]
    return "\n".join(css) + "\n", tokens


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="把 DESIGN.md 的 token 表轉成 tokens.css 與 tokens.json（DTCG）。")
    parser.add_argument("design", help="DESIGN.md 的路徑")
    parser.add_argument("--out-dir", help="輸出資料夾；預設為 DESIGN.md 所在的資料夾")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    design = Path(args.design).expanduser().resolve()
    if not design.is_file():
        print(f"錯誤：找不到 {design}。請傳入 DESIGN.md 的路徑。", file=sys.stderr)
        return 1
    rows, problems = parse(design.read_text(encoding="utf-8"))
    if problems:
        print(f"錯誤：{design.name} 無法轉出 token。這些是格式問題，只需調整表格格式、不需改值：", file=sys.stderr)
        for item in problems:
            print(f"- {item}", file=sys.stderr)
        return 2
    if not rows:
        print(f"錯誤：{design.name} 沒有任何 token 表。請依 ui-design 的 DESIGN.md 樣板撰寫色彩、字體等表格。", file=sys.stderr)
        return 2
    out = Path(args.out_dir).expanduser().resolve() if args.out_dir else design.parent
    out.mkdir(parents=True, exist_ok=True)
    css, tokens = convert(rows)
    (out / "tokens.css").write_text(css, encoding="utf-8", newline="\n")
    (out / "tokens.json").write_text(json.dumps(tokens, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    counts = {}
    for row in rows:
        counts[row["section"]] = counts.get(row["section"], 0) + 1
    print(json.dumps({"css": str(out / "tokens.css"), "json": str(out / "tokens.json"), "tokens": len(rows), "by_section": counts}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
