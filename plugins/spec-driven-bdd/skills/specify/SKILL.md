---
name: specify
description: 使用者要把一段功能描述轉成功能規格書（spec.md），或呼叫 /specify 時使用此 skill。plan 的開立、狀態與交付交由 plan-package，需求訪談交由 clarify，規格盲點的掃描與需求變更交由 clarify-over-specs，技術規劃與任務拆解不在範圍內。
---

## SOP

### Phase 1 --- 開立 plan

1. READ 讀取使用者的功能描述。
2. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 open 與取自功能描述的英文短名開立新的 plan，被拒絕時停止。

### Phase 2 --- 釐清需求

1. READ 讀取 `specs/truth/features/用語表.md` 的「模組」表，取得既有功能的名稱與範圍。
2. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）在功能描述存在會改變使用者故事範圍或驗收結果的缺口時，以詳記問答紀錄的方式釐清缺口，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。

### Phase 3 --- 撰寫規格

1. THINK 依 [使用者故事切分規範](rules/使用者故事切分規範.md) 從功能描述與釐清結果切分使用者故事並排定優先順序。
2. THINK 依 [需求推導規範](rules/需求推導規範.md) 從每個使用者故事的驗收情境與釐清結果推導 FR、NFR，並判定各條需求屬於單一故事或全域。
3. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 spec.md 適用的憲法條款。
4. WRITE 依 [規格內容撰寫規範](rules/規格內容撰寫規範.md) 與憲法條款與 [spec.md](templates/spec.md) 與 [spec.example.md](templates/spec.example.md) 撰寫 plan 資料夾的 spec.md。

### Phase 4 --- 檢查一致性

1. DELEGATE 依 [check_spec.py](scripts/check_spec.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查 spec.md 的表頭、受影響的既有功能、編號不重複、交叉引用與殘留佔位符。
2. THINK 檢查每個釐清答案是否都已落入需求。
3. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 spec.md 是否符合憲法條款，並判斷腳本回報的問題是否與條款衝突。
4. WRITE 修正檢查與核對發現的問題。

### Phase 5 --- 回報

1. WRITE 在對話中列出這個 plan 的使用者故事、FR、NFR 的條數與受影響的既有功能的項數。
2. WRITE 建議使用者可選擇執行 [clarify-over-specs](../clarify-over-specs/SKILL.md) 澄清規格盲點。
3. WRITE 建議使用者可選擇執行 [spec-by-example](../spec-by-example/SKILL.md) 以 Gherkin 定義驗收標準。
