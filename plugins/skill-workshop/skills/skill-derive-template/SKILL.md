---
name: skill-derive-template
description: 給定一個已寫好 SOP 的 skill，針對其中約束產出格式的步驟抽出樣板（骨架與範例），並連動調整既有 RuleFile。
---

## SOP

### Phase 1 --- 判斷需求

1. READ 讀取目標 skill 的 SKILL.md 與使用者指定的 Phase 或 Step。
2. ASK 未指定步驟或範圍不明時詢問使用者。
3. THINK 依 [樣板邊界判斷](rules/樣板邊界判斷.md) 判斷指定步驟中應抽成樣板的格式內容。

### Phase 2 --- 撰寫樣板

1. WRITE 依 [skill-form-template](../skill-form-template/SKILL.md) 於目標 skill 的 `templates/` 撰寫骨架與範例。

### Phase 3 --- 連動調整

1. WRITE 依 [skill-form-rule](../skill-form-rule/SKILL.md) 與 [規則連動調整](rules/規則連動調整.md) 刪改指定 Step 已掛載 RuleFile 中已由樣板涵蓋的 Rule。
2. WRITE 依 [SOP 檔案掛載規範](../skill-form-sop/rules/sop-檔案掛載規範.md) 在指定 Step 加入骨架與範例兩份檔案的連結引用。
