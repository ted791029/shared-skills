# 腳本依賴宣告規範

## Rule 1 -- 無依賴時必須保留空清單

**強度：MUST**

沒有第三方依賴時，PEP 723 區塊仍必須保留 `dependencies` 欄位，寫成 `dependencies = []`，不得刪除該欄位。

### Good Example

這個範例沒有第三方依賴，仍保留空的 `dependencies` 欄位。

```python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
```

### Bad Example

這個範例因為沒有依賴就刪掉 `dependencies` 欄位，不符合 PEP 723 要求該欄位必須存在的規定，日後要加入依賴時也看不出該寫在哪裡。

```python
# /// script
# requires-python = ">=3.10"
# ///
```

## Rule 2 -- 不得另建依賴管理檔

**強度：MUST**

依賴只能宣告在腳本自身的 PEP 723 區塊，不得在 skill 內另建 `requirements.txt`、`pyproject.toml`、`setup.py` 或虛擬環境目錄。

### Good Example

這個範例的 `scripts/` 只有腳本本身，依賴都在各腳本的 PEP 723 區塊。

```text
skill-pdf-form/
├── SKILL.md
└── scripts/
    ├── extract_fields.py
    └── fill_form.py
```

### Bad Example

這個範例另建 `requirements.txt` 與 `.venv/`，依賴同時存在兩處，修改其中一處時容易不同步，`.venv/` 也無法跨平台共用。

```text
skill-pdf-form/
├── SKILL.md
└── scripts/
    ├── requirements.txt
    ├── .venv/
    ├── extract_fields.py
    └── fill_form.py
```

## Rule 3 -- 優先使用標準函式庫

**強度：SHOULD**

標準函式庫能完成的功能，應使用標準函式庫，不加入第三方套件。只有標準函式庫無法完成，或實作成本明顯過高時，才加入第三方依賴。

### Good Example

這個範例讀取 CSV 與輸出 JSON 都使用標準函式庫，沒有第三方依賴。

```python
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
import csv
import json
```

### Bad Example

這個範例只為讀取 CSV 就加入 `pandas`，首次執行需下載數十 MB 的套件，拖慢執行並增加網路受限時安裝失敗的機會。

```python
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pandas>=2.2,<3",
# ]
# ///
import json

import pandas as pd
```

## Rule 4 -- 依賴版本必須限定範圍

**強度：MUST**

每個第三方依賴都必須寫成 `>=<已驗證版本>,<<下一個主版本>` 的範圍，不得只寫套件名稱，也不得以 `==` 釘死單一版本。

### Good Example

這個範例限定在已驗證版本以上、下一個主版本以下。

```python
# dependencies = [
#   "pypdf>=4.2,<5",
# ]
```

### Bad Example

這個範例只寫套件名稱，套件發布不相容的新主版本後，腳本會在沒有任何修改的情況下突然失效。

```python
# dependencies = [
#   "pypdf",
# ]
```

## Rule 5 -- requires-python 必須寫最低需求

**強度：MUST**

`requires-python` 只能寫成 `>=3.X` 的下限，預設為 `>=3.10`。只有腳本用到更新版本才有的語法或標準函式庫時，才提高下限，且不得設定上限。

### Good Example

這個範例使用預設下限，沒有設定上限。

```python
# requires-python = ">=3.10"
```

### Bad Example

這個範例釘死單一版本，使用者機器上沒有 3.12.4 時，uv 必須額外下載該版 Python，離線環境則直接無法執行。

```python
# requires-python = "==3.12.4"
```
