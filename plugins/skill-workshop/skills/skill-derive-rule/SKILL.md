---
name: skill-derive-rule
description: 給定一個已寫好 SOP 的 skill，針對其中某個步驟展開該步驟需要遵守的規範並產出 RuleFile。從已寫好的 Rule 抽出它對照的基準交由 skill-derive-baseline。
---

## SOP

### Phase 1 --- 判斷需求

1. READ 讀取目標 skill 的 SKILL.md 與使用者指定的 Phase 或 Step。
2. ASK 未指定步驟或範圍不明時詢問使用者。
3. THINK 依 [規範邊界判斷](rules/規範邊界判斷.md) 判斷指定步驟需寫入 RuleFile 的規範項目。

### Phase 2 --- 撰寫 RuleFile

1. WRITE 依 [skill-form-rule](../skill-form-rule/SKILL.md) 於目標 skill 的 `rules/` 撰寫 RuleFile。

### Phase 3 --- 回寫 SOP

1. WRITE 依 [SOP 檔案掛載規範](../skill-form-sop/rules/sop-檔案掛載規範.md) 在指定 SOP Step 加入對應 RuleFile 的連結引用。

### Phase 4 --- 建議基準

1. WRITE 有 Rule 的對照資料是型錄時在回覆中建議以 skill-derive-baseline 抽出基準。
