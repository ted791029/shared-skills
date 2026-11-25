# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""把 /bdd verify 各端點的測試報告（behave JSON、Playwright JSON、vitest JSON）正規化為每個 Example 的通過／失敗，與上次的 verify 結果比對出回歸並存回結果檔。"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # 匯入同目錄的 resolve_scope 時不在 skill 內留下 __pycache__
from resolve_scope import SCOPE_FORMS, find_endpoint_dir, parse_feature, parse_scope, select_scope_examples, title_of  # noqa: E402
from run_suite import files_changed_after, project_snapshot  # noqa: E402

RESULT_VERSION = 2  # 2：頂層 last_run（產生結果的執行與其結束時的檔案清單摘要），Example 加 run 與失敗的 message
MESSAGE_LIMIT = 300
ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
EXAMPLE_PREFIXES = ("Scenario Outline", "Scenario Template", "Scenario", "Example", "場景大綱", "劇本大綱", "場景", "劇本")
BACKGROUND_PREFIXES = ("Background", "背景")
UNEXECUTED_VITEST = ("pending", "skipped", "todo", "disabled")


class ReportError(Exception):
    pass


class FeatureIndex:
    """快取 feature 的解析結果，把報告中的 feature 路徑與行號或標題對回 Example。"""

    def __init__(self, root: Path):
        self.root = root
        self.cache: dict[Path, dict] = {}

    def load(self, feature: Path) -> dict | None:
        feature = feature.resolve()
        if feature not in self.cache:
            if not feature.is_file():
                self.cache[feature] = None
            else:
                parsed = parse_feature(feature)
                lines = feature.read_text(encoding="utf-8").splitlines()
                rule_titles = {rule["line"]: rule["title"] for rule in parsed["rules"]}
                feature_title = title_of(lines[parsed["feature_line"] - 1]) if parsed["feature_line"] else ""
                self.cache[feature] = {"parsed": parsed, "rule_titles": rule_titles, "feature_title": feature_title}
        return self.cache[feature]

    def relative(self, feature: Path) -> str | None:
        try:
            return feature.resolve().relative_to(self.root).as_posix()
        except ValueError:
            return None

    def record(self, feature: Path, example: dict) -> dict:
        info = self.load(feature)
        rel = self.relative(feature)
        endpoint_dir = find_endpoint_dir(feature.resolve())
        rule = info["rule_titles"].get(example["rule_line"], "") if example["rule_line"] else ""
        return {
            "key": f"{rel}::{rule}::{example['title']}",
            "endpoint_dir": self.relative(endpoint_dir) if endpoint_dir else None,
            "feature": rel,
            "line": example["line"],
            "rule": rule,
            "title": example["title"],
        }

    def by_line(self, feature: Path, line: int) -> dict | None:
        """行號落在哪個 Example（場景大綱的例子列歸入大綱）。"""
        info = self.load(feature)
        if info is None or self.relative(feature) is None:
            return None
        candidates = [e for e in info["parsed"]["examples"] if e["line"] <= line]
        return max(candidates, key=lambda e: e["line"]) if candidates else None

    def by_title(self, feature: Path, rule_title: str | None, example_title: str) -> dict | None:
        info = self.load(feature)
        if info is None:
            return None
        examples = [
            e for e in info["parsed"]["examples"]
            if rule_title is None or info["rule_titles"].get(e["rule_line"], "") == rule_title
        ]
        exact = [e for e in examples if e["title"] == example_title]
        if len(exact) == 1:
            return exact[0]
        outlines = [
            e for e in examples if e["kind"] == "outline"
            and re.fullmatch(".*?".join(re.escape(part) for part in re.split(r"<[^>]+>", e["title"])), example_title)
        ]
        return outlines[0] if len(outlines) == 1 else None

    def examples_under(self, feature: Path, rule_title: str | None) -> list[dict]:
        info = self.load(feature)
        if info is None:
            return []
        return [
            e for e in info["parsed"]["examples"]
            if rule_title is None or info["rule_titles"].get(e["rule_line"], "") == rule_title
        ]


