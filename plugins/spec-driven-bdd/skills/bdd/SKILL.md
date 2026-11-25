---
name: bdd
description: 使用者已有 dsl-refine 產出的端點 feature 與 dsl.md，要對指定範疇（端點資料夾、feature、Rule 或 Example）執行 BDD 的紅燈、綠燈或重構其中一個階段，或句型只改說明、要確認既有 step 不用改並重新執行範疇，或要執行所有端點的測試確認有沒有回歸，或呼叫 /bdd red、/bdd green、/bdd refactor、/bdd rerun、/bdd verify，或 implement 委派紅燈、綠燈、重構、重跑或驗證任務時使用此 skill。feature、dsl.md 與用語表的產生與修正交由 dsl-refine，介面文檔的錯誤與規格沒寫的行為交由 dev-finding，依 tasks.md 逐任務執行交由 implement，任務的拆解交由 task。
---

## SOP

### Phase 1 --- 確認範疇

1. READ 讀取呼叫者指定的 subcommand、範疇與附帶的 NFR 約束、預計修改、必讀與任務描述。
2. ASK 未指定 subcommand 時列出 red、green、refactor、rerun、verify 五個入口並停止。
3. THINK subcommand 為 verify 時略過本 Phase 其餘 Step，直接執行 Phase 5。
4. DELEGATE 依 [全端點驗證規範](rules/全端點驗證規範.md) 執行 Phase 5 的 Step 1 至 Step 3，確認所有端點的測試環境就緒且沒有殘留的測試行程。
5. DELEGATE 依 [resolve_scope.py](scripts/resolve_scope.py) 與 [腳本執行規範](rules/script-執行規範.md) 把範疇展開為端點資料夾與 Example 行號清單（Rule 行或 Rule 名稱展開為其下全部 Example，換算依範疇與執行規範）。
6. READ 讀取範疇所屬端點資料夾的 feature 與 dsl.md、`specs/truth/features/用語表.md`、`specs/truth/techstack.md`、進行中 plan 的 plan.md 的原始碼、`truth-changes.md` 與該端點介面文檔、呼叫者附帶的必讀與 NFR 約束在 spec.md 的原文，以及既有的 step definitions、Driver 與產品程式。
7. THINK 依 [範疇與執行規範](rules/範疇與執行規範.md) 從專案測試設定判定範疇的 step 目錄、範疇指令、端點資料夾指令與任務指令組。
8. ASK 依 [停下回報規範](rules/停下回報規範.md) 在沒有測試設定涵蓋範疇的 feature 或沒有載入 step 時停下回報。
9. DELEGATE 依 [全端點驗證規範](rules/全端點驗證規範.md) 在 `specs/truth/features/.verify-result.json` 不存在時以完整指令組執行 Phase 5 的 Step 4 至 Step 9 建立上次結果（不傳 `--ran-scope`）。
10. DELEGATE 依 [baseline.py](scripts/baseline.py) 與 [腳本執行規範](rules/script-執行規範.md) 讀出範疇與（快速端點的）範疇所在端點資料夾每個 Example 的上次結果，並判定範疇的結果是否可沿用。
11. DELEGATE 依 [範疇與執行規範](rules/範疇與執行規範.md) 與 [全端點驗證規範](rules/全端點驗證規範.md) 在 green 或 refactor 而範疇的結果不可沿用、沿用的失敗訊息不足以判定失敗原因類別，或沿用的結果使進入條件不成立時，以任務指令組執行 Phase 5 的 Step 4 至 Step 8 確認現況。
12. THINK 依 subcommand 只執行 Phase 2、Phase 3、Phase 4 或 Phase 6 其中一個。

### Phase 2 --- 紅燈（red）

