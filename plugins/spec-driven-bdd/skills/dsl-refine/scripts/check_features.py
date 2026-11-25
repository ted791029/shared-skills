# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""檢查 truth 各端點的 feature 與 dsl.md：句型比對、DSL 範例、Data Table、起點句位置（Background 或每個 Example 的第一句）、Then 句型的回應與查證斷言、
Outline、技術詞、一句 When、標題不帶編號、重複 Rule、dsl.md 是否指向 plan 的 acceptance、用語表與 dsl.md 引用的編號是否帶 plan 前綴，以及 plan 的
acceptance 每組 When 與每句步驟是否被 plan 涵蓋表的 AC 涵蓋表、端點 feature 或 AC 句型對照涵蓋；技術修正 plan 沒有 acceptance，只檢查涵蓋表的補充案例。"""
import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

STEP = re.compile(r"^\s+(Given|When|Then|And|But) (.*)$")
BLOCK = re.compile(r"^(\s+)(Example|Scenario Outline): (.*)$")
RULE_LINE = re.compile(r"^\s+Rule: (.*)$")
ID_TITLE = re.compile(r"^(?:AC|US|GL|XUS|FR|NFR|SC)[-\d]")
COVER_COMMENT = re.compile(r"^\s*# (?:涵蓋|來源)：")
KIND = {"整數": r"\d+", "小數": r"\d+(?:\.\d+)?"}
START_PREFIX = "系統處於 "
NOT_APPLICABLE = "本端點不適用"
ASSERT_LABELS = ("回應斷言：", "查證斷言：")
# 各專案通用的技術詞；專案自己的技術說法由 truth 用語表的「技術說法對照」補充
DEFAULT_TECH = ["假 API", "假API", "假 WS", "假WS", "請求", "屬性", "localStorage", "sessionStorage", "testid", "快照", "權杖", "stub", "mock"]
SNAKE = re.compile(r"(?<![A-Za-z0-9_<])[a-z][a-z0-9]*(?:_[a-z0-9]+)+(?![A-Za-z0-9_>])")
CAMEL = re.compile(r"(?<![A-Za-z0-9_<])[a-z]+(?:[A-Z][a-z0-9]+)+(?![A-Za-z0-9_>])")
HTTP_CODE = re.compile(r"(?:狀態碼|HTTP|回應)\s*\"?[1-5]\d\d(?!\d)")


GLOSSARY = "用語表.md"
COVERAGE = "涵蓋表.md"
PLAN_FILE = ".plan.json"
TECH_FIX = "技術修正"
TECH_SOURCE = "技術："
CHANGES = ("ADD", "MOD", "無")
MAPPING_HEADER = ["AC 句型", "端點", "端點句型"]
COVERAGE_HEADER = ["AC", "When 組", "端點", "feature", "Rule", "異動"]
SUPPLEMENT_HEADER = ["來源需求", "端點", "feature", "Rule", "異動"]
BARE_ID = re.compile(r"(?<![0-9A-Za-z/_-])(?:AC|US|FR|NFR|SC|R|UI|API|DB|FS)-\d+")


def section_table(path: Path, heading: str) -> tuple[list[str], list[dict]]:
    """讀 Markdown 檔指定「## 章節」的表格，回傳（表頭、每列以表頭為鍵的字典，去掉反引號）。"""
    if not path.is_file():
        return [], []
    section = re.search(r"(?ms)^## " + re.escape(heading) + r"\s*\n(.*?)(?=^## |\Z)", path.read_text(encoding="utf-8"))
    if not section:
        return [], []
    header, rows = [], []
    for line in section.group(1).splitlines():
        if not line.strip().startswith("|") or re.match(r"^\|[-:\s|]+\|$", line.strip()):
            continue
        cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
        if not header:
            header = cells
            continue
        if len(cells) >= len(header):
            rows.append(dict(zip(header, cells)))
    return header, rows


def plan_kind(plan_dir: Path) -> str:
    """讀 plan 的 .plan.json 的種類（需求或技術修正）；沒有檔案或欄位時視為需求。"""
    path = plan_dir / PLAN_FILE
    if not path.is_file():
        return "需求"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("kind") or "需求"
    except json.JSONDecodeError:
        return "需求"


def acceptance_refs(dsl_text: str) -> list[dict]:
    """dsl.md 是 truth，只描述現況：提到 acceptance 的行（例如起點內容指向 acceptance 的預設值註解）都算問題。"""
    return [{"line": number, "text": line.strip()[:80],
             "problem": "dsl.md 不得指向 plan 的 acceptance（交付後是歷史紀錄）；起點內容寫「依該 feature 起點句上方的 `# 預設值：` 註解」"}
            for number, line in enumerate(dsl_text.splitlines(), 1) if "acceptance" in line.lower()]


