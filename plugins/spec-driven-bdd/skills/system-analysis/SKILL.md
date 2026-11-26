---
name: system-analysis
description: 使用者已有功能規格書（spec.md）與技術研究產物（research.md、techstack.md），要規劃系統分析、產出實作計畫（plan.md）並依分析 Wave 產出各端點的介面文檔，或 plan-package 列出 system-analysis 或 Planner 待補跑、Planner 回報 plan.md 的上游問題、implement 交辦修正 plan.md 的原始碼段，或呼叫 /system-analysis 時使用此 skill。功能規格交由 specify，技術研究交由 technical-research，各端點介面文檔的撰寫交由各 Planner，Planner 的配對與建立交由 planner-provisioning，plan 的狀態檢查與記錄交由 plan-package，開發發現與技術項交由 dev-finding，任務拆解交由 task。
---

## SOP

### Phase 1 --- 讀取輸入

1. READ 讀取呼叫者指定的入口與交辦內容：原始碼段入口帶入的原始碼段以外的產品檔，或依差異時轉交的上游問題與要重跑的端點。
2. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
3. READ 讀取這個 plan 的 spec.md、`features/acceptance/`、research.md、已有的 `技術項.md`、plan.md 與 wave-report.md，以及 `specs/truth/techstack.md`。
4. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 query 取得上游已記錄的 truth 異動。
5. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 與 [依差異範圍規範](rules/依差異範圍規範.md) 判定這次是完整流程或依差異；依差異時對每個差異判斷 plan.md 的介面列、Wave 與原始碼段是連帶異動或不受影響，只把連帶異動與要重跑的端點列為這次的範圍。
6. READ 讀取 `specs/truth/` 中範圍內的需求、「受影響的既有功能」與端點涉及的既有介面文檔與 feature。
7. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）在輸入存在會改變端點、介面或 Wave 劃分的疑慮時釐清缺口，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。

### Phase 2 --- 規劃實作計畫

1. THINK 依 [介面盤點規範](rules/介面盤點規範.md) 從 spec.md、涵蓋需求的 AC 與既有的介面文檔盤點範圍內涉及的端點、每個端點的對外介面、各介面依據的需求與這次的異動。
2. THINK 依 [分析 Wave 規劃規範](rules/分析Wave規劃規範.md) 由外而內依相依性將範圍內的端點分成 Wave，並決定每個 Wave 的分析重點、前置 Wave 端點的相依與每個端點的 sub-agent 委派。
3. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 plan.md 適用的憲法條款。
4. WRITE 依憲法條款與 [專案結構規劃規範](rules/專案結構規劃規範.md) 與 [plan.md](templates/plan.md) 與 [plan.example.md](templates/plan.example.md) 撰寫 plan 資料夾的 plan.md，依差異時只改範圍內的介面列、Wave、原始碼段與結構決策。
5. DELEGATE 依 [check_plan.py](scripts/check_plan.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查 plan.md 的介面 ID、異動、依據需求、Wave 分配、委派、相依與統計數字是否一致，以及殘留佔位符。
6. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 plan.md 是否符合憲法條款，並判斷腳本回報的問題是否與條款衝突；plan.md 被條款或上游事實擋住而不能改時，不執行 Phase 3 與 Phase 4。
7. WRITE 修正檢查與核對發現的問題。

### Phase 3 --- 備妥前置

1. DELEGATE 依 [planner-provisioning](../planner-provisioning/SKILL.md) 在範圍內有這次新排進 Wave 的端點時，補建它們委派但缺少的 Planner。
2. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，在這次要執行的 Wave 中有異動為 ADD 或 MOD 的前端介面列時，重新取得待補跑。
3. DELEGATE 依 [前端設計前置規範](rules/前端設計前置規範.md) 與 [plan-package](../plan-package/SKILL.md) 在前端設計前置條件不齊時，以 record 記錄這次的結果是「改了」。
4. ASK 依 [前端設計前置規範](rules/前端設計前置規範.md) 在前端設計前置條件不齊時，請使用者先執行 /ui-direction 再以依差異入口接續，不執行 Phase 4 與 Phase 5 並停止。

### Phase 4 --- 執行分析 Wave

1. THINK 依 [分析 Wave 執行規範](rules/分析Wave執行規範.md) 在範圍內有要執行的端點時取得開 sub-agent 的工具，工具未直接列出時先查詢，確定無法開啟時停止回報，不得改由自己撰寫介面文檔。
2. DELEGATE 依 [分析 Wave 執行規範](rules/分析Wave執行規範.md) 與 [Planner 配對規範](../planner-provisioning/rules/Planner配對規範.md) 為目前 Wave 範圍內的每個端點各開一個 sub-agent 完整執行對應 Planner 的 SKILL.md，並要求回傳這次的結果、產出、憲法核對結果、衝突與上游問題；功能為增量、改動小或使用者要求一次做完時同樣委派，不得由自己照 Planner 的 skill 撰寫產出。
3. THINK 依 [分析 Wave 執行規範](rules/分析Wave執行規範.md) 只以本次 sub-agent 的回傳確認每個端點的結果與產出，執行前已存在的檔案不算完成；有 plan.md 或前置端點產出的上游問題時，等這個 Wave 全部回傳後回到 Phase 1 Step 5 判定範圍並修正一次，有端點因其他原因回傳不能改、沒有回傳或回報失敗時不執行後續的 Wave，全部完成時回到 Step 2 執行範圍內的下一個 Wave。

### Phase 5 --- 回報結果

1. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在 Planner 依條款化解的衝突要由 plan.md 與前置端點以外的上游擁有者修正、`技術項.md` 還沒有這一項時，以 record 記成技術項並寫上應修正的擁有者。
2. WRITE 依 [分析 Wave 執行規範](rules/分析Wave執行規範.md) 與 [wave-report.md](templates/wave-report.md) 與 [wave-report.example.md](templates/wave-report.example.md) 在這次有執行 Planner 時，只依各 sub-agent 的回傳撰寫或更新 plan 資料夾的 `wave-report.md`，回報各端點的狀態、產出、不能改與憲法衝突，不得加入樣板以外的欄位或回傳以外的合憲宣稱。
3. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
4. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
