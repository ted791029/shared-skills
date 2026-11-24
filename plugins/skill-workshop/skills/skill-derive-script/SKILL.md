---
name: skill-derive-script
description: 給定一個已寫好 SOP 的 skill，針對其中某個步驟抽出可交給 Python 腳本執行的動作並產出腳本，再將該步驟改為委派腳本。
---

## SOP

### Phase 1 --- 判斷需求

1. READ 讀取目標 skill 的 SKILL.md 與使用者指定的 Phase 或 Step。
2. ASK 未指定步驟或範圍不明時詢問使用者。
3. THINK 依 [腳本邊界判斷](rules/腳本邊界判斷.md) 判斷指定步驟中可交給腳本執行的動作。

### Phase 2 --- 撰寫腳本

1. WRITE 依 [skill-form-script](../skill-form-script/SKILL.md) 於目標 skill 的 `scripts/` 撰寫腳本。
2. WRITE 將 [腳本執行規範](../skill-form-script/rules/script-執行規範.md) 複製到目標 skill 的 `rules/`，已存在時以原版覆蓋。

### Phase 3 --- 回寫 SOP

1. WRITE 依 [SOP 檔案掛載規範](../skill-form-sop/rules/sop-檔案掛載規範.md) 與 [腳本掛載規範](rules/腳本掛載規範.md) 將指定 Step 改為以 `DELEGATE` 委派腳本並加入連結。