def glossary_tech_terms(features: Path) -> list[str]:
    _, rows = section_table(features / GLOSSARY, "技術說法對照")
    return [row["技術說法"] for row in rows if row.get("技術說法")]


def tech_hits(text: str, terms: list[str]) -> list[str]:
    hits = [t for t in DEFAULT_TECH + terms if t in text]
    hits += SNAKE.findall(text) + CAMEL.findall(text) + HTTP_CODE.findall(text)
    return sorted(set(hits))


def check_wording(path: Path, terms: list[str]) -> dict:
    """技術詞（檔名、Rule、標題、步驟、表格）、不是剛好一句 When 的 Example、帶編號的標題或涵蓋註解、同檔重複的 Rule 名稱。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    tech, multi = [], []
    hits = tech_hits(path.stem, terms)
    if hits:
        tech.append({"file": path.name, "where": "檔名", "text": path.stem, "hits": hits})
    for line in lines:
        s = line.strip()
        m = STEP.match(line)
        if s.startswith("Rule: "):
            where, text = "Rule", s[len("Rule: "):]
        elif BLOCK.match(line):
            where, text = "標題", BLOCK.match(line).group(3)
        elif m:
            where, text = "步驟", m.group(2)
        elif s.startswith("|"):
            where, text = "表格", s
        else:
            continue
        hits = tech_hits(text, terms)
        if hits:
            tech.append({"file": path.name, "where": where, "text": text, "hits": hits})
    rules = collections.Counter(l.strip()[len("Rule: "):] for l in lines if l.strip().startswith("Rule: "))
    duplicates = [{"file": path.name, "rule": r, "count": c} for r, c in rules.items() if c > 1]
    id_titles = [{"file": path.name, "line": i + 1, "text": l.strip(),
                  "problem": "Example 標題不得以 AC、US、FR 等編號開頭，也不得加 # 涵蓋 註解；追溯只記在 plan 涵蓋表的 AC 涵蓋表"}
                 for i, l in enumerate(lines) if COVER_COMMENT.match(l) or (BLOCK.match(l) and ID_TITLE.match(BLOCK.match(l).group(3)))]
    starts = [i for i, l in enumerate(lines) if BLOCK.match(l)]
    for k, start in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        # Example 的內容到下一個 Rule 或 Outline 的 Examples 為止
        cut = next((j for j in range(start + 1, end) if lines[j].strip().startswith(("Rule: ", "Examples:"))), end)
        body = lines[start + 1:cut]
        m = BLOCK.match(lines[start])
        keywords = [STEP.match(l).group(1) for l in body if STEP.match(l)]
        whens = keywords.count("When")
        then_before_when = "When" in keywords and "Then" in keywords[:len(keywords) - 1 - keywords[::-1].index("When")]
        if whens != 1 or then_before_when:
            multi.append({"file": path.name, "example": m.group(3), "whens": whens,
                          "problem": "每個 Example 只能有一句 When：後續動作用 And 接在 When 之後，Then 全部寫在動作之後；AC 的多組 When 拆成多個 Example"})
    return {"tech_terms": tech, "multi_when": multi, "duplicate_rules": duplicates, "id_titles": id_titles}


def width(text: str) -> int:
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in text)


def align_tables(path: Path) -> bool:
    """依顯示寬度（全形算 2）對齊 feature 中的每個表格，有變動時回傳 True。"""
    original = path.read_text(encoding="utf-8")
    lines, out, i = original.split("\n"), [], 0
    while i < len(lines):
        if not lines[i].lstrip().startswith("|"):
            out.append(lines[i]); i += 1; continue
        j = i
        while j < len(lines) and lines[j].lstrip().startswith("|"):
            j += 1
        indent = lines[i][:len(lines[i]) - len(lines[i].lstrip())]
        rows = [[c.strip() for c in line.strip()[1:-1].split("|")] for line in lines[i:j]]
        cols = max(len(r) for r in rows)
        rows = [r + [""] * (cols - len(r)) for r in rows]
        widths = [max(width(r[k]) for r in rows) for k in range(cols)]
        out += [indent + "| " + " | ".join(c + " " * (widths[k] - width(c)) for k, c in enumerate(r)) + " |" for r in rows]
        i = j
    updated = "\n".join(out)
    if updated != original:
        path.write_text(updated, encoding="utf-8", newline="\n")
        return True
    return False


def value_pattern(value: str) -> str:
    """把參數對照的值轉成正規式：獨立的 N 代表數字，X 與 … 代表任意文字。"""
    escaped = re.escape(value)
    escaped = re.sub(r"(?<![A-Za-z])N(?![A-Za-z])", r"\\d+", escaped)
    escaped = re.sub(r"(?<![A-Za-z])X(?![A-Za-z])", ".+?", escaped)
    return escaped.replace("…", ".+?")


def parse_dsl(path: Path) -> dict:
    """讀 dsl.md：句型列（5 欄）、參數對照（### `{型別}` 小節的值）、每個型別的種類（字串／整數／小數）。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    enums: dict[str, list[str]] = {}
    current, section = None, ""
    rows, then_rows = [], []
    for line in lines:
        heading = re.match(r"^### `\{(.+?)\}`", line)
        if heading:
            current = heading.group(1); enums[current] = []; continue
        if line.startswith("## "):
            section = line[3:].strip()
        if line.startswith("#"):
            current = None
        if line.startswith("| `"):
            rows.append(line)
            if section.startswith("Then"):
                then_rows.append(line)
            continue
        if current and line.startswith("| ") and not line.startswith("|---"):
            cell = line.strip().strip("|").split("|")[0].strip()
            if cell not in ("值", "欄位"):
                enums[current].append(cell)
    kinds: dict[str, str] = {}
    for row in rows:
        for m in re.finditer(r"\*\*[^*]+\*\* `\{(.+?)\}`（(字串|整數|小數)", row):
            kinds.setdefault(m.group(1), m.group(2))
    return {"rows": rows, "then_rows": then_rows, "enums": enums, "kinds": kinds}


