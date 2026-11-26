# 腳本執行規範

## Rule 1 -- 必須以 uv run 執行腳本

**強度：MUST**

執行 skill 的 `scripts/` 底下的 Python 腳本時，一律使用 `uv run <腳本路徑>`，不得使用 `python`、`python3` 或 `py` 直接執行。

### Good Example

這個範例以 `uv run` 執行，uv 會依腳本的 PEP 723 宣告自動安裝依賴。

```bash
uv run "D:/work/report/.claude/skills/skill-pdf-form/scripts/extract_fields.py" form.pdf
```

### Bad Example

這個範例以 `python` 直接執行，腳本宣告的 `pypdf` 不會被安裝，執行時出現 `ModuleNotFoundError`。

```bash
python "D:/work/report/.claude/skills/skill-pdf-form/scripts/extract_fields.py" form.pdf
```

## Rule 2 -- 未安裝 uv 時必須先詢問使用者

**強度：MUST**

找不到 `uv` 指令時，必須先詢問使用者是否以 `python -m pip install uv` 安裝。使用者同意後才安裝，並改以 `python -m uv run <腳本路徑>` 執行；使用者拒絕時停止執行該 Step，並說明腳本需要 uv 才能執行。呼叫者標明不可詢問時（例如在 sub-agent 中執行），視同使用者拒絕：不得自行安裝，改依該 Step 所屬規範的退路處理（例如退回讀程式碼並寫明未實測），沒有退路時停止並回報。

### Good Example

這個範例在找不到 uv 時先詢問，取得同意後才安裝並執行。

```text
找不到 uv 指令。這個步驟的腳本需要 uv 才能安裝依賴並執行。
是否同意以 `python -m pip install uv` 安裝 uv？

（使用者同意）

python -m pip install uv
python -m uv run "D:/work/report/.claude/skills/skill-pdf-form/scripts/extract_fields.py" form.pdf
```

### Bad Example

這個範例未經詢問就直接安裝 uv，在使用者不知情的情況下改動了使用者的 Python 環境。

```text
找不到 uv 指令，自動安裝中。

python -m pip install uv
python -m uv run "D:/work/report/.claude/skills/skill-pdf-form/scripts/extract_fields.py" form.pdf
```

## Rule 3 -- 必須在專案根目錄執行

**強度：MUST**

腳本一律在專案根目錄執行。腳本的路徑參數（例如 `specs`、`specs/plans/004-ranking`）以專案根目錄為基準。

### Good Example

這個範例在專案根目錄執行，參數 `specs` 從專案根目錄出發。

```bash
uv run "D:/work/report/.claude/skills/plan-package/scripts/plan_state.py" check specs --plan 004-ranking
```

### Bad Example

這個範例先切換到 skill 的目錄再執行，參數 `specs` 被解析成 `plan-package/specs`，腳本回報找不到 specs 資料夾。

```bash
cd "D:/work/report/.claude/skills/plan-package"
uv run "D:/work/report/.claude/skills/plan-package/scripts/plan_state.py" check specs --plan 004-ranking
```

## Rule 4 -- 腳本路徑必須取自 skill 實際位置

**強度：MUST**

SKILL.md 掛載的腳本連結（例如 `scripts/plan_state.py`）相對於該 skill 的目錄。執行時必須寫成該 SKILL.md 實際所在目錄底下的絕對路徑，並以雙引號包住；不得假設 skill 位於 `.claude/skills/` 或其他固定目錄，因為 skill 可能安裝在專案內，也可能由 plugin 安裝在專案外。以下 Example 的 SKILL.md 位於 `D:/plugins/skill-workshop/skills/plan-package/SKILL.md`，專案根目錄為 `D:/work/report`。

### Good Example

這個範例以 SKILL.md 實際所在目錄組成絕對路徑，skill 裝在專案外也能找到腳本。

```bash
uv run "D:/plugins/skill-workshop/skills/plan-package/scripts/plan_state.py" check specs --plan 004-ranking
```

### Bad Example

這個範例假設 skill 位於專案的 `.claude/skills/`，實際上由 plugin 安裝在專案外，執行時找不到腳本。

```bash
uv run .claude/skills/plan-package/scripts/plan_state.py check specs --plan 004-ranking
```
