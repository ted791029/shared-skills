---
name: skill-form-script
description: 撰寫、新增或修改任何 skill 的 `scripts/` 底下時，必須使用此 skill；即使同時在使用其他 skill 也適用。
---

## SOP

### Phase 1 --- 判斷需求

1. READ 讀取使用者需求與目標腳本。
2. THINK 判斷腳本的輸入、輸出與第三方依賴。
3. ASK 需求不明時詢問使用者。

### Phase 2 --- 撰寫腳本

1. WRITE 依 [script.py](templates/script.py) 與 [script.example.py](templates/script.example.py) 建立腳本的 PEP 723 區塊與程式進入點結構。
2. WRITE 依 [腳本依賴宣告規範](rules/script-依賴宣告規範.md) 填寫 Python 版本與第三方依賴。
3. WRITE 依 [腳本介面規範](rules/script-介面規範.md) 撰寫命令列參數、輸出與錯誤處理。
4. WRITE 依 [腳本跨平台規範](rules/script-跨平台規範.md) 撰寫腳本主要邏輯。

### Phase 3 --- 驗證腳本

1. DELEGATE 依 [腳本執行規範](rules/script-執行規範.md) 執行腳本的 `--help` 與一組代表性輸入。
2. WRITE 修正執行失敗的問題。
