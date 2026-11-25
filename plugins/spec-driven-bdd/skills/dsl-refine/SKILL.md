---
name: dsl-refine
description: 使用者已有 spec-by-example 產出的驗收 feature 與 system-analysis 產出的 plan.md 和介面文檔，要把驗收標準衍生成前端、後端、資料庫等各端點可直接寫成測試程式的 Gherkin feature 與 dsl.md，或驗收 feature、介面文檔變更後要更新既有的端點 feature，或 plan-package 列出本 skill 待補跑、被交辦修正指定的 Rule 或句型、`技術項.md` 有交給本 skill 修正的行（含技術修正 plan），或呼叫 /dsl-refine 時使用此 skill。驗收 feature 的撰寫與澄清交由 spec-by-example，plan.md 與介面文檔交由 system-analysis 與各 Planner，plan 的狀態檢查與記錄交由 plan-package，truth 異動的盤點與紀錄交由 truth-changes，規格沒寫的行為與上游的錯漏交由 dev-finding，step definitions 與測試的執行交由 bdd。
---

## SOP

### Phase 1 --- 讀取輸入

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得 plan 的種類、待補跑與本 skill 的輸入差異，被拒絕時停止。
2. READ 讀取這個 plan 的 spec.md、`features/acceptance/`、plan.md、wave-report.md（技術修正 plan 沒有這四項）、`技術項.md` 中「修正：dsl-refine」的行與 `specs/truth/techstack.md`，以及專案既有的測試設定（如 behave 設定與 runner、`playwright.config.js`）。
3. ASK 這是需求 plan，而 `features/acceptance/`、plan.md、wave-report.md 或 `specs/truth/techstack.md` 缺漏，或 wave-report.md 有端點的狀態不是「完成」（未完成、未執行或不能改）時，列出缺漏並請使用者先執行產出它的上游 skill（spec-by-example、system-analysis 或 technical-research），不能改的端點依 wave-report.md「不能改」一段交給使用者或 PM，之後再繼續；acceptance 殘留 `[NEED CLARIFICATION]` 時請使用者先完成 spec-by-example 的澄清。
4. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 query 取得上游已記錄的 truth 異動。
5. READ 讀取 wave-report.md 列出的各端點介面文檔（plan 資料夾的文檔與它以「沿用」指到的先前 plan 的文檔）、`truth-changes.md` 各 Planner 一節寫明的 truth 資料夾中這次的介面涉及的現況，以及技術項、交辦內容與輸入差異引用的介面文檔。
6. READ 讀取 `specs/truth/features/` 的用語表、各端點資料夾的 dsl.md，以及與 acceptance 同名、spec.md「受影響的既有功能」、上游異動、技術項或交辦內容涉及的 feature。
7. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 feature 與 dsl.md 適用的憲法條款。

### Phase 2 --- 規劃骨架