1. WRITE 依 [Step definitions 撰寫規範](rules/step-definitions-撰寫規範.md) 依 dsl.md 撰寫範疇內尚未定義、或句型的測試寫法已改的 step definitions 與 Driver。
2. DELEGATE 依 [範疇與執行規範](rules/範疇與執行規範.md) 與 [全端點驗證規範](rules/全端點驗證規範.md) 與 [紅燈規範](rules/紅燈規範.md) 以任務指令組（改寫既有 step 時另加範疇外用到它的 Example）執行 Phase 5 的 Step 4 至 Step 8，判定範疇內每個 Example 的失敗原因與回歸。
3. ASK 依 [停下回報規範](rules/停下回報規範.md) 在 feature 或 dsl.md 有問題，或失敗原因是其他端點尚未實作時停下回報。
4. WRITE 依 [Step definitions 撰寫規範](rules/step-definitions-撰寫規範.md) 在失敗原因是測試程式錯誤或有本階段可修正的回歸時修正測試程式，修正後回到 Step 2。
5. WRITE 依 [紅燈規範](rules/紅燈規範.md) 在範疇內的 Example 第一次就通過時破壞產品程式，破壞後回到 Step 2。
6. DELEGATE 依 [全端點驗證規範](rules/全端點驗證規範.md) 以最後一次執行的報告與參數執行 Phase 5 的 Step 9 至 Step 10 存回結果。
7. WRITE 依 [紅燈規範](rules/紅燈規範.md) 寫出紅燈完成說明。

### Phase 3 --- 綠燈（green）

1. ASK 依 [階段範圍規範](rules/階段範圍規範.md) 與 [停下回報規範](rules/停下回報規範.md) 在現況中範疇內有 Example 既不是業務行為尚未實作的紅燈，也沒有通過時停下回報。
2. WRITE 依 [綠燈規範](rules/綠燈規範.md) 依呼叫者附帶的必讀與 NFR 約束撰寫讓範疇通過的最小產品程式，範疇已通過時不新增產品程式，並還原紅燈留下的破壞。
3. DELEGATE 依 [範疇與執行規範](rules/範疇與執行規範.md) 與 [全端點驗證規範](rules/全端點驗證規範.md) 在本階段修改過檔案時以任務指令組執行 Phase 5 的 Step 4 至 Step 8。
4. ASK 依 [停下回報規範](rules/停下回報規範.md) 在 feature 或 dsl.md 矛盾或無法實作、失敗原因是其他端點尚未實作，或範疇內出現測試程式錯誤時停下回報。
5. WRITE 依 [階段範圍規範](rules/階段範圍規範.md) 在範疇未全部通過或有本階段可修正的回歸時修正產品程式，修正後回到 Step 3。
6. DELEGATE 依 [全端點驗證規範](rules/全端點驗證規範.md) 以最後一次執行的報告與參數執行 Phase 5 的 Step 9 至 Step 10 存回結果。
7. WRITE 依 [綠燈規範](rules/綠燈規範.md) 寫出綠燈完成說明。

### Phase 4 --- 重構（refactor）

1. ASK 依 [階段範圍規範](rules/階段範圍規範.md) 與 [停下回報規範](rules/停下回報規範.md) 在現況中範疇內有 Example 未通過時停下回報。
2. WRITE 依 [重構規範](rules/重構規範.md) 與 [階段範圍規範](rules/階段範圍規範.md) 與 [Step definitions 撰寫規範](rules/step-definitions-撰寫規範.md) 在不改變行為的前提下重構範疇對應的 step definitions、Driver 與產品程式，呼叫者附帶任務描述時依描述重構。
3. DELEGATE 依 [範疇與執行規範](rules/範疇與執行規範.md) 與 [全端點驗證規範](rules/全端點驗證規範.md) 在本階段修改過檔案時以任務指令組執行 Phase 5 的 Step 4 至 Step 8。
4. WRITE 依 [重構規範](rules/重構規範.md) 在範疇未全部通過或有本階段可修正的回歸時修正或還原這次重構，修正後回到 Step 3。
5. DELEGATE 依 [全端點驗證規範](rules/全端點驗證規範.md) 以最後一次執行的報告與參數執行 Phase 5 的 Step 9 至 Step 10 存回結果。
6. WRITE 依 [重構規範](rules/重構規範.md) 寫出重構完成說明。

