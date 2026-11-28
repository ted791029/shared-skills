---
name: skill-derive-baseline
description: 給定一個已寫好 RuleFile 的 skill，要把其中某條 Rule 對照的型錄（條目清單、句型、外部來源的原文）抽成基準，或 skill-derive-rule 委派抽出基準時使用此 skill。從 SOP 的 Step 展開 RuleFile 交由 skill-derive-rule，只撰寫基準檔交由 skill-form-baseline。
---

## SOP

### Phase 1 --- 判斷需求

1. READ 讀取目標 skill 的 SKILL.md、RuleFile 與使用者指定的 Rule。
2. ASK 未指定 Rule 或範圍不明時詢問使用者。
3. THINK 依 [基準邊界判斷](rules/基準邊界判斷.md) 判斷指定 Rule 中應抽成基準的對照資料與其來源。
4. ASK 對照資料不在 Rule 與使用者提供的材料中時請使用者提供。

### Phase 2 --- 撰寫基準

1. WRITE 依 [skill-form-baseline](../skill-form-baseline/SKILL.md) 於目標 skill 的 `rules/baselines/` 撰寫基準。

### Phase 3 --- 連動調整

1. WRITE 依 [skill-form-rule](../skill-form-rule/SKILL.md) 與 [基準連動調整](rules/基準連動調整.md) 改寫指定 Rule，移除已抽出的資料並宣告基準。
2. WRITE 依 [SOP 檔案掛載規範](../skill-form-sop/rules/sop-檔案掛載規範.md) 在掛載該 RuleFile 的 Step 加入基準的連結引用。