def clean_message(text: str | None) -> str:
    if not text:
        return ""
    text = ANSI_PATTERN.sub("", text).strip()
    return text if len(text) <= MESSAGE_LIMIT else text[:MESSAGE_LIMIT] + "…"


def load_json(path: Path, kind: str) -> object:
    if not path.is_file():
        raise ReportError(f"找不到 {kind} 報告 {path.as_posix()}。請確認完整指令有加上 JSON 報告輸出，且路徑與傳入的相同。")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ReportError(f"{kind} 報告 {path.as_posix()} 不是 UTF-8 JSON（{error}）。請確認報告格式為 JSON 且測試執行有正常結束。")


def read_behave(report: Path, run_dir: Path, index: FeatureIndex, entries: list, unmapped: list, unexecuted: list) -> None:
    data = load_json(report, "behave")
    if not isinstance(data, list):
        raise ReportError(f"behave 報告 {report.as_posix()} 的最外層不是 feature 陣列。請以 behave 的 -f json 產生報告。")
    for feature in data:
        for element in feature.get("elements", []):
            if element.get("type") != "scenario":
                continue
            location = element.get("location", "")
            path_text, _, line_text = location.rpartition(":")
            if not line_text.isdigit():
                unmapped.append({"report": report.as_posix(), "entry": location, "reason": "location 沒有行號"})
                continue
            feature_path = run_dir / path_text
            example = index.by_line(feature_path, int(line_text))
            if example is None:
                unmapped.append({"report": report.as_posix(), "entry": location, "reason": "對不到專案內 feature 的 Example"})
                continue
            steps = element.get("steps", [])
            status = element.get("status")
            step_statuses = [s.get("result", {}).get("status") for s in steps]
            ran_failure = any(st not in (None, "passed", "skipped", "untested", "pending") for st in step_statuses)
            if not ran_failure and (status in ("skipped", "untested", "pending") or (status is None and not any(st == "passed" for st in step_statuses))):
                # 行號或名稱篩選時未選取的場景（與 Background）仍列在報告中，沒有任何 step 實際執行：視為報告中不存在
                unexecuted.append({"report": report.as_posix(), "entry": location, "status": status})
                continue
            if status is None:
                status = "passed" if steps and all(st == "passed" for st in step_statuses) else "failed"
            message = ""
            for step in steps:
                result = step.get("result", {})
                if result.get("status") not in (None, "passed", "skipped", "untested"):
                    error = result.get("error_message")
                    detail = "\n".join(error) if isinstance(error, list) else (error or result.get("status"))
                    message = f"{step.get('keyword', '').strip()} {step.get('name', '')}：{detail}"
                    break
            if status != "passed" and not message:
                message = f"狀態：{status}"
            entries.append({"feature": feature_path, "example": example, "passed": status == "passed", "message": message})


def generated_mapping(spec_file: Path, config_dir: Path) -> tuple[Path, dict[int, int]] | None:
    """讀 playwright-bdd 產生的測試檔，回傳來源 feature 與 pwTestLine → pickleLine 對照。"""
    if not spec_file.is_file():
        return None
    text = spec_file.read_text(encoding="utf-8")
    source = re.search(r"^// Generated from: (.+)$", text, flags=re.MULTILINE)
    data = re.search(r"bdd-data-start\s*\n(.*?)\n\s*\]; // bdd-data-end", text, flags=re.DOTALL)
    if not source or not data:
        return None
    mapping = {}
    for line in data.group(1).splitlines():
        line = line.strip().rstrip(",")
        if line:
            item = json.loads(line)
            mapping[item["pwTestLine"]] = item["pickleLine"]
    return config_dir / source.group(1).strip().replace("\\", "/"), mapping


def is_unexecuted_playwright(test: dict) -> bool:
    """Playwright 的 skipped（test.skip、fixme、被篩選略過）沒有實際執行；有 failed、timedOut、interrupted 結果者一律算已執行。"""
    results = test.get("results") or []
    if any(r.get("status") in ("failed", "timedOut", "interrupted") for r in results):
        return False
    if test.get("status") == "skipped":
        return True
    return bool(results) and all(r.get("status") == "skipped" for r in results)


