---
name: task
description: 使用者已有 dsl-refine 產出的端點 feature、dsl.md 與涵蓋表，以及 system-analysis 產出的 plan.md 與介面文檔，要把功能拆解成實作任務清單（tasks.md），或 plan-package 列出本 skill 待補跑、implement 交辦修正未勾選的任務、技術修正 plan 要為 truth 的修正排任務，或呼叫 /task 時使用此 skill。端點 feature 與 dsl.md 交由 dsl-refine，plan.md 與介面文檔交由 system-analysis，開發發現的確認交由 dev-finding，plan 的狀態檢查與記錄交由 plan-package，任務的實作交由 implement，BDD 各階段的執行交由 bdd。
---

## SOP

### Phase 1 --- 讀取輸入

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
2. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 以 review 請使用者確認標 `@開發發現` 的 AC，review 回報有 AC 被刪除或改寫、交辦了保留並取代，或回報有 task 以外的擁有者待補跑時停止（task 自己這時本來就是待補跑，不算），請使用者先依 plan-package check 列出的待補跑依序補跑。
3. READ 讀取這個 plan 的 `truth-changes.md`、`技術項.md`、既有的 tasks.md，需求 plan 另讀 spec.md、plan.md、research.md、`features/`（acceptance 與涵蓋表）與 plan 資料夾中的介面文檔，以及 `specs/truth/` 的 techstack.md、這次異動的介面文檔與 `features/`（用語表、這次異動的 feature 與各端點資料夾的 dsl.md）。
4. THINK 依 [輸入完整性規範](rules/輸入完整性規範.md) 確認這個 plan 的種類應有的輸入皆存在。
5. THINK 依 [需求對應規範](rules/需求對應規範.md) 讀取涵蓋表與 acceptance 涵蓋註解列出的 NFR 所指的 Rule，判定每個條件都被 Rule 驗證的 NFR。
6. DELEGATE 依 [feature_summary.py](scripts/feature_summary.py) 與 [腳本執行規範](rules/script-執行規範.md) 以各 feature 經 dsl.md 走到的介面為 `--interfaces`、以判定已被完整驗證的 NFR 為 `--verified-nfr`，統計要排的 Feature Phase、修正 Phase 與 [重跑] 任務的範疇、Rule 數、Example 數、驗收 AC、Rule 需求聯集、涵蓋的最高優先故事與 NFR 約束，並列出 tasks.md 的進度、被刪除的 feature、每一列 DEL、只刪除了 Example 的 Rule、撤回的 Rule、技術項、這次異動的技術堆疊與未驗證的 NFR。
7. THINK 依 [案例缺口規範](rules/案例缺口規範.md) 確認這次新增或修改的每條 Rule 都登記在涵蓋表，且這次異動的介面、上游的 truth 異動與 plan.md 的實作內容都有 Rule 驅動。
8. ASK 有輸入缺漏或案例缺口時列出，並請使用者先執行產出它的上游 skill（specify、technical-research、system-analysis、spec-by-example 或 dsl-refine）後再繼續，不記錄。
9. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 tasks.md 適用的憲法條款。

### Phase 2 --- 規劃 Phase

1. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 在 check 回報本 skill 有紀錄且是待補跑時，對列出的每個輸入差異判斷連帶異動或不受影響，只把連帶異動列為這次的範圍。
2. THINK 依 [任務拆解規範](rules/任務拆解規範.md) 排定 Feature Phase 與修正 Phase 的順序，tasks.md 已有勾選的任務時只重新規劃尚未開始的部分。

### Phase 3 --- 撰寫任務清單

1. WRITE 依憲法條款與 [基礎任務規範](rules/基礎任務規範.md) 與 [必讀錨點規範](rules/必讀錨點規範.md) 與 [tasks.md](templates/tasks.md) 與 [tasks.example.md](templates/tasks.example.md) 在 plan 資料夾撰寫 tasks.md 的表頭、Setup 與 Foundational。
2. WRITE 依 [需求對應規範](rules/需求對應規範.md) 與 [必讀錨點規範](rules/必讀錨點規範.md) 與 [案例任務規範](rules/案例任務規範.md) 撰寫每個 Feature Phase 與修正 Phase 的驗收 AC、NFR 約束、預計修改與必讀。
3. WRITE 依 [案例任務規範](rules/案例任務規範.md) 撰寫每個 Feature Phase 與修正 Phase 的紅燈、綠燈與重構任務。
4. WRITE 依 [案例任務規範](rules/案例任務規範.md) 與 [必讀錨點規範](rules/必讀錨點規範.md) 撰寫重跑 Phase 的 [重跑] 任務。
5. WRITE 依 [基礎任務規範](rules/基礎任務規範.md) 與 [必讀錨點規範](rules/必讀錨點規範.md) 撰寫移除與技術項 Phase。
6. WRITE 依 [需求對應規範](rules/需求對應規範.md) 與 [必讀錨點規範](rules/必讀錨點規範.md) 與 [基礎任務規範](rules/基礎任務規範.md) 撰寫 NFR 重構 Phase。
7. WRITE 依 [基礎任務規範](rules/基礎任務規範.md) 撰寫 Polish 與 Verify Phase。

### Phase 4 --- 檢查修正

1. DELEGATE 依 [check_tasks.py](scripts/check_tasks.py) 與 [腳本執行規範](rules/script-執行規範.md) 以每個端點 Planner 產出的介面文檔為 `--own-doc`、以同一組 `--interfaces` 與 `--verified-nfr` 檢查任務編號、已勾選任務的位置與內容、Phase 結構與順序、範疇、Rule 與 Example 數、驗收 AC、必讀、[重跑] 任務、技術項、DEL 列與撤回 Rule 的涵蓋、NFR 分割、NFR 重構任務粒度與描述涵蓋、Verify 的位置與殘留佔位符。
2. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 tasks.md 是否符合憲法條款，並判斷腳本回報的問題是否與條款衝突。
3. WRITE 修正檢查與核對發現的問題。
4. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
5. DELEGATE 依 [feature_summary.py](scripts/feature_summary.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 `--record` 記下這次拆解時 truth 的逐 Example 狀態與每個任務涵蓋的 Rule。
6. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