### Phase 5 --- 全端點驗證（verify）

1. READ 讀取 `specs/truth/features/用語表.md`、`specs/truth/techstack.md` 與專案的測試設定。
2. THINK 依 [全端點驗證規範](rules/全端點驗證規範.md) 與 [範疇與執行規範](rules/範疇與執行規範.md) 決定每個端點的完整指令、任務驗證的指令組與所有端點的測試環境是否就緒，並以 [cleanup_test_processes.py](scripts/cleanup_test_processes.py) 與 [腳本執行規範](rules/script-執行規範.md) 確認沒有殘留的測試行程與未還原的紅燈破壞標記。
3. ASK 依 [停下回報規範](rules/停下回報規範.md) 在任一端點的測試環境或測試設定未就緒，或完整指令組執行前仍有未還原的紅燈破壞標記時停下回報。
4. DELEGATE 依 [全端點驗證規範](rules/全端點驗證規範.md) 與 [run_suite.py](scripts/run_suite.py) 與 [腳本執行規範](rules/script-執行規範.md) 依呼叫時機的指令組（完整或任務）序列執行，輸出 JSON 報告與執行紀錄。
5. DELEGATE 依 [verify_result.py](scripts/verify_result.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 `--dry-run` 把各端點的報告正規化為每個 Example 的通過或失敗，與 `specs/truth/features/.verify-result.json` 的上次結果比對出回歸，不寫結果檔（完整指令組不傳 `--partial` 與 `--ran-scope`；任務指令組以 `--ran-scope` 傳入本次實際執行的範疇，範疇外的 Example 沿用上次結果）。
6. DELEGATE 依 [全端點驗證規範](rules/全端點驗證規範.md) 與 [run_suite.py](scripts/run_suite.py) 在有回歸時單獨重跑每個回歸的 Example 並輸出 JSON 報告。
7. DELEGATE 依 [verify_result.py](scripts/verify_result.py) 與 [腳本執行規範](rules/script-執行規範.md) 在 Step 6 有重跑時把重跑報告接在原報告之後覆蓋同一 Example 的結果，以 `--dry-run` 重新比對。
8. THINK 依 [全端點驗證規範](rules/全端點驗證規範.md) 與 [範疇與執行規範](rules/範疇與執行規範.md) 為重跑後仍失敗的回歸判定失敗原因類別，並以進行中 plan 的 `features/涵蓋表.md` 對回 AC。
9. DELEGATE 依 [verify_result.py](scripts/verify_result.py) 與 [腳本執行規範](rules/script-執行規範.md) 以與 Step 7 相同的參數（不傳 `--dry-run`，以 `--run` 傳入 Step 4 與 Step 6 的執行紀錄）比對並把結果存回 `specs/truth/features/.verify-result.json`，完整 JSON 以 `--out` 寫到暫存目錄。
10. ASK 依 [停下回報規範](rules/停下回報規範.md) 與 [全端點驗證規範](rules/全端點驗證規範.md) 在有回歸，或比對結果有未執行、無法對應的 Example 時停下回報。
11. WRITE 依 [全端點驗證規範](rules/全端點驗證規範.md) 在沒有回歸時簡短說明驗證結果。

### Phase 6 --- 重跑（rerun）

1. THINK 依 [重跑規範](rules/重跑規範.md) 比對呼叫者任務描述列出的句型或參數的既有 step definitions 與 Driver 和 dsl.md 現在的寫法，判定既有 step 是否需要改。
2. ASK 依 [停下回報規範](rules/停下回報規範.md) 在既有 step 需要改時停下並建議改排紅燈。
3. DELEGATE 依 [範疇與執行規範](rules/範疇與執行規範.md) 與 [全端點驗證規範](rules/全端點驗證規範.md) 在範疇的結果不可沿用或沿用的結果有失敗時，以任務指令組執行 Phase 5 的 Step 4 至 Step 10（含存回結果）。
4. WRITE 依 [重跑規範](rules/重跑規範.md) 寫出重跑完成說明。