def read_playwright(report: Path, index: FeatureIndex, entries: list, unmapped: list, unexecuted: list) -> None:
    data = load_json(report, "Playwright")
    if not isinstance(data, dict) or "suites" not in data or "config" not in data:
        raise ReportError(f"Playwright 報告 {report.as_posix()} 缺少 config 或 suites。請以 --reporter=json 產生報告。")
    config = data["config"]
    config_dir = Path(config.get("configFile", "")).parent
    test_root = Path(config.get("rootDir", ""))
    cache: dict[str, tuple | None] = {}

    def walk(suite: dict) -> None:
        for spec in suite.get("specs", []):
            entry = f"{spec.get('file')}:{spec.get('line')} {spec.get('title', '')}"
            if spec["file"] not in cache:
                cache[spec["file"]] = generated_mapping(test_root / spec["file"], config_dir)
            mapped = cache[spec["file"]]
            if mapped is None or spec.get("line") not in mapped[1]:
                unmapped.append({"report": report.as_posix(), "entry": entry, "reason": "找不到 playwright-bdd 產生檔或其中的 bddFileData"})
                continue
            feature_path, lines = mapped
            example = index.by_line(feature_path, lines[spec["line"]])
            if example is None:
                unmapped.append({"report": report.as_posix(), "entry": entry, "reason": "對不到專案內 feature 的 Example"})
                continue
            tests = spec.get("tests", [])
            executed = [t for t in tests if not is_unexecuted_playwright(t)]
            if not executed:
                unexecuted.append({"report": report.as_posix(), "entry": entry, "status": "skipped"})
                continue
            tests = executed
            passed = bool(tests) and all(
                t.get("status") in ("expected", "flaky") and t.get("results") and t["results"][-1].get("status") == "passed"
                for t in tests
            )
            message = ""
            for t in tests:
                for result in reversed(t.get("results", [])):
                    error = result.get("error") or (result.get("errors") or [{}])[0]
                    if error.get("message"):
                        message = error["message"]
                        break
                if message:
                    break
            if not passed and not message:
                message = "未執行或被略過（狀態：" + "、".join(str(t.get("status")) for t in tests) + "）"
            entries.append({"feature": feature_path, "example": example, "passed": passed, "message": message})
        for child in suite.get("suites", []):
            walk(child)

    for suite in data["suites"]:
        walk(suite)


def split_ancestor(title: str) -> tuple[str, str]:
    keyword, _, rest = title.partition(":")
    return keyword.strip(), rest.strip()


def read_vitest(report: Path, feature_dirs: list[Path], index: FeatureIndex, entries: list, unmapped: list, unexecuted: list) -> None:
    data = load_json(report, "vitest")
    if not isinstance(data, dict) or "testResults" not in data:
        raise ReportError(f"vitest 報告 {report.as_posix()} 缺少 testResults。請以 --reporter=json 產生報告。")
    features_by_title: dict[str, list[Path]] = {}
    for directory in feature_dirs:
        if not directory.is_dir():
            raise ReportError(f"找不到 feature 資料夾 {directory.as_posix()}。請傳入 vitest 執行的端點資料夾。")
        for feature in sorted(directory.rglob("*.feature")):
            info = index.load(feature)
            features_by_title.setdefault(info["feature_title"], []).append(feature)
    for file_result in data["testResults"]:
        for assertion in file_result.get("assertionResults", []):
            ancestors = [split_ancestor(t) for t in assertion.get("ancestorTitles", [])]
            entry = " > ".join(assertion.get("ancestorTitles", []))
            feature_title = next((rest for kw, rest in ancestors if kw in ("Feature", "功能")), None)
            rule_title = next((rest for kw, rest in ancestors if kw in ("Rule", "規則")), None)
            example_title = next((rest for kw, rest in ancestors if kw in EXAMPLE_PREFIXES), None)
            is_background = any(kw in BACKGROUND_PREFIXES for kw, _ in ancestors)
            if assertion.get("status") in UNEXECUTED_VITEST:
                # -t 篩選後 pending、skipped、todo、disabled 的測項沒有實際執行：視為報告中不存在
                unexecuted.append({"report": report.as_posix(), "entry": entry, "status": assertion.get("status")})
                continue
            candidates = features_by_title.get(feature_title or "", [])
            if len(candidates) != 1:
                unmapped.append({"report": report.as_posix(), "entry": entry, "reason": "Feature 標題在指定資料夾中找不到或不唯一"})
                continue
            feature_path = candidates[0]
            passed = assertion.get("status") == "passed"
            message = clean_message("\n".join(assertion.get("failureMessages", []))) if not passed else ""
            if not passed and not message:
                message = f"狀態：{assertion.get('status')}"
            if is_background:
                for example in index.examples_under(feature_path, rule_title):
                    entries.append({"feature": feature_path, "example": example, "passed": passed, "message": f"Background {assertion.get('title', '')}：{message}" if message else ""})
                continue
            example = index.by_title(feature_path, rule_title, example_title or "")
            if example is None:
                unmapped.append({"report": report.as_posix(), "entry": entry, "reason": "Example 標題在 feature 中找不到或不唯一"})
                continue
            entries.append({"feature": feature_path, "example": example, "passed": passed, "message": f"{assertion.get('title', '')}：{message}" if message else ""})


