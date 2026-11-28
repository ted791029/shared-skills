---
name: skill-form-baseline
description: 撰寫、新增或修改任何 skill 的 `rules/baselines/` 底下的基準檔時，必須使用此 skill；即使同時在使用其他 skill 也適用。`rules/` 底下的 RuleFile 交由 skill-form-rule。
---

## SOP

### Phase 1 --- 判斷需求

1. READ 讀取使用者需求、目標基準與來源材料。
2. THINK 依 [基準內容邊界規範](rules/baseline-內容邊界規範.md) 判斷來源材料中屬於對照資料的內容。
3. ASK 需求不明或缺少來源材料時詢問使用者。

### Phase 2 --- 撰寫基準

1. WRITE 基準為 Markdown 時依 [基準格式規範](rules/baseline-格式規範.md) 與 [baseline.md](templates/baseline.md) 與 [baseline.example.md](templates/baseline.example.md) 撰寫檔頭與條目。
2. WRITE 基準不是 Markdown 時依 [基準來源標示規範](rules/baseline-來源標示規範.md) 標示來源。

### Phase 3 --- 核對

1. WRITE 依 [基準內容邊界規範](rules/baseline-內容邊界規範.md) 逐條目對照來源材料修正與來源不同的內容。
2. WRITE 回報判定不屬於對照資料的要求與判斷。