1. DELEGATE 依 [plan_cases.py](scripts/plan_cases.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 diff 比對 acceptance 與這個 plan 上次的產生紀錄，列出新增、修改、刪除的 AC、它們對應的 Rule 與使用者手改過的 Example。
2. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 與 [異動判斷規範](rules/異動判斷規範.md) 在 check 回報本 skill 有紀錄且是待補跑、被交辦修正，或目標是技術修正 plan 時，對每個輸入差異、交辦內容與 `技術項.md` 中「修正：dsl-refine」的行判斷連帶異動或不受影響，只把連帶異動的 Rule、句型與用語表項目列為這次的範圍。
3. DELEGATE 依 [plan_cases.py](scripts/plan_cases.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 list 列出每個 AC 的起點、When 組與斷言、plan.md 的介面前綴與異動、techstack.md 的測試工具與 spec.md 的需求編號。
4. THINK 依 [端點分派規範](rules/端點分派規範.md) 以 plan.md 介面盤點的介面 ID 前綴與 techstack.md 的測試工具決定端點資料夾，並從專案測試設定找出各端點資料夾載入的 step 目錄與既有 step 模組。
5. THINK 依 [端點分派規範](rules/端點分派規範.md) 依介面文檔把 AC 每組 When 的每個動作分派到在該動作有行為的畫面或 API 端點。
6. THINK 依 [AC 衍生規範](rules/AC衍生規範.md) 為每個分派到的端點列出 AC 衍生的 Rule 與它對照既有 Rule 的異動，以及每個 Example 從 acceptance 已登記的起點中選用的起點、Given、要驗的動作與要落到 Then 的斷言。
7. THINK 依 [AC 衍生規範](rules/AC衍生規範.md) 與 [端點分派規範](rules/端點分派規範.md) 從 spec.md 與介面文檔挑出 AC 沒涵蓋的補充案例與它的起點，分派到能直接驗證它的端點，儲存端點只接儲存結構與約束的案例。
8. THINK 依 [feature 規劃規範](rules/feature規劃規範.md) 為每個有案例的端點資料夾依功能規劃 feature 清單與每份所屬的模組。
9. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 inventory 盤點這次對 `specs/truth/features/` 的新增、修改與刪除（依差異判斷時另帶入這次的範圍與輸入差異）。
10. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在規劃或盤點中發現規格沒寫的行為，或介面文檔與 acceptance 不一致、缺了衍生需要的事實時，以 record 記錄並取得應修正的擁有者（介面文檔的問題為該文檔的 Planner），回覆應由本 skill 修正的列入這次的範圍，新增了 AC 時回到 Step 1 把它納入規劃。
11. WRITE 依 [DSL 撰寫規範](rules/DSL撰寫規範.md) 與 [用語表.md](templates/用語表.md) 與 [用語表.example.md](templates/用語表.example.md) 增修 `specs/truth/features/用語表.md` 的端點、模組、技術說法對照、跨端點共用的參數合法值、共用句子與同名 Rule。
12. WRITE 依 [涵蓋表.md](templates/涵蓋表.md) 與 [涵蓋表.example.md](templates/涵蓋表.example.md) 撰寫 plan 資料夾的 `features/涵蓋表.md`，含 AC 句型對照（含本端點不適用的步驟）、AC 涵蓋表與補充案例。
13. THINK 依 [子 agent 委派規範](rules/子agent委派規範.md) 判定每個有異動的端點資料夾要開 sub-agent，或由主 agent 直接修改。
14. DELEGATE 依 [子 agent 委派規範](rules/子agent委派規範.md) 與 [委派簡報.md](templates/委派簡報.md) 與 [委派簡報.example.md](templates/委派簡報.example.md) 為判定要開 sub-agent 的端點資料夾各開一個 sub-agent，同時執行 Phase 3 並回傳產出、涵蓋表的異動、句型異動、待確認事項、規格沒寫的行為、上游的事實問題、增量衝突與新增的技術說法。
15. WRITE 為判定由主 agent 直接修改的端點資料夾執行 Phase 3 的 Step 4 至 Step 6。

### Phase 3 --- 產生端點內容

1. WRITE 依 [Rule 與 Example 規範](rules/Rule與Example規範.md) 與 [步驟與斷言規範](rules/步驟與斷言規範.md) 與 [前端測試規範](rules/前端測試規範.md) 與 [功能.feature](templates/frontend/功能.feature) 與 [功能.example.feature](templates/frontend/功能.example.feature) 與 [功能.feature](templates/backend/功能.feature) 與 [功能.example.feature](templates/backend/功能.example.feature) 與 [功能.feature](templates/database/功能.feature) 與 [功能.example.feature](templates/database/功能.example.feature) 與 [功能.feature](templates/filesystem/功能.feature) 與 [功能.example.feature](templates/filesystem/功能.example.feature) 依委派簡報指定的樣板資料夾與異動範圍，在該端點資料夾新增、修改、刪除 feature 的 Rule 與 Example，每個 Example 從自己的起點撰寫。
2. WRITE 依 [feature 規劃規範](rules/feature規劃規範.md) 把所有 Example 起點句相同的 feature 的起點句抽成 Background。
3. WRITE 依 [句型收斂規範](rules/句型收斂規範.md) 收斂 feature 步驟的句型，先沿用該端點 dsl.md 既有的句型。
4. WRITE 依 [DSL 撰寫規範](rules/DSL撰寫規範.md) 與 [dsl.md](templates/frontend/dsl.md) 與 [dsl.example.md](templates/frontend/dsl.example.md) 與 [dsl.md](templates/backend/dsl.md) 與 [dsl.example.md](templates/backend/dsl.example.md) 與 [dsl.md](templates/database/dsl.md) 與 [dsl.example.md](templates/database/dsl.example.md) 與 [dsl.md](templates/filesystem/dsl.md) 與 [dsl.example.md](templates/filesystem/dsl.example.md) 依委派簡報指定的樣板資料夾增修該端點資料夾的 dsl.md：加上新用到的句型，修改與刪除異動範圍列出的既有句型，刪除不再被任何 feature 使用的句型，每個 Then 句型寫出回應斷言與其他管道的查證斷言。
5. DELEGATE 依 [check_features.py](scripts/check_features.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查該端點資料夾的 feature 與 dsl.md。
6. WRITE 修正檢查發現的問題。

### Phase 4 --- 合併回報

1. THINK 只以本輪 sub-agent 的回傳確認本輪委派的每個端點資料夾的產出，有委派的端點資料夾沒有回傳或回報失敗時停止回報。
2. WRITE 依 [跨端點一致規範](rules/跨端點一致規範.md) 統一各端點資料夾的共用句子與同名 Rule，並把 sub-agent 回傳的涵蓋表異動與 AC 句型對照異動補進涵蓋表、新增技術說法補進用語表。
3. THINK 依 [跨端點一致規範](rules/跨端點一致規範.md) 比對每個端點 dsl.md 依賴的其他端點入口、回應欄位與推播事件，找出被依賴端點沒有 Rule 驅動的缺口。
4. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在各端點回傳了規格沒寫的行為或上游的事實問題時，以 record 記錄並取得應修正的擁有者，新增了 AC 時保留本輪的回傳，回到 Phase 2 Step 1 以新增的 AC 為異動範圍再執行一次。
5. DELEGATE 依 [check_features.py](scripts/check_features.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查全部端點資料夾的 feature、dsl.md、編號的 plan 前綴與 AC 涵蓋。
6. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對這次新增與修改的 feature 與 dsl.md 是否符合憲法條款。
7. WRITE 修正檢查、比對與核對發現的問題。
8. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 與 [異動判斷規範](rules/異動判斷規範.md) 以 record 把這次的異動記進 plan 的 `truth-changes.md` 並核對，修改既有句型、Background、預設值註解或用語表的列標明只改說明或改測試寫法。
9. DELEGATE 依 [plan_cases.py](scripts/plan_cases.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 record 更新 plan 與 truth 的產生紀錄。
10. WRITE 依 [待確認事項規範](rules/待確認事項規範.md) 與 [回報.md](templates/回報.md) 與 [回報.example.md](templates/回報.example.md) 回報各端點資料夾的產出、沒有案例而未產生的端點與原因、AC 涵蓋、truth 異動、補充案例、含應修正的擁有者的開發發現與待確認事項（含只有回應或只有查證的句型與跨端點依賴缺口）。
11. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
12. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