def scope_records(targets: list[str], index: FeatureIndex, option: str = "--expected-fail") -> dict[str, dict]:
    """把 --expected-fail、--ran-scope 的 端點資料夾、feature、feature:行號[:行號…] 或 feature ＞ Rule「名稱」 展開為 Example 的 key 與紀錄。"""
    records: dict[str, dict] = {}
    for target in targets:
        try:
            path, lines, rule_names = parse_scope(target)
        except ValueError as error:
            raise ReportError(f"{option} 的 {target}：{error}")
        path = path if path.is_absolute() else index.root / path
        if not path.exists():
            raise ReportError(
                f"{option} 的 {target} 不存在。請傳入相對於 --root 的範疇（行號為 Feature、Rule、Example 或場景大綱的標題行；"
                f"含空白的範疇整段以引號包成一個參數）：{SCOPE_FORMS}"
            )
        if index.relative(path) is None:
            raise ReportError(f"{option} 的 {target} 不在專案根目錄 {index.root.as_posix()} 底下，請改用專案內的 feature 路徑。")
        features = sorted(path.rglob("*.feature")) if path.is_dir() else [path]
        if not features:
            raise ReportError(f"{option} 的 {target} 底下沒有任何 .feature 檔，請確認路徑。")
        for feature in features:
            parsed = index.load(feature)["parsed"]
            try:
                chosen = select_scope_examples(feature, parsed, lines, rule_names)
            except ValueError as error:
                raise ReportError(f"{option} 的 {target}：{error}")
            for example in chosen:
                record = index.record(feature, example)
                records[record["key"]] = record
    return records


def aggregate(entries: list, index: FeatureIndex) -> dict[str, dict]:
    """同一個 Example 在同一份報告中的所有項目（場景大綱的每列、每個瀏覽器專案）都通過才算通過；
    同一個 Example 出現在多份報告時，只採用最後傳入的那一份（單一 Example 的重跑報告覆蓋原報告）。"""
    latest: dict[str, int] = {}
    records = []
    for item in entries:
        record = index.record(item["feature"], item["example"])
        records.append(record)
        latest[record["key"]] = max(latest.get(record["key"], -1), item["seq"])
    current: dict[str, dict] = {}
    for item, record in zip(entries, records):
        if item["seq"] != latest[record["key"]]:
            continue
        existing = current.setdefault(record["key"], {**record, "status": "passed", "message": ""})
        if not item["passed"]:
            existing["status"] = "failed"
            if not existing["message"]:
                existing["message"] = clean_message(item["message"]) or "失敗（報告沒有錯誤訊息）"
    return current


def load_previous(path: Path) -> dict[str, dict] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {item["key"]: item for item in data["examples"]}
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise ReportError(
            f"上次的 verify 結果 {path.as_posix()} 格式不正確（{error}）。"
            "這個檔案只由 verify_result.py 寫入；請還原它，或刪除後重新執行 verify 建立新基準。"
        )


