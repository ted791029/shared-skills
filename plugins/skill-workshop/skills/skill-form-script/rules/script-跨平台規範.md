# 腳本跨平台規範

## Rule 1 -- 路徑必須使用 pathlib

**強度：MUST**

組合與操作路徑必須使用 `pathlib.Path`，不得以字串手動串接 `/` 或 `\\`。

### Good Example

這個範例以 `Path` 的 `/` 運算子組合路徑，由 pathlib 處理各平台的分隔符號。

```python
output_path = Path(args.output_dir) / "fields.json"
```

### Bad Example

這個範例以字串串接反斜線，在 Mac 與 Linux 上會產生名稱含 `\` 的錯誤路徑。

```python
output_path = args.output_dir + "\\fields.json"
```

## Rule 2 -- 附帶資源必須以腳本位置定位

**強度：MUST**

腳本讀取 skill 內附帶的檔案時，必須以 `Path(__file__).resolve().parent` 為基準定位，不得依賴目前工作目錄。使用者提供的路徑則透過參數傳入。

### Good Example

這個範例以腳本所在目錄定位附帶的對照表，不論從哪個目錄執行都能找到。

```python
SCRIPT_DIR = Path(__file__).resolve().parent
field_map = json.loads((SCRIPT_DIR / "field_map.json").read_text(encoding="utf-8"))
```

### Bad Example

這個範例以相對於工作目錄的路徑讀取附帶檔案，agent 從專案根目錄執行時會找不到檔案。

```python
field_map = json.loads(Path("scripts/field_map.json").read_text(encoding="utf-8"))
```

## Rule 3 -- 文字讀寫必須指定 UTF-8

**強度：MUST**

讀寫文字檔時（如 `open()`、`read_text()`、`write_text()`）必須明確指定 `encoding="utf-8"`。

### Good Example

這個範例讀寫檔案時都明確指定編碼。

```python
content = Path(args.rule_file).read_text(encoding="utf-8")
Path(args.output).write_text(content, encoding="utf-8")
```

### Bad Example

這個範例沒有指定編碼，在繁中 Windows 上預設為 cp950，讀取 UTF-8 中文檔時會出現 `UnicodeDecodeError`。

```python
content = Path(args.rule_file).read_text()
```

## Rule 4 -- 不得呼叫作業系統特有指令

**強度：MUST**

不得透過 `subprocess` 或 `os.system` 呼叫 `cp`、`rm`、`ls`、`grep`、`dir`、`copy` 等作業系統特有指令，必須改用 `shutil`、`pathlib` 等標準函式庫完成。

### Good Example

這個範例以 `shutil` 複製檔案，各平台行為一致。

```python
shutil.copy2(source_path, target_path)
```

### Bad Example

這個範例呼叫 `cp` 指令，Windows 上沒有 `cp`，腳本會直接失敗。

```python
subprocess.run(["cp", str(source_path), str(target_path)], check=True)
```