def type_regex(name: str, dsl: dict) -> str:
    kind = dsl["kinds"].get(name, "字串")
    if kind in KIND:
        return KIND[kind]
    if name in dsl["enums"] and dsl["enums"][name]:
        return '"(?:' + "|".join(value_pattern(v) for v in dsl["enums"][name]) + ')"'
    if name.endswith("列表") and dsl["enums"].get(name[:-2]):
        item = "(?:" + "|".join(value_pattern(v) for v in dsl["enums"][name[:-2]]) + ")"
        return f'"{item}(?:、{item})+"'
    return '"[^"]*"'


def compile_expr(expr: str, dsl: dict) -> re.Pattern:
    out, pos = "", 0
    for m in re.finditer(r"\{([^{}]+)\}", expr):
        out += re.escape(expr[pos:m.start()]) + f"(?:{type_regex(m.group(1), dsl)})"
        pos = m.end()
    return re.compile("^" + out + re.escape(expr[pos:]) + "$")


def expand(path: Path) -> tuple[list[str], list[tuple[str, str]], list]:
    """把 Scenario Outline 依 Examples 每列展開；回傳（展開後的行、(Rule, 標題) 清單、Outline 問題）。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    out, titles, probs, i, rule = [], [], [], 0, None
    while i < len(lines):
        if RULE_LINE.match(lines[i]):
            rule = RULE_LINE.match(lines[i]).group(1).strip()
        m = BLOCK.match(lines[i])
        if not m:
            out.append(lines[i]); i += 1; continue
        indent, kind, title = m.groups()
        j = i + 1
        while j < len(lines) and not re.match(r"^\s+(Example|Scenario Outline|Examples):|^  Rule: ", lines[j]):
            j += 1
        body = lines[i + 1:j]
        if kind == "Example":
            out += [lines[i]] + body; titles.append((rule, title)); i = j; continue
        if j >= len(lines) or not lines[j].strip().startswith("Examples:"):
            probs.append({"file": path.name, "block": title, "problem": "Outline 缺少 Examples"}); i = j; continue
        k = j + 1
        while k < len(lines) and not lines[k].strip().startswith("|"):
            k += 1
        table = []
        while k < len(lines) and lines[k].strip().startswith("|"):
            table.append([c.strip() for c in lines[k].strip()[1:-1].split("|")]); k += 1
        head, data = table[0], table[1:]
        if "編號" in head or "<編號>" in title:
            probs.append({"file": path.name, "block": title, "problem": "Outline 不得使用編號欄，Examples 只列資料欄"})
        used = set(re.findall(r"<([^<>]+)>", " ".join([title] + body)))
        if set(head) - used or used - set(head):
            probs.append({"file": path.name, "block": title, "problem": "Examples 欄位與參數不符", "diff": sorted(set(head) ^ used)})
        for row in data:
            values = dict(zip(head, row))
            sub = lambda s: re.sub(r"<([^<>]+)>", lambda x: values.get(x.group(1), x.group(0)), s)
            titles.append((rule, sub(title)))
            out += [f"{indent}Example: {sub(title)}"] + [sub(b) for b in body] + [""]
        i = k
    return out, titles, probs


def table_spec(cell: str):
    """解析 Data Table 參數欄：不支援→None；直式表格→('直式', 欄位集合)；其他→{欄位: 是否必填}。"""
    if cell.strip() == "不支援":
        return None
    vertical = re.search(r"直式表格.*?欄位：(.*?)（", cell)
    if vertical:
        return ("直式", set(vertical.group(1).split("、")))
    return {m.group(1): ("必填" in m.group(2) and "時必填" not in m.group(2))
            for m in re.finditer(r"\*\*([^*]+)\*\*[^（]*（([^）]*)）", cell)}


def check_assertions(then_rows: list[str]) -> list[dict]:
    """每個 Then 句型的測試撰寫語意都要同時寫回應斷言與查證斷言；只有一種時，另一種寫成「無，因為…」。"""
    problems = []
    for row in then_rows:
        expr = re.match(r"\| `([^`]+)`", row).group(1)
        semantics = row.rstrip().rstrip("|").split(" | ")[-1]
        missing = [label for label in ASSERT_LABELS if label not in semantics]
        if missing:
            problems.append({"pattern": expr, "missing": missing,
                             "problem": "Then 句型必須同時寫回應斷言與其他管道的查證斷言；確實只有一種時，另一種寫成「無，因為…」並列入待確認事項"})
            continue
        for label in ASSERT_LABELS:
            if re.search(re.escape(label) + r"\s*無(?!，因為)", semantics):
                problems.append({"pattern": expr, "problem": f"{label}寫「無」時必須接「，因為…」寫出理由"})
        if all(re.search(re.escape(label) + r"\s*無", semantics) for label in ASSERT_LABELS):
            problems.append({"pattern": expr, "problem": "回應斷言與查證斷言不能都是「無」"})
    return problems


def check_starts(path: Path, regs: list, exprs: list[str]) -> list[dict]:
    """起點句只能寫在 Background，或在沒有 Background 時寫在每個 Example 的第一句 Given；所有 Example 起點相同時應抽成 Background。"""
    lines = path.read_text(encoding="utf-8").splitlines()
    start_regs = [regs[i] for i, e in enumerate(exprs) if e.startswith(START_PREFIX)]
    is_start = lambda step: any(r.match(step) for r in start_regs)
    problems, n_bg, in_bg, bg_has_start = [], 0, False, False
    for line in lines:
        if line.startswith("  Background:"):
            in_bg, n_bg = True, n_bg + 1
        elif line.startswith("  Rule:") or BLOCK.match(line):
            in_bg = False
        m = STEP.match(line)
        if m and in_bg and is_start(m.group(2)):
            bg_has_start = True
    if n_bg > 1:
        problems.append({"file": path.name, "problem": f"Background 有 {n_bg} 個"})
    starts_used = []
    for block in re.split(r"(?m)^(?=[ \t]+(?:Example|Scenario Outline): )", "\n".join(lines))[1:]:
        title = BLOCK.match(block.splitlines()[0]).group(3)
        steps = [m for l in block.splitlines()[1:] if (m := STEP.match(l))]
        for k, m in enumerate(steps):
            if not is_start(m.group(2)):
                continue
            if bg_has_start:
                problems.append({"file": path.name, "example": title, "step": m.group(2), "problem": "已有 Background 起點，Example 不得再寫起點句"})
            elif k != 0 or m.group(1) != "Given":
                problems.append({"file": path.name, "example": title, "step": m.group(2), "problem": "起點句必須是 Example 的第一句 Given"})
        if not bg_has_start:
            if not steps or not (steps[0].group(1) == "Given" and is_start(steps[0].group(2))):
                problems.append({"file": path.name, "example": title, "problem": "沒有 Background 時，每個 Example 的第一句必須是 Given 起點句"})
            else:
                starts_used.append(steps[0].group(2))
    if not bg_has_start and len(starts_used) >= 2 and len(set(starts_used)) == 1:
        problems.append({"file": path.name, "start": starts_used[0], "problem": "所有 Example 都從同一個起點出發，應抽成 Background"})
    return problems


def check_endpoint(folder: Path, terms: list[str]) -> dict:
    dsl = parse_dsl(folder / "dsl.md")
    rows = dsl["rows"]
    exprs = [re.match(r"\| `([^`]+)`", r).group(1) for r in rows]
    regs = [compile_expr(e, dsl) for e in exprs]
    specs = {e: table_spec(r.split(" | ")[3]) if r.count(" | ") == 4 else None for e, r in zip(exprs, rows)}
    result = {"patterns": len(rows), "duplicates": sorted({e for e in exprs if exprs.count(e) > 1}),
              "bad_columns": [r[:40] for r in rows if r.count(" | ") != 4],
              "undeclared_types": sorted({t for e in exprs for t in re.findall(r"\{([^{}]+)\}", e)} - set(dsl["kinds"])),
              "unmatched": [], "unused": [], "examples_missing": [], "table_problems": [], "background_problems": [], "mapping_problems": [],
              "table_candidates": [], "assertion_problems": check_assertions(dsl["then_rows"]), "tech_terms": [], "multi_when": [], "duplicate_rules": [], "id_titles": [],
              "acceptance_refs": acceptance_refs((folder / "dsl.md").read_text(encoding="utf-8"))}
    used, texts = set(), set()
    for path in sorted(folder.glob("*.feature")):
        for key, found in check_wording(path, terms).items():
            result[key] += found
        lines, _, _ = expand(path)
        result["background_problems"] += check_starts(path, regs, exprs)
        matched = []
        for n, line in enumerate(lines):
            m = STEP.match(line)
            if not m:
                continue
            step = m.group(2)
            texts.add(step)
            hits = [exprs[i] for i, r in enumerate(regs) if r.match(step)]
            if len(hits) != 1:
                result["unmatched"].append({"file": path.name, "step": step, "matches": hits})
                continue
            used.add(hits[0])
            matched.append((n, hits[0], step))
            spec = specs[hits[0]]
            has = n + 1 < len(lines) and lines[n + 1].lstrip().startswith("|")
            if spec is None and has:
                result["table_problems"].append({"file": path.name, "step": step, "problem": "句型不支援 Data Table 卻帶了表格"})
            elif spec is not None and not has:
                result["table_problems"].append({"file": path.name, "step": step, "problem": "句型需要 Data Table 但沒有表格"})
            elif has:
                k, table = n + 1, []
                while k < len(lines) and lines[k].lstrip().startswith("|"):
                    table.append([c.strip() for c in lines[k].strip().strip("|").split("|")]); k += 1
                if isinstance(spec, tuple):
                    extra = {r[0] for r in table} - spec[1]
                    if extra:
                        result["table_problems"].append({"file": path.name, "step": step, "problem": "直式表格有未宣告的欄位", "fields": sorted(extra)})
                elif set(table[0]) - set(spec) or {k for k, req in spec.items() if req} - set(table[0]):
                    result["table_problems"].append({"file": path.name, "step": step, "problem": "表頭與 DSL 宣告不符", "header": table[0]})
        k = 0
        while k < len(matched):
            j = k
            while j + 1 < len(matched) and matched[j + 1][0] == matched[j][0] + 1 and matched[j + 1][1] == matched[k][1]:
                j += 1
            if j - k + 1 >= 3:
                result["table_candidates"].append({"file": path.name, "pattern": matched[k][1], "steps": [s for _, _, s in matched[k:j + 1]],
                                                   "problem": "同一句型連續三行以上只差參數值，應合成一句帶 Data Table 的步驟"})
            k = j + 1
    result["unused"] = [e for e in exprs if e not in used]
    dsl_text = (folder / "dsl.md").read_text(encoding="utf-8")
    section = re.search(r"(?ms)^## 參數對照" + chr(10) + r"(.*?)(?=^## )", dsl_text)
    if section and not re.search(r"(?m)^### ", section.group(1)):
        result["mapping_problems"].append({"problem": "參數對照段落沒有任何型別，應刪除整段"})
    result["tbd"] = dsl_text.count("（擬定）")
    feature_text = chr(10).join(p.read_text(encoding="utf-8") for p in sorted(folder.glob("*.feature")))
    for name, values in dsl["enums"].items():
        rows_using = [r for r in rows if "{" + name + "}" in r]
        if len(rows_using) < 3:
            result["mapping_problems"].append({"type": name, "problem": f"只有 {len(rows_using)} 列句型使用，應寫在該列而不是參數對照"})
        for v in values:
            pattern = value_pattern(v)
            if not re.search(r'"' + pattern + r'"|\|\s*' + pattern + r'\s*\|', feature_text):
                result["mapping_problems"].append({"type": name, "value": v, "problem": "feature 沒有用到這個值"})
    result["examples_missing"] = [ex for r in rows if r.count(" | ") == 4 for ex in r.split(" | ")[1].split("<br>")
                                  if re.sub(r"\{([^{}]*)\}", r"\1", ex) not in texts]
    result["ok"] = not any(result[k] for k in ("duplicates", "bad_columns", "undeclared_types", "unmatched", "unused",
                                                "examples_missing", "table_problems", "background_problems", "mapping_problems",
                                                "table_candidates", "assertion_problems", "tech_terms", "multi_when", "duplicate_rules", "id_titles",
                                                "acceptance_refs"))
    return result


def check_titles(folders: list[Path]) -> dict:
    """同一份 feature 同一條 Rule 底下的 Example 標題不得重複，並彙整 Outline 的問題。"""
    loaded = [(path, *expand(path)) for folder in folders for path in sorted(folder.glob("*.feature"))]
    duplicates, total = [], 0
    for path, _, titles, _ in loaded:
        total += len(titles)
        for (rule, title), count in collections.Counter(titles).items():
            if count > 1:
                duplicates.append({"file": path.name, "rule": rule, "title": title, "count": count})
    result = {"tests": total, "duplicate_titles": duplicates, "outline_problems": [p for _, _, _, ps in loaded for p in ps]}
    result["ok"] = not (duplicates or result["outline_problems"])
    return result


def normalize(step: str) -> str:
    """把步驟或句型正規化：引號內的值、{型別} 與獨立的數字都換成 {}，比對時只看固定文字。"""
    text = re.sub(r'"[^"]*"', "{}", step.strip())
    text = re.sub(r"\{[^{}]+\}", "{}", text)
    text = re.sub(r"(?<![A-Za-z0-9{])\d+(?![A-Za-z0-9}])", "{}", text)
    return re.sub(r"\s+", " ", text)


def parse_acceptance_groups(acceptance: Path) -> list[dict]:
    """讀 acceptance 的每個 AC：AC 編號、第一句 When 之前的 Given，與每組 When 的步驟。"""
    acs = []
    for path in sorted(acceptance.glob("*.feature")):
        lines = path.read_text(encoding="utf-8").splitlines()
        starts = [i for i, l in enumerate(lines) if BLOCK.match(l)]
        for n, start in enumerate(starts):
            end = starts[n + 1] if n + 1 < len(starts) else len(lines)
            for k in range(start + 1, end):
                if RULE_LINE.match(lines[k]):
                    end = k
                    break
            title = BLOCK.match(lines[start]).group(3).strip()
            ac_id = title.split(" ")[0]
            steps = [(m.group(1), m.group(2).strip()) for l in lines[start + 1:end] if (m := STEP.match(l))]
            given, groups, mode = [], [], "given"
            for keyword, text in steps:
                if keyword == "When":
                    groups.append({"index": len(groups) + 1, "steps": [text]}); mode = "when"
                elif keyword == "Then":
                    groups[-1]["steps"].append(text); mode = "then"
                elif keyword in ("And", "But") and mode != "given":
                    groups[-1]["steps"].append(text)
                else:
                    given.append(text); mode = "given"
            acs.append({"file": path.name, "id": ac_id, "given": given, "groups": groups})
    return acs


def check_coverage(plan_features: Path, features: Path, folders: list[Path], technical: bool = False) -> dict:
    """plan 的每組 When 都要在涵蓋表的 AC 涵蓋表有列；AC 涵蓋表與補充案例的列指向的 feature 與 Rule 存在於 truth、異動是 ADD、MOD 或 無；
    AC 的每句步驟都要逐字出現在端點 feature，或經 AC 句型對照對到某端點 dsl.md 的句型；只登記為本端點不適用不算涵蓋。
    技術修正 plan 沒有 AC：AC 的兩張表只留表頭，補充案例的來源需求寫「技術：」加技術項的問題。"""
    acs = [] if technical else parse_acceptance_groups(plan_features / "acceptance")
    problems, tables = [], {}
    for heading, expected in (("AC 句型對照", MAPPING_HEADER), ("AC 涵蓋表", COVERAGE_HEADER), ("補充案例", SUPPLEMENT_HEADER)):
        header, table = section_table(plan_features / COVERAGE, heading)
        missing = [name for name in expected if name not in header]
        if missing:
            problems.append({"table": heading, "problem": f"{COVERAGE}「{heading}」缺少欄位 {missing}，請依樣板補上這張表與欄位"})
            table = []
        tables[heading] = table
    mapping, rows, supplements = tables["AC 句型對照"], tables["AC 涵蓋表"], tables["補充案例"]
    if technical:
        for heading in ("AC 句型對照", "AC 涵蓋表"):
            for row in tables[heading]:
                problems.append({"table": heading, "row": row,
                                 "problem": f"技術修正 plan 沒有 AC，「{heading}」只留表頭；技術項新增或修改的 Rule 登記在補充案例"})
        for row in supplements:
            if not row["來源需求"].startswith(TECH_SOURCE):
                problems.append({"table": "補充案例", "row": row,
                                 "problem": "技術修正 plan 沒有 spec.md，補充案例的來源需求寫「技術：」加技術項的問題"})
        mapping, rows = [], []
    derived_steps, rules_by_file, dsl_patterns, steps_by_file = set(), {}, {}, {}
    for folder in folders:
        name = endpoint_name(folder, features)
        dsl_patterns[name] = {normalize(e) for e in re.findall(r"^\| `([^`]+)`", (folder / "dsl.md").read_text(encoding="utf-8"), re.M)}
        for path in sorted(folder.glob("*.feature")):
            lines, _, _ = expand(path)
            rules_by_file[f"{name}/{path.name}"] = {RULE_LINE.match(l).group(1).strip() for l in lines if RULE_LINE.match(l)}
            steps_by_file[(name, path.name)] = {normalize(STEP.match(l).group(2)) for l in lines if STEP.match(l)}
            derived_steps |= steps_by_file[(name, path.name)]
    mapped = set()
    for row in mapping:
        if row["端點句型"] == NOT_APPLICABLE:
            used_there = sorted(f"{name}/{f}" for (name, f), steps in steps_by_file.items()
                                if name == row["端點"] and normalize(row["AC 句型"]) in steps)
            if used_there:
                problems.append({"row": row, "files": used_there, "problem": "AC 句型對照登記為本端點不適用，該端點的 feature 卻仍使用這句"})
        elif normalize(row["端點句型"]) in dsl_patterns.get(row["端點"], set()):
            mapped.add(normalize(row["AC 句型"]))
    for table_name, table in (("AC 涵蓋表", rows), ("補充案例", supplements)):
        for row in table:
            key = f"{row['端點']}/{row['feature']}"
            if key not in rules_by_file:
                problems.append({"table": table_name, "row": row, "problem": f"{table_name}指向的 feature 不存在於 truth"})
            elif row["Rule"] not in rules_by_file[key]:
                problems.append({"table": table_name, "row": row, "problem": f"{table_name}指向的 Rule 不在該 feature 中"})
            if row["異動"] not in CHANGES:
                problems.append({"table": table_name, "row": row,
                                 "problem": "異動必須是 ADD、MOD 或 無；被刪除的 Rule 不列在涵蓋表，只記在 truth-changes.md"})
    uncovered_groups, uncovered_steps = [], []
    for row in rows:
        if not any(ac["id"] == row["AC"] and any(str(g["index"]) == row["When 組"] for g in ac["groups"]) for ac in acs):
            problems.append({"table": "AC 涵蓋表", "row": row, "problem": "AC 涵蓋表的 AC 或 When 組不存在於 acceptance"})
    for ac in acs:
        for group in ac["groups"]:
            if not any(r["AC"] == ac["id"] and r["When 組"] == str(group["index"]) for r in rows):
                uncovered_groups.append({"ac": ac["id"], "group": group["index"], "when": group["steps"][0]})
        for text in ac["given"] + [s for g in ac["groups"] for s in g["steps"]]:
            norm = normalize(text)
            if norm not in derived_steps and norm not in mapped:
                uncovered_steps.append({"ac": ac["id"], "step": text,
                                        "problem": "沒有逐字出現在任何端點 feature，也沒有在 AC 句型對照登記對到某個端點 dsl.md 的句型；只登記為本端點不適用不算涵蓋"})
    result = {"technical_fix": technical, "acs": len(acs), "groups": sum(len(ac["groups"]) for ac in acs), "rows": len(rows),
              "supplements": len(supplements), "row_problems": problems, "uncovered_groups": uncovered_groups, "uncovered_steps": uncovered_steps}
    result["ok"] = not (problems or uncovered_groups or uncovered_steps)
    return result


def check_ids(features: Path, folders: list[Path], include_glossary: bool) -> list[dict]:
    """truth 的 dsl.md 與用語表引用 plan 的編號時必須帶 plan 前綴（例如 002/R-08）。"""
    paths = [folder / "dsl.md" for folder in folders] + ([features / GLOSSARY] if include_glossary else [])
    problems = []
    for path in paths:
        if not path.is_file():
            continue
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in BARE_ID.finditer(line):
                problems.append({"file": path.relative_to(features).as_posix(), "line": number, "id": match.group(0),
                                 "problem": f"引用 plan 的編號必須帶 plan 前綴，例如 002/{match.group(0)}"})
    return problems


def endpoint_folders(features: Path) -> list[Path]:
    """端點資料夾：features/ 底下含 dsl.md 的資料夾（acceptance 沒有 dsl.md，不會被當成端點）。"""
    return sorted(p.parent for p in features.rglob("dsl.md") if p.parent != features)


def endpoint_name(folder: Path, features: Path) -> str:
    return folder.relative_to(features).as_posix()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="檢查 truth 各端點的 feature 與 dsl.md：句型比對、DSL 範例、Data Table、起點句位置、Then 句型的回應與查證斷言、Outline、一句 When、標題不帶編號、dsl.md 指向 acceptance、編號的 plan 前綴，以及 plan 的 acceptance 的 AC 涵蓋（技術修正 plan 沒有 acceptance，只檢查涵蓋表的補充案例）。")
    parser.add_argument("plan_dir", help="plan 資料夾，內含 features/acceptance/ 與 features/涵蓋表.md（.plan.json 的種類為技術修正時不需要 acceptance），例如 specs/plans/004-ranking")
    parser.add_argument("--features", help="truth 的 features 資料夾，預設為 plan 資料夾往上兩層的 truth/features，例如 specs/truth/features")
    parser.add_argument("--endpoint", action="append", help="只檢查指定的端點資料夾（相對 truth 的 features/ 的路徑，例如 backend 或 frontend），可重複；預設檢查全部並加做用語表的編號與 AC 涵蓋檢查")
    parser.add_argument("--fix-tables", action="store_true", help="檢查前先依顯示寬度對齊所有 feature 的表格")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    plan_dir = Path(args.plan_dir)
    if not plan_dir.is_dir():
        print(f"錯誤：找不到 plan 資料夾 {plan_dir}。請傳入 specs/plans/ 底下的 plan 資料夾，例如 specs/plans/004-ranking", file=sys.stderr)
        return 1
    plan_features = plan_dir / "features"
    acceptance = plan_features / "acceptance"
    technical = plan_kind(plan_dir) == TECH_FIX
    if not technical and (not acceptance.is_dir() or not any(acceptance.glob("*.feature"))):
        print(f"錯誤：{plan_dir} 底下需要 features/acceptance/（含 .feature）。請先執行 spec-by-example，再傳入 plan 資料夾，例如 specs/plans/004-ranking；"
              f"只為技術修正的 plan 要以 plan-package open --kind 技術修正 開立", file=sys.stderr)
        return 1
    if technical:
        print(f"{plan_dir.name} 是技術修正 plan，沒有 acceptance，AC 涵蓋只檢查涵蓋表的補充案例", file=sys.stderr)
    features = Path(args.features) if args.features else plan_dir.resolve().parent.parent / "truth" / "features"
    if not features.is_dir():
        print(f"錯誤：找不到 truth 的 features 資料夾 {features}。請先產出各端點的 feature 與 dsl.md，或以 --features 指定，例如 --features specs/truth/features", file=sys.stderr)
        return 1
    folders = endpoint_folders(features)
    if args.endpoint:
        missing = [name for name in args.endpoint if not (features / name / "dsl.md").is_file()]
        if missing:
            print(f"錯誤：找不到端點 {missing} 的 dsl.md。可用的端點：{[endpoint_name(p, features) for p in folders]}", file=sys.stderr)
            return 1
        folders = [features / name for name in args.endpoint]
    if not folders:
        print(f"錯誤：{features} 底下沒有任何含 dsl.md 的端點資料夾。請先產出各端點的 feature 與 dsl.md 再檢查", file=sys.stderr)
        return 1
    if args.fix_tables:
        fixed = [p.name for folder in folders for p in sorted(folder.glob("*.feature")) if align_tables(p)]
        print(f"重新對齊表格的檔案：{fixed or '無'}", file=sys.stderr)
    terms = glossary_tech_terms(features)
    report = {"plan_kind": TECH_FIX if technical else "需求", "glossary_tech_terms": terms,
              "endpoints": {endpoint_name(folder, features): check_endpoint(folder, terms) for folder in folders}}
    report["titles"] = check_titles(folders)
    report["bare_ids"] = check_ids(features, folders, include_glossary=not args.endpoint)
    if not args.endpoint:
        report["coverage"] = check_coverage(plan_features, features, folders, technical)
    report["ok"] = (all(r["ok"] for r in report["endpoints"].values()) and report["titles"]["ok"] and not report["bare_ids"]
                    and report.get("coverage", {"ok": True})["ok"])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print("PASS" if report["ok"] else "FAIL：請依報告修正後重新檢查", file=sys.stderr)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