def still_exists(item: dict, index: FeatureIndex) -> bool:
    feature = index.root / item["feature"]
    info = index.load(feature)
    if info is None:
        return False
    return any(
        e["title"] == item["title"] and info["rule_titles"].get(e["rule_line"], "") == item["rule"]
        for e in info["parsed"]["examples"]
    )


def view(item: dict, with_message: bool = False) -> dict:
    shown = {"endpoint_dir": item["endpoint_dir"], "location": f"{item['feature']}:{item['line']}", "rule": item["rule"], "title": item["title"]}
    if with_message:
        shown["message"] = item.get("message", "")
    return shown


def compare(current: dict[str, dict], previous: dict[str, dict] | None, index: FeatureIndex, expected_fail: set[str], partial: bool = False, ran_scope: dict[str, dict] | None = None) -> tuple[dict, list[dict]]:
    groups = {"regressions": [], "in_progress": [], "no_baseline_failures": [], "fixed": [], "not_run": [], "carried": [], "removed": []}
    ran_dirs = {item["endpoint_dir"] for item in current.values()}
    saved = []
    for key in sorted(current, key=lambda k: (current[k]["feature"], current[k]["line"])):
        item = current[key]
        before = previous.get(key) if previous is not None else None
        failed = item["status"] == "failed"
        if previous is None:
            baseline = item["status"]
            if failed:
                groups["no_baseline_failures"].append(view(item, True))
        elif failed and key in expected_fail:
            baseline = "failed"
            groups["in_progress"].append({**view(item, True), "new": before is None, "expected_fail": True})
        elif before is None:
            baseline = item["status"]
            if failed:
                groups["in_progress"].append({**view(item, True), "new": True})
        elif before["baseline"] == "passed":
            baseline = "passed"
            if failed:
                groups["regressions"].append(view(item, True))
        else:
            baseline = item["status"]
            if failed:
                groups["in_progress"].append({**view(item, True), "new": False})
            else:
                groups["fixed"].append(view(item))
        saved.append({k: item[k] for k in ("key", "endpoint_dir", "feature", "line", "rule", "title", "status")} | {"baseline": baseline})
    for key, before in sorted((previous or {}).items()):
        if key in current:
            continue
        if still_exists(before, index):
            if ran_scope is not None:
                # Example 層級部分執行：只有本次實際執行的範疇內缺報告才是 not_run，範疇外沿用上次結果
                if key in ran_scope:
                    groups["not_run"].append(view(before))
                else:
                    groups["carried"].append(view(before))
            elif partial and before["endpoint_dir"] not in ran_dirs:
                groups["carried"].append(view(before))  # 部分執行：這次完全沒有執行的端點資料夾沿用上次結果
            else:
                groups["not_run"].append(view(before))
            saved.append(before)
        else:
            groups["removed"].append(view(before))
    for key, record in sorted((ran_scope or {}).items()):
        if key not in current and (previous is None or key not in previous):
            groups["not_run"].append(view(record))  # 範疇內的新 Example 沒有報告：不存入結果，仍列為未執行
    saved.sort(key=lambda item: (item["feature"], item["line"]))
    return groups, saved


