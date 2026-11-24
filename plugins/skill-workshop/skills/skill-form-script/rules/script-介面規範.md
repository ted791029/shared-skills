# 腳本介面規範

## Rule 1 -- 不得等待互動輸入

**強度：MUST**

所有輸入只能透過命令列參數、環境變數或 stdin 提供，不得使用 `input()`、`getpass()` 或任何確認提示。缺少必要輸入時，必須直接以錯誤訊息結束。

### Good Example

這個範例以必填參數取得輸入，缺少時由 argparse 直接報錯結束。

```python
parser = argparse.ArgumentParser(description="擷取 PDF 表單欄位。")
parser.add_argument("pdf_path", help="要擷取的 PDF 檔案路徑")
args = parser.parse_args()
```

### Bad Example

這個範例在執行中等待使用者輸入，agent 的 shell 無法回應互動提示，腳本會一直卡住直到逾時。

```python
pdf_path = input("請輸入 PDF 檔案路徑：")
```

## Rule 2 -- 資料與診斷必須分流

**強度：MUST**

結果資料只能輸出到 stdout；進度、警告與錯誤訊息必須輸出到 stderr。

### Good Example

這個範例把進度寫到 stderr，stdout 只有結果資料。

```python
print(f"讀取 {len(files)} 份 RuleFile", file=sys.stderr)
print(json.dumps(result, ensure_ascii=False))
```

### Bad Example

這個範例把進度訊息也寫到 stdout，agent 解析 stdout 的 JSON 時會因開頭多出一行文字而失敗。

```python
print(f"讀取 {len(files)} 份 RuleFile")
print(json.dumps(result, ensure_ascii=False))
```

## Rule 3 -- 結果資料應使用 JSON

**強度：SHOULD**

輸出到 stdout 的結果資料應使用 JSON，並以 `ensure_ascii=False` 保留中文。結果只是單一路徑或單一數值時，可以直接輸出純文字。

### Good Example

這個範例以 JSON 輸出結構化結果，中文保持可讀。

```python
print(json.dumps({"file": "sop-格式規範.md", "rule_count": 7}, ensure_ascii=False))
```

### Bad Example

這個範例以空白對齊的表格輸出，欄位值含空白時邊界不明，agent 難以可靠解析。

```python
print(f"{'file':<20}{'rule_count':>10}")
print(f"{'sop-格式規範.md':<20}{7:>10}")
```

## Rule 4 -- 錯誤訊息必須說明修正方式

**強度：MUST**

錯誤訊息必須寫出哪裡錯、預期的值或狀態，以及該怎麼修正，不得只輸出籠統的錯誤或原始 traceback。

### Good Example

這個範例說明收到的值、可接受的值與正確用法，agent 可以直接修正指令。

```python
print(
    f"錯誤：--format 只接受 json、csv，收到 {args.format}。\n"
    "用法：uv run scripts/count_rules.py rules --format json",
    file=sys.stderr,
)
```

### Bad Example

這個範例只說輸入無效，agent 不知道錯在哪個參數，只能反覆嘗試，浪費多輪呼叫。

```python
print("Error: invalid input", file=sys.stderr)
```

## Rule 5 -- 失敗必須以非零 exit code 結束

**強度：MUST**

腳本成功時以 exit code `0` 結束；任何失敗都必須以非零 exit code 結束，不得印出錯誤後仍回傳 `0`。

### Good Example

這個範例在找不到目錄時印出錯誤並回傳 `1`。

```python
if not rules_dir.is_dir():
    print(f"錯誤：找不到目錄 {rules_dir}，請確認路徑。", file=sys.stderr)
    return 1
```

### Bad Example

這個範例印出錯誤後正常結束，exit code 為 `0`，agent 會誤判腳本執行成功並繼續下一步。

```python
if not rules_dir.is_dir():
    print(f"錯誤：找不到目錄 {rules_dir}，請確認路徑。", file=sys.stderr)
    return 0
```
