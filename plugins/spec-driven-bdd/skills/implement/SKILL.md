---
name: implement
description: 使用者已有任務清單（tasks.md），要依任務把功能實作成程式碼，或呼叫 /implement 時使用此 skill。任務的拆解與未勾選任務的修正交由 task，BDD 紅燈、綠燈、重構、重跑與全端點驗證的執行交由 bdd，feature 與 dsl.md 交由 dsl-refine，plan.md 的原始碼段交由 system-analysis，開發中發現的問題交由 dev-finding，plan 的狀態檢查與交付交由 plan-package。
---

## SOP

### Phase 1 --- 讀取輸入

1. READ 讀取使用者輸入的範圍篩選。
2. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 確認目標是進行中的 plan，被拒絕，或列出待補跑的擁有者時停止（tasks.md 可能已經過時，請使用者先依待補跑依序補跑）。
3. DELEGATE 依 [tasks_state.py](scripts/tasks_state.py) 與 [腳本執行規範](rules/script-執行規範.md) 解析這個 plan 的 tasks.md 的任務狀態、Phase 標頭、階段任務的範疇與必讀錨點檔案是否存在。
4. THINK 依 [輸入完整性規範](rules/輸入完整性規範.md) 確認輸入完整，並界定範圍內要執行的任務。
5. ASK 有輸入缺漏或範圍內任務之前有未完成的範圍外任務時列出缺漏，並請使用者先處理。

### Phase 2 --- 準備專案

1. THINK 依 [Ignore 檔規範](rules/Ignore檔規範.md) 偵測專案使用的工具，並比對 tasks.md 中建立 ignore 檔的任務。
2. WRITE 建立或補齊不由任務建立的 ignore 檔。
3. THINK 依 [檢查指令選擇規範](rules/檢查指令選擇規範.md) 從 `specs/truth/techstack.md` 決定各類檔案的語法檢查指令與專案的 lint 指令。

### Phase 3 --- 選定任務

1. DELEGATE 依 [tasks_state.py](scripts/tasks_state.py) 與 [腳本執行規範](rules/script-執行規範.md) 以範圍的任務編號與 `--summary` 列出範圍內下一個任務、它所屬 Phase 的標頭與各 Phase 的完成進度。
2. THINK 依 [執行順序規範](rules/執行順序規範.md) 選出範圍內下一個要執行的任務。
3. READ 讀取該任務適用的所有必讀原文。
4. THINK 依 [錨點對照規範](rules/錨點對照規範.md) 比對任務描述與必讀原文。
5. ASK 依 [停止回報.md](templates/停止回報.md) 與 [停止回報.example.md](templates/停止回報.example.md) 在必讀衝突或找不到時停止執行並回報。

### Phase 4 --- 執行任務

1. DELEGATE 依 [bdd](../bdd/SKILL.md) 與 [實作範圍規範](rules/實作範圍規範.md) 在任務標 `[紅燈]`、`[綠燈]`、`[重構]` 或 `[重跑]` 時以對應的 subcommand 傳入範疇與所屬 Phase 標頭（沒有標頭的 NFR 重構與 `[重跑]` 改附任務描述與逐任務必讀），只執行標記的階段。
2. DELEGATE 依 [bdd](../bdd/SKILL.md) 與 [bdd 停下處理規範](rules/bdd停下處理規範.md) 在 bdd green 因範疇內測試程式錯誤停下並建議先執行 red 時，對同一範疇依序委派 red 與 green 各重試一次。
3. DELEGATE 依 [bdd](../bdd/SKILL.md) 與 [驗證任務規範](rules/驗證任務規範.md) 在任務標 `[驗證]` 時以 verify 執行所有端點的測試並與上次結果比對。
4. DELEGATE 依 [bdd](../bdd/SKILL.md) 與 [bdd 停下處理規範](rules/bdd停下處理規範.md) 在回歸符合重試條件時，對回歸的 Example 依建議各重試一次後再次 verify。
5. WRITE 依 [實作範圍規範](rules/實作範圍規範.md) 在任務沒有階段或驗證標記時實作任務。
6. DELEGATE 依 [static_check.py](scripts/static_check.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 Phase 2 決定的指令對直接實作的任務建立或修改的檔案執行語法檢查與 lint。
7. WRITE 依 [靜態檢查規範](rules/靜態檢查規範.md) 修正靜態檢查發現的錯誤。
8. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在 bdd 的說明或直接實作的任務中發現規格沒寫的行為、bdd 判斷介面文檔有誤，或認為既有的規格（需求、AC、介面文檔、feature）應該改變時，以 record 記錄這個發現。
9. DELEGATE 依 [system-analysis](../system-analysis/SKILL.md) 與 [bdd 停下處理規範](rules/bdd停下處理規範.md) 在 bdd 的完成說明或直接實作的任務列出原始碼段以外的產品檔時，以原始碼段入口帶入這些檔案修正 plan.md 的原始碼段。
10. DELEGATE 依 [task](../task/SKILL.md) 在 Step 9 修正了原始碼段時，以增量入口修正未勾選的任務。
11. ASK 依 [bdd 停下處理規範](rules/bdd停下處理規範.md) 與 [停止回報.md](templates/停止回報.md) 與 [停止回報.example.md](templates/停止回報.example.md) 在 bdd 停下且未經重試完成、verify 的回歸不符合重試條件或重試後仍有回歸、verify 有未執行或無法對應的 Example、system-analysis 或 task 停下，或靜態檢查錯誤無法在任務範圍內修正時停止執行並回報。
12. WRITE 在 tasks.md 將該任務勾為 [X]。
13. WRITE 回報該任務的完成進度、修改的檔案與 verify 結果，範圍內仍有未完成任務時回到 Phase 3。

### Phase 5 --- 收尾驗證

1. DELEGATE 依 [static_check.py](scripts/static_check.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 Phase 2 決定的指令對範圍內所有任務建立或修改的檔案執行語法檢查與 lint。
2. THINK 依 [驗證任務規範](rules/驗證任務規範.md) 決定收尾引用的 verify 結果，範圍不含 `[驗證]` 任務時寫明未執行。
3. READ 讀取這個 plan 的 `features/涵蓋表.md`、`truth-changes.md`、`技術項.md` 與 `features/acceptance/` 中標 `@開發發現` 的 AC。
4. THINK 依 [收尾驗證規範](rules/收尾驗證規範.md) 對照 spec.md、plan.md、`specs/truth/techstack.md`、verify 結果與涵蓋表的 AC 涵蓋表確認實作符合規格、技術計畫與各故事的驗收標準。
5. WRITE 依 [完成報告.md](templates/完成報告.md) 與 [完成報告.example.md](templates/完成報告.example.md) 撰寫完成報告。
6. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 在 tasks.md 的任務全部勾選時以 deliver 交付這個 plan。