def load_run(path: Path, root: Path) -> dict:
    """讀 run_suite.py 寫出的執行紀錄；逾時的執行沒有可用報告，不得存回。"""
    if not path.is_file():
        raise ReportError(f"找不到執行紀錄 {path.as_posix()}。請傳入 run_suite.py stdout 的 run_record 路徑（<out>/run-<代號>.json）。")
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
        run_id, snapshot = record["run_id"], record["snapshot"]["digest"]
    except (json.JSONDecodeError, KeyError, TypeError, UnicodeDecodeError) as error:
        raise ReportError(f"執行紀錄 {path.as_posix()} 格式不正確（{error}）。這個檔案只由 run_suite.py 寫入，請重新執行 run_suite.py 產生。")
    if record.get("timed_out"):
        raise ReportError(f"執行紀錄 {path.as_posix()}（{run_id}）有指令逾時，報告可能不完整，不得比對或存回；請排查卡住的原因後重新執行。")
    if Path(record.get("root", "")).resolve() != root:
        raise ReportError(f"執行紀錄 {path.as_posix()} 的專案根目錄是 {record.get('root')}，與 --root {root.as_posix()} 不同；請以同一個專案根目錄執行 run_suite.py 與本腳本。")
    return record


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="把 /bdd verify 各端點的測試報告正規化為每個 Example 的通過／失敗，與上次的 verify 結果比對出回歸並存回結果檔。"
        "上次通過（或上次已是回歸）而這次失敗的列為回歸；上次就失敗、新出現或列在 --expected-fail 的失敗列為開發中，並存為失敗；"
        "沒有上次結果時全部失敗列為無基準。stdout 預設只印摘要，完整結果用 --out 寫檔。"
        "同一個 Example 出現在多份報告時採用最後傳入的那一份，可用來以單一 Example 的重跑報告覆蓋原報告。"
        "報告中沒有實際執行的項目（行號或名稱篩選後 behave 的 skipped／status 為 None 且沒有 step 結果的場景與 Background、vitest 的 pending／skipped／todo、Playwright 的 skipped）視為報告中不存在："
        "不覆蓋同一 Example 在其他報告的結果、不算失敗，列在輸出的 unexecuted_items；只有真正執行且失敗（有失敗或錯誤的 step、failed、timedOut）才算失敗。--ran-scope 範疇內缺報告的 Example 仍列為 not_run。"
    )
    parser.add_argument("--root", default=".", help="專案根目錄，feature 路徑與結果檔都相對於它（預設為目前目錄）")
    parser.add_argument("--behave", nargs=2, action="append", default=[], metavar=("JSON", "RUN_DIR"),
                        help="behave -f json 的報告，以及執行 behave 時的工作目錄（報告內的 feature 路徑相對於它），例如 tmp/api.json backend")
    parser.add_argument("--playwright", action="append", default=[], metavar="JSON",
                        help="Playwright --reporter=json 的報告（playwright-bdd 產生的測試檔必須仍在原處）")
    parser.add_argument("--vitest", nargs="+", action="append", default=[], metavar="JSON_OR_DIR",
                        help="vitest --reporter=json 的報告，後接一或多個該工具執行的端點資料夾，例如 tmp/vitest.json specs/truth/features/frontend/component；"
                        "有多份 vitest 報告（如原報告與單一 Example 的重跑報告）時必須重複整個選項，每份報告各接自己的資料夾："
                        "--vitest tmp/vitest.json specs/truth/features/frontend/component --vitest tmp/vitest-rerun.json specs/truth/features/frontend/component；"
                        "寫成 --vitest a.json b.json 時 b.json 會被當成 feature 資料夾")
    parser.add_argument("--expected-fail", nargs="+", action="extend", default=[], metavar="SCOPE",
                        help="這次預期失敗的 Example（如 red 範疇、因故意破壞產品程式或改寫既有 step 而失敗的 Example），格式同 resolve_scope.py 的範疇："
                        "端點資料夾、feature 路徑、feature 路徑:行號[:行號…] 或 feature 路徑 ＞ Rule「名稱」[、Rule「名稱」…]（含空白時整段以引號包成一個參數），"
                        "相對於 --root；列入者這次失敗時歸為開發中、不算回歸，並存為失敗")
    parser.add_argument("--partial", action="store_true",
                        help="部分執行：這次完全沒有報告的端點資料夾，其 Example 沿用上次結果（列為 carried，不算 not_run 也不算回歸）；"
                        "有報告的端點資料夾仍要求每個上次存在的 Example 都出現，否則列為 not_run。不傳時任何上次存在而這次沒有的 Example 都是 not_run")
    parser.add_argument("--ran-scope", nargs="+", action="extend", default=[], metavar="SCOPE",
                        help="Example 層級部分執行：本次實際執行的範疇（端點資料夾、feature 路徑、feature 路徑:行號[:行號…] 或 feature 路徑 ＞ Rule「名稱」[、Rule「名稱」…]，"
                        "含空白時整段以引號包成一個參數，相對於 --root，可多個），"
                        "只有範疇內缺報告的 Example 列為 not_run（報告缺漏或腳本崩潰會被抓到），範疇外沒有報告的 Example 沿用上次結果（列為 carried）；"
                        "範疇內有報告的 Example 照常比對與寫入。不可與 --partial 併用；不傳時行為不變")
    parser.add_argument("--result", default="specs/truth/features/.verify-result.json", help="這次 verify 結果的寫入位置，相對於 --root（預設 specs/truth/features/.verify-result.json）；未傳 --base 時也是比對的上次結果")
    parser.add_argument("--base", metavar="FILE",
                        help="以指定檔當比對基準（相對於 --root 或絕對路徑，格式同結果檔），預設為 --result 指定的檔案；用於回歸重跑時以原基準的備份重新比對")
    parser.add_argument("--dry-run", action="store_true",
                        help="只比對，不寫結果檔（specs/truth/features/.verify-result.json 維持原樣）；回歸重跑的判斷階段使用，確認後才不帶本選項寫入")
    parser.add_argument("--out", metavar="FILE",
                        help="把完整比對結果（含沿用、開發中等所有分組與逐項訊息）以 JSON 寫到這個檔案（相對於目前目錄）；stdout 預設只印摘要")
    parser.add_argument("--run", action="append", default=[], metavar="RUN_JSON",
                        help="run_suite.py 寫出的執行紀錄（stdout 的 run_record），可重複（如原執行與單一 Example 的重跑）；"
                        "寫入時以最後結束的那份為 last_run：本次有報告的 Example 記為它的代號，並要求目前的專案檔案清單摘要與它結束時相同"
                        "（之後改過任何檔案就拒絕寫入，必須重新執行）。不傳時結果檔不帶 last_run，下一個階段判定不可沿用")
    return parser.parse_args()


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    root = Path(args.root).resolve()
    if not args.behave and not args.playwright and not args.vitest:
        print(
            "錯誤：沒有傳入任何報告。請至少傳入一個 --behave、--playwright 或 --vitest。\n"
            "用法：uv run scripts/verify_result.py --behave tmp/api.json backend --playwright tmp/e2e.json",
            file=sys.stderr,
        )
        return 1
    if any(len(group) < 2 for group in args.vitest):
        print("錯誤：--vitest 後面必須接報告路徑與至少一個端點資料夾，例如 --vitest tmp/vitest.json specs/truth/features/frontend/component", file=sys.stderr)
        return 1
    if args.ran_scope and args.partial:
        print("錯誤：--ran-scope 與 --partial 不可併用。--partial 以端點資料夾為單位沿用；--ran-scope 以 Example 為單位沿用，請擇一。", file=sys.stderr)
        return 1
    index = FeatureIndex(root)
    entries: list[dict] = []
    unmapped: list[dict] = []
    unexecuted: list[dict] = []
    result_path = root / args.result
    shown_result = result_path.relative_to(root).as_posix() if result_path.is_relative_to(root) else result_path.as_posix()
    try:
        def tag(start: int, seq: int) -> None:
            for item in entries[start:]:
                item["seq"] = seq  # 報告傳入順序，後者覆蓋前者

        seq = 0
        for report, run_dir in args.behave:
            start = len(entries)
            read_behave(Path(report), Path(run_dir), index, entries, unmapped, unexecuted)
            tag(start, seq := seq + 1)
        for report in args.playwright:
            start = len(entries)
            read_playwright(Path(report), index, entries, unmapped, unexecuted)
            tag(start, seq := seq + 1)
        for report, *dirs in args.vitest:
            start = len(entries)
            read_vitest(Path(report), [Path(d) for d in dirs], index, entries, unmapped, unexecuted)
            tag(start, seq := seq + 1)
        base_path = (root / args.base) if args.base else result_path
        previous = load_previous(base_path)
        expected_fail = set(scope_records(args.expected_fail, index))
        ran_scope = scope_records(args.ran_scope, index, "--ran-scope") if args.ran_scope else None
        runs = [load_run(Path(path), root) for path in args.run]
    except ReportError as error:
        print(f"錯誤：{error}", file=sys.stderr)
        return 1
    current = aggregate(entries, index)
    groups, saved = compare(current, previous, index, expected_fail, args.partial, ran_scope)
    latest = max(runs, key=lambda run: run["finished_at"]) if runs else None
    last_run = None
    if latest is not None:
        last_run = {
            "run_id": latest["run_id"],
            "finished_at": latest["finished_at"],
            "snapshot": latest["snapshot"],
            "ran_scope": args.ran_scope or None,  # None：完整指令組或 --partial，本次有報告的 Example 都由這次執行產生
            "commands": [step["command"] for run in runs for step in run.get("steps", [])],
        }
    for record in saved:
        if record["key"] in current:
            # 本次有報告的 Example：一律記為最後結束的執行代號，失敗時存下訊息供下一個階段判定失敗原因類別
            record["run"] = last_run["run_id"] if last_run else None
            if current[record["key"]]["status"] == "failed":
                record["message"] = current[record["key"]]["message"]
            else:
                record.pop("message", None)
    if not args.dry_run:
        if latest is not None:
            now = project_snapshot(root)
            if now["digest"] != latest["snapshot"]["digest"]:
                hints = files_changed_after(root, latest["snapshot"]["taken_at_ns"])
                print(
                    f"錯誤：執行 {latest['run_id']} 結束後專案檔案有變動（檔案數 {latest['snapshot']['files']} → {now['files']}；"
                    f"較新的檔案：{hints or '無，可能是刪除'}），報告不是目前檔案狀態的結果，不得存回。"
                    "請重新以 run_suite.py 執行同一指令組後，以新的執行紀錄與報告存回。",
                    file=sys.stderr,
                )
                return 1
        result_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": RESULT_VERSION, **({"last_run": last_run} if last_run else {}), "examples": saved}
        result_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    endpoints: dict[str, dict] = {}
    for item in current.values():
        counts = endpoints.setdefault(item["endpoint_dir"], {"passed": 0, "failed": 0})
        counts[item["status"]] += 1
    summary = {
        "examples": len(current),
        "passed": sum(1 for item in current.values() if item["status"] == "passed"),
        "failed": sum(1 for item in current.values() if item["status"] == "failed"),
        **{name: len(items) for name, items in groups.items()},
        "expected_fail": sum(1 for item in groups["in_progress"] if item.get("expected_fail")),
        "unmapped": len(unmapped),
        "unexecuted_items": len(unexecuted),
    }
    where = "（--dry-run，未寫結果檔）" if args.dry_run else f"；結果已存到 {shown_result}"
    print(
        f"共 {summary['examples']} 個 Example：通過 {summary['passed']}、失敗 {summary['failed']}；"
        f"回歸 {summary['regressions']}、開發中 {summary['in_progress']}（預期失敗 {summary['expected_fail']}）、無基準失敗 {summary['no_baseline_failures']}、"
        f"未執行 {summary['not_run']}、沿用上次 {summary['carried']}、無法對應 {summary['unmapped']}{where}",
        file=sys.stderr,
    )
    full = {
        "result_file": None if args.dry_run else shown_result,
        "base_file": base_path.relative_to(root).as_posix() if base_path.is_relative_to(root) else base_path.as_posix(),
        "dry_run": args.dry_run,
        "has_baseline": previous is not None,
        "ran_scope_examples": None if ran_scope is None else len(ran_scope),
        "last_run": None if last_run is None else last_run["run_id"],
        "summary": summary,
        "endpoints": dict(sorted(endpoints.items())),
        **groups,
        "unmapped": unmapped,
        "unexecuted_items": unexecuted,
    }
    # stdout 只印摘要：各分組數量、需要人處理或審閱的清單與各端點數量；沿用、開發中、已修好等大型分組只印數量，完整內容用 --out 寫檔
    listed = ("regressions", "not_run", "removed")
    digest = {
        "result_file": full["result_file"],
        "base_file": full["base_file"],
        "dry_run": args.dry_run,
        "has_baseline": full["has_baseline"],
        "ran_scope_examples": full["ran_scope_examples"],
        "last_run": full["last_run"],
        "full_report": Path(args.out).as_posix() if args.out else None,
        "summary": summary,
        "endpoints": full["endpoints"],
        **{name: full[name] for name in listed},
        "unmapped": unmapped,
    }
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(full, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(digest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
