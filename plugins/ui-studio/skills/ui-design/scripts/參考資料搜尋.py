# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""以英文關鍵字搜尋字體搭配（typography）或視覺風格（style）的參考候選，以 BM25 排序後輸出 JSON。
資料取自 nextlevelbuilder/ui-ux-pro-max-skill（MIT），位於 skill 根目錄的 data/。候選只供參考，必須再經視覺方向規範篩選。"""

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DOMAINS = {
    "typography": {
        "file": "typography.csv",
        "search": ["Font Pairing Name", "Category", "Heading Font", "Body Font", "Mood/Style Keywords", "Best For", "Notes"],
        "output": ["Font Pairing Name", "Category", "Heading Font", "Body Font", "Mood/Style Keywords", "Best For", "Google Fonts URL", "Notes"],
    },
    "style": {
        "file": "styles.csv",
        "search": ["Style Category", "Type", "Keywords", "Best For", "Effects & Animation", "Era/Origin", "Aliases"],
        "output": ["Style Category", "Type", "Keywords", "Best For", "Do Not Use For", "Effects & Animation",
                   "Accessibility", "Performance", "Light Mode ✓", "Dark Mode ✓", "Complexity"],
    },
}
EXCLUDED_STATUS = {"deprecated"}
TOKEN = re.compile(r"[a-z0-9]+")
K1, B = 1.5, 0.75


def tokens(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def load(domain: str) -> list[dict]:
    config = DOMAINS[domain]
    path = DATA_DIR / config["file"]
    if not path.is_file():
        raise SystemExit(f"錯誤：找不到資料檔 {path}。這個檔案應隨 ui-design 一起提供，請重新複製 skill 的 data/。")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows if (row.get("Status") or "").strip().lower() not in EXCLUDED_STATUS]


def rank(rows: list[dict], fields: list[str], query: list[str]) -> list[tuple[float, dict]]:
    docs = [tokens(" ".join(row.get(field) or "" for field in fields)) for row in rows]
    average = sum(len(doc) for doc in docs) / max(len(docs), 1)
    frequency = {term: sum(1 for doc in docs if term in doc) for term in set(query)}
    scored = []
    for row, doc in zip(rows, docs):
        score = 0.0
        for term in query:
            hits = doc.count(term)
            if not hits:
                continue
            idf = math.log(1 + (len(docs) - frequency[term] + 0.5) / (frequency[term] + 0.5))
            score += idf * hits * (K1 + 1) / (hits + K1 * (1 - B + B * len(doc) / average))
        if score > 0:
            scored.append((score, row))
    return sorted(scored, key=lambda item: item[0], reverse=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="搜尋字體搭配或視覺風格的參考候選（英文關鍵字）。")
    parser.add_argument("--domain", required=True, choices=sorted(DOMAINS), help="typography：字體搭配；style：視覺風格")
    parser.add_argument("--query", required=True, help="英文關鍵字，例如 \"calm trustworthy healthcare editorial\"")
    parser.add_argument("--limit", type=int, default=5, help="最多輸出幾筆，預設 5")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    query = tokens(args.query)
    if not query:
        print("錯誤：--query 沒有可用的英文關鍵字。資料是英文，請改用英文描述受眾、氣質或用途，例如 \"warm handmade craft\"。", file=sys.stderr)
        return 1
    config = DOMAINS[args.domain]
    results = rank(load(args.domain), config["search"], query)[: max(args.limit, 1)]
    if not results:
        print(f"沒有符合「{args.query}」的候選，請換成更一般的英文關鍵字。", file=sys.stderr)
    output = {
        "domain": args.domain, "query": args.query,
        "note": "只是候選：必須經視覺方向規範篩選與調整，不得直接採用排序第一筆；字體搭配只涵蓋拉丁字。",
        "candidates": [{"score": round(score, 2), **{field: row.get(field, "") for field in config["output"]}} for score, row in results],
    }
    print(json.dumps(output, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
