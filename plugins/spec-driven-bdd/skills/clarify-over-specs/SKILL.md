---
name: clarify-over-specs
description: 使用者已有 specify 產出的功能規格書（spec.md），要在技術研究前主動找出規格盲點、與使用者澄清並寫回 spec.md，或 plan 進行中使用者或 PM 要修改需求，或 dev-finding、spec-by-example 交辦改寫 spec.md 的需求，或呼叫 /clarify-over-specs 時使用此 skill。從功能描述產出 spec.md 交由 specify，問題撰寫與問答互動交由 clarify，驗收 feature 的改寫交由 spec-by-example，plan 的狀態檢查與記錄交由 plan-package，技術選型交由 technical-research。
---

## SOP

### Phase 1 --- 掃描覆蓋缺口

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
2. READ 讀取這個 plan 的 spec.md、使用者或 PM 這次提出的需求變更或交辦修正的需求（連同交辦引用的 AC 原文），以及 `specs/truth/features/用語表.md` 的「模組」表。
3. ASK spec.md 不存在時（例如技術修正 plan），回報需求的修改要以 /specify 開立有需求的 plan 處理，不記錄並停止。
4. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 spec.md 適用的憲法條款。
5. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 在只為修改需求而執行（使用者或 PM 提出需求變更，或被交辦修正指定的需求）時，以這些變更為這次的差異，對 spec.md 中涉及它們的每個章節判斷連帶異動或不受影響，只把變更與連帶異動的章節列為這次的範圍；要找出規格盲點時以 spec.md 全文為範圍。
6. THINK 依 [需求覆蓋分類法](rules/需求覆蓋分類法.md) 在這次的範圍內為每個分類判定 Clear、Partial 或 Missing，建立覆蓋地圖。
7. THINK 依 [缺口影響力判準](rules/缺口影響力判準.md) 從 Partial 與 Missing 的分類挑出值得提問的面向，為每個面向標上所屬分類與狀態，並依影響力排序。

### Phase 2 --- 委派一輪訪談

1. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）在有值得提問的面向時，以排序後的面向、以「分類（狀態）」作為各面向的題目標籤、每輪至多 5 題、只問一輪的設定訪談使用者，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。

### Phase 3 --- 寫回規格

1. DELEGATE 依 [check_spec.py](../specify/scripts/check_spec.py) 與 [腳本執行規範](../specify/rules/script-執行規範.md) 在本輪答案或需求變更需要新增 FR、NFR、SC 或使用者故事時取得新的編號。
2. WRITE 依 [釐清結果寫回規範](rules/釐清結果寫回規範.md) 與 [使用者故事切分規範](../specify/rules/使用者故事切分規範.md) 與 [規格內容撰寫規範](../specify/rules/規格內容撰寫規範.md) 與 [需求推導規範](../specify/rules/需求推導規範.md) 與憲法條款把本輪問答與這次的需求變更寫進 spec.md 的釐清紀錄與對應章節。
3. THINK 依 [釐清結果寫回規範](rules/釐清結果寫回規範.md) 逐條核對本輪每個答案與需求變更都已寫入對應章節，沒有殘留被推翻的內容、已確認的預設值或舊用語，且先前的釐清紀錄沒有被改動。
4. DELEGATE 依 [check_spec.py](../specify/scripts/check_spec.py) 與 [腳本執行規範](../specify/rules/script-執行規範.md) 檢查 spec.md 的表頭、受影響的既有功能、編號不重複、交叉引用與殘留佔位符。
5. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 spec.md 是否符合憲法條款，並判斷腳本回報的問題是否與條款衝突。
6. WRITE 修正核對與檢查發現的問題。

### Phase 4 --- 回報覆蓋並記錄

1. THINK 依 [需求覆蓋分類法](rules/需求覆蓋分類法.md) 與 [缺口影響力判準](rules/缺口影響力判準.md) 重新判定這次範圍的覆蓋地圖，並挑出剩餘的高影響缺口。
2. ASK 仍有高影響缺口時，列出這些缺口與是否推薦再問一輪；使用者選擇繼續時回到 Phase 2。
3. WRITE 依 [缺口影響力判準](rules/缺口影響力判準.md) 與 [覆蓋總表.md](templates/覆蓋總表.md) 與 [覆蓋總表.example.md](templates/覆蓋總表.example.md) 輸出覆蓋總表與下一步建議。
4. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
5. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
