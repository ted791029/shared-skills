---
name: skill-engineering
description: 建立新 skill 或優化、修正既有 skill（包含使用者對某個 skill 的產出不滿意）時使用此 skill。先以終為始釐清預期，優化時做根因分析並經使用者確認，再以 skill-form-sop 推導主幹並編排 skill-derive-* 衍生 rules、templates、scripts；每個 Step 由閘門腳本逐步給出並記錄，跳過須經使用者同意，結束時回報執行狀態表。以 Artifact 範例出發建立 skill 時先交由 artifact-to-skill-engineering 抽出樣板。
---

## SOP

### Phase 1 --- 釐清預期

1. DELEGATE 依 [sop_gate.py](scripts/sop_gate.py) 與 [SOP 閘門規範](rules/sop-閘門規範.md) 與 [腳本執行規範](rules/script-執行規範.md) 建立執行紀錄。
2. READ 讀取使用者需求與目標 skill。
3. THINK 判斷為新建或優化。
4. THINK 依 [預期定義規範](rules/預期定義規範.md) 以終為始寫出使用者預期的產出。
5. ASK 請使用者確認模式與預期。

### Phase 2 --- 診斷落差（僅優化）

1. THINK 依 [根因分析規範](rules/根因分析規範.md) 與 [重構取捨規範](rules/重構取捨規範.md) 沿呼叫鏈演練 SOP 找出第一個偏離點、根因與修改方向。
2. DELEGATE 依 [根因分析規範](rules/根因分析規範.md) 在符合驗證條件時委派子 agent 盲測反事實檢驗。
3. WRITE 依 [落差分析報告.md](templates/落差分析報告.md) 與 [落差分析報告.example.md](templates/落差分析報告.example.md) 撰寫落差分析報告。
4. ASK 請使用者確認根因，使用者否定或質疑時回到 Step 1 重新演練。
5. ASK 目標 skill 有未 commit 的變更時請使用者先 commit。

### Phase 3 --- 推導主幹

1. DELEGATE 依 [skill-form-sop](../skill-form-sop/SKILL.md) 與 [零基推導規範](rules/零基推導規範.md) 從確認後的預期推導目標 SOP。
2. WRITE 依 [description 撰寫規範](rules/description-撰寫規範.md) 撰寫目標 skill 的 name 與 description。
3. THINK 依 [重構取捨規範](rules/重構取捨規範.md) 判定既有部件的存留。

### Phase 4 --- 編排衍生

1. THINK 依 [編排判斷規範](rules/編排判斷規範.md) 為每個 Step 決定 deriver 與執行順序。
2. ASK 依 [編排判斷規範](rules/編排判斷規範.md) 請使用者確認編排提案與刪除清單。
3. WRITE 刪除判定不存留的部件。
4. WRITE 依 [SOP 檔案掛載規範](../skill-form-sop/rules/sop-檔案掛載規範.md) 刪除所有 skill 中指向已刪除部件的掛載連結。
5. DELEGATE 依 [skill-derive-script](../skill-derive-script/SKILL.md) 為編排提案中指派的 Step 抽出腳本。
6. DELEGATE 依 [skill-derive-rule](../skill-derive-rule/SKILL.md) 為編排提案中指派的 Step 展開規則。
7. DELEGATE 依 [skill-derive-template](../skill-derive-template/SKILL.md) 為編排提案中指派的 Step 抽出樣板。

### Phase 5 --- 驗證

1. DELEGATE 依 [skill_graph.py](scripts/skill_graph.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查所有 skill 的失效連結與目標 skill 的孤兒檔案。
2. THINK 以預期中的每個演練情境演練新 SOP 確認產出符合預期。
3. WRITE 依 [sop_gate.py](scripts/sop_gate.py) 回報新增、修改、刪除的部件、驗證結果與執行狀態表。
