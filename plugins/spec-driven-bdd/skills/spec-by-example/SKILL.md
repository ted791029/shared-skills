---
name: spec-by-example
description: 使用者已有 specify 產出的功能規格書（spec.md），要在技術研究前讓 PM 以 Gherkin 定義驗收標準與要 Demo 的流程，或 spec.md 變更後要更新既有的驗收 feature（含 plan-package 列出本 skill 待補跑），或 dev-finding 的 review 交辦保留並取代、要依保留的開發發現 AC 改寫 PM 提出的 AC，或呼叫 /spec-by-example 時使用此 skill。從功能描述產出 spec.md 交由 specify，掃描規格盲點與需求變更交由 clarify-over-specs，開發中發現的 AC 交由 dev-finding，plan 的狀態檢查與記錄交由 plan-package，依驗收 feature 衍生端點 feature 與 dsl.md 交由 dsl-refine。
---

## SOP

### Phase 1 --- 讀取規格

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
2. READ 讀取這個 plan 的 spec.md、既有的 `features/acceptance/` 與 dev-finding 交辦的保留並取代，以及 `specs/truth/features/` 的用語表、各端點資料夾的 feature 檔名與可用起點的預設值註解。
3. ASK spec.md 不存在時請使用者先執行 [specify](../specify/SKILL.md)。
4. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取驗收 feature 與 spec.md 適用的憲法條款。

### Phase 2 --- 規劃驗收旅程

1. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 與 [增量更新規範](rules/增量更新規範.md) 在既有 `features/acceptance/` 存在時判斷要新增、修改的 AC 與和既有內容衝突的 AC，只把它們列為這次的範圍：check 回報本 skill 有紀錄且是待補跑時只對列出的每個需求單位差異判斷新增 AC、修改 AC 或不受影響，dev-finding 交辦保留並取代時交辦的 AC 就是這次的差異，本 plan 沒有紀錄時比對整份 spec.md。
2. THINK 依 [feature 規劃規範](rules/feature規劃規範.md) 依使用者操作的功能規劃 feature 清單，並決定每份的檔名。
3. THINK 依 [驗收旅程挑選規範](rules/驗收旅程挑選規範.md) 為每份 feature 挑出 2 至 3 個最關鍵的驗收旅程（既有 `features/acceptance/` 存在時只挑這次範圍內要新增或修改的），並標出每個旅程涵蓋的使用者故事、FR 與 NFR。
4. DELEGATE 依 [check_acceptance.py](scripts/check_acceptance.py) 與 [腳本執行規範](rules/script-執行規範.md) 在既有 `features/acceptance/` 存在且要新增 AC 時取得新增 AC 的編號。
5. ASK 有衝突時列出衝突請使用者確認，並依回覆判斷是否覆蓋。

### Phase 3 --- 撰寫 feature

1. WRITE 依 [Gherkin 撰寫規範](rules/Gherkin撰寫規範.md) 與 [feature 規劃規範](rules/feature規劃規範.md) 與 [功能.feature](templates/功能.feature) 與 [功能.example.feature](templates/功能.example.feature) 從每個 AC 自己需要的起點撰寫這個 plan 的 `features/acceptance/<功能名稱>.feature`。
2. WRITE 依 [feature 規劃規範](rules/feature規劃規範.md) 把所有 AC 起點句相同的 feature 的起點句抽成 Background。
3. WRITE 依 [澄清標記規範](rules/澄清標記規範.md) 在 spec.md 沒有寫清楚且影響驗收流程的步驟上方標出 [NEED CLARIFICATION]。
4. DELEGATE 依 [check_acceptance.py](scripts/check_acceptance.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查所有 feature 的 AC 編號、每份的 Example 數、起點與 Background、澄清標籤總數與涵蓋的需求編號，並列出沒有被任何 AC 涵蓋的使用者故事與需求。
5. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 feature 是否符合憲法條款。
6. WRITE 修正檢查與核對發現的問題。

### Phase 4 --- 澄清並回寫

1. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）在有澄清標籤時，以依 AC 編號與出現位置排序的澄清標籤為提問面向、AC 編號為題目標籤、題數上限為標籤總數，依序訪談使用者，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。
2. WRITE 依 [澄清答案改寫規範](rules/澄清答案改寫規範.md) 把每題答案改進對應的步驟或表格，並刪除該題的澄清標籤。
3. DELEGATE 依 [check_spec.py](../specify/scripts/check_spec.py) 與 [腳本執行規範](rules/script-執行規範.md) 在答案需要新增 FR、NFR、SC 或使用者故事時取得新的編號。
4. WRITE 依 [規格寫回規範](rules/規格寫回規範.md) 與 [釐清結果寫回規範](../clarify-over-specs/rules/釐清結果寫回規範.md) 與 [需求覆蓋分類法](../clarify-over-specs/rules/需求覆蓋分類法.md) 與 [規格內容撰寫規範](../specify/rules/規格內容撰寫規範.md) 與 [需求推導規範](../specify/rules/需求推導規範.md) 與憲法條款把問答寫成 spec.md 釐清紀錄中本次的場次，並寫進答案對應的需求。
5. DELEGATE 依 [check_spec.py](../specify/scripts/check_spec.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查 spec.md 的表頭、受影響的既有功能、編號不重複、交叉引用與殘留佔位符。
6. DELEGATE 依 [check_acceptance.py](scripts/check_acceptance.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 `--clarified` 檢查改寫後的 feature 沒有殘留澄清標籤，且 AC 編號、Example 數、起點與 Background 與涵蓋的需求編號仍然正確。
7. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對改寫後的 feature 與寫回的 spec.md 是否符合憲法條款。
8. WRITE 修正檢查與核對發現的問題。

### Phase 5 --- 回報並記錄

1. WRITE 依 [回報.md](templates/回報.md) 與 [回報.example.md](templates/回報.example.md) 回報模式、輸入差異的判斷、feature 清單、AC 清單、每題的澄清結果、未由旅程驗收的需求與下一步。
2. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
3. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
