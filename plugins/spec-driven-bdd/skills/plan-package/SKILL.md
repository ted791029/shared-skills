---
name: plan-package
description: 工作流的 skill 要開立新的 plan package、確認目標是進行中的 plan 並取得待補跑、在跑完後記錄這次的結果、在實作完成後交付這次迭代，或使用者要放棄進行中的 plan，或呼叫 /plan-package 時使用此 skill。待補跑的補跑由使用者依序執行各擁有者，spec.md 的撰寫交由 specify，任務的拆解與執行交由 task 與 implement，truth 異動的紀錄與核對交由 truth-changes，開發發現的紀錄與確認交由 dev-finding，測試的執行交由 bdd。
---

## SOP

### Phase 1 --- 確認呼叫

1. READ 讀取呼叫者指定的子命令、目標 plan、呼叫的擁有者與這次的結果，以及開立時的英文短名與種類。
2. ASK 未指定子命令時列出 open、check、record、deliver、abandon 五個入口並停止。
3. THINK 依子命令只執行 Phase 2、Phase 3 中對應的 Step 或 Phase 4。

### Phase 2 --- 開立 plan（open）

1. DELEGATE 依 [plan_state.py](scripts/plan_state.py) 與 [腳本執行規範](rules/script-執行規範.md) 以英文短名與種類開立新的 plan 資料夾與 `.plan.json`。
2. ASK 依 [plan 狀態處理規範](rules/plan狀態處理規範.md) 在開立被拒絕時回報原因與下一步並停止。
3. WRITE 依 [truth-changes.md](../truth-changes/templates/truth-changes.md) 在新的 plan 資料夾建立 `truth-changes.md`，開立結果列出的每個 truth owner 各一節只有表頭的表格。
4. WRITE 依 [技術項.md](../dev-finding/templates/技術項.md) 在種類為技術修正時，於新的 plan 資料夾建立只有標題與說明、還沒有任何一行的 `技術項.md`。

### Phase 3 --- 檢查與記錄（check、record、abandon）

1. DELEGATE 依 [plan_state.py](scripts/plan_state.py) 與 [腳本執行規範](rules/script-執行規範.md) 在 check 時以目標 plan 與呼叫的擁有者確認目標是進行中的 plan，並取得待補跑、呼叫者的輸入差異與交叉檢查的結果。
2. DELEGATE 依 [plan_trace.py](scripts/plan_trace.py) 與 [腳本執行規範](rules/script-執行規範.md) 在 record 時以呼叫的擁有者與這次的結果記錄它目前的輸入摘要。
3. DELEGATE 依 [plan_state.py](scripts/plan_state.py) 與 [腳本執行規範](rules/script-執行規範.md) 在 abandon 時輸出還原步驟。
4. ASK 依 [plan 狀態處理規範](rules/plan狀態處理規範.md) 回報 check 或 record 被拒絕的原因與下一步，或 abandon 的還原步驟，並停止。
5. WRITE 依 [串接規範](rules/串接規範.md) 與 [dependencies.json](scripts/dependencies.json) 轉述 check 列出的待補跑、呼叫者的輸入差異與交叉檢查的問題與提醒，或 record 之後仍待補跑的擁有者。

### Phase 4 --- 交付（deliver）

1. DELEGATE 依 [tasks_state.py](../implement/scripts/tasks_state.py) 與 [腳本執行規範](rules/script-執行規範.md) 列出 tasks.md 中未勾選的任務。
2. DELEGATE 依 [baseline.py](../bdd/scripts/baseline.py) 與 [腳本執行規範](rules/script-執行規範.md) 確認全端點驗證的結果是最新的且沒有失敗。
3. DELEGATE 依 [truth_changes.py](../truth-changes/scripts/truth_changes.py) 與 [腳本執行規範](rules/script-執行規範.md) 核對所有 truth owner 的表格與基準以來的實際異動是否一致。
4. DELEGATE 依 [plan_trace.py](scripts/plan_trace.py) 與 [腳本執行規範](rules/script-執行規範.md) 列出待補跑的擁有者。
5. DELEGATE 依 [cross_check.py](scripts/cross_check.py) 與 [腳本執行規範](rules/script-執行規範.md) 以交付階段執行交叉檢查。
6. ASK 依 [交付規範](rules/交付規範.md) 在任一交付條件不成立時逐條列出還缺什麼並停止。
7. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 以 review 請使用者確認這個 plan 標 `@開發發現` 的 AC。
8. ASK 依 [交付規範](rules/交付規範.md) 在 review 刪除或改寫了 AC、交辦了保留並取代，或回報有待補跑時，轉述處理結果與待補跑的擁有者並停止，交付條件由下一次 deliver 重新判定。
9. DELEGATE 依 [plan_state.py](scripts/plan_state.py) 與 [腳本執行規範](rules/script-執行規範.md) 列出將被 commit 的檔案。
10. DELEGATE 依 [check_findings.py](../dev-finding/scripts/check_findings.py) 與 [腳本執行規範](rules/script-執行規範.md) 列出這個 plan 標 `@開發發現` 的 AC 與技術項。
11. WRITE 依 [commit-message.md](templates/commit-message.md) 與 [commit-message.example.md](templates/commit-message.example.md) 撰寫交付的 commit 訊息。
12. ASK 依 [交付規範](rules/交付規範.md) 列出將被 commit 的檔案、commit 訊息與交叉檢查的提醒，詢問使用者是否交付。
13. DELEGATE 依 [plan_state.py](scripts/plan_state.py) 與 [腳本執行規範](rules/script-執行規範.md) 在使用者同意時把 plan 標為已交付並建立單一 commit。
14. WRITE 回報交付結果。
