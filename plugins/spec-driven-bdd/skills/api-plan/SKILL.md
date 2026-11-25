---
name: api-plan
description: 執行 plan.md 分析 Wave 中後端（介面 ID 前綴 API）的分析，或 plan-package 列出本 skill 待補跑、`技術項.md` 或 dev-finding 的回覆交給本 skill 修正 `specs/truth/contracts/`（含技術修正 plan），或呼叫 /api-plan 時使用此 skill。plan.md 的介面列與 Wave 由 system-analysis 修正，本 skill 只回報；truth 異動的盤點與紀錄交由 truth-changes。
---

## SOP

### Phase 1 --- 讀取輸入

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
2. READ 讀取呼叫參數指定的 plan.md（技術修正 plan 沒有）中的共用輸入、所屬端點的介面列與該 Wave 的分析重點（Wave 為「無」時沒有）、`features/acceptance/` 中涵蓋這些介面列依據需求的 AC，以及 `技術項.md` 中「修正：api-plan」的行。
3. READ 依 [Planner 配對規範](../planner-provisioning/rules/Planner配對規範.md) 找到「相依」列出的前置端點的 Planner，讀取它這次的產出。
4. READ 讀取 `specs/truth/contracts/` 的入口檔，以及介面列、技術項與前置產出涉及的既有契約。
5. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 `specs/truth/contracts/` 適用的憲法條款。
6. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 與 [依差異判斷規範](rules/依差異判斷規範.md) 在 check 回報本 skill 有紀錄且是待補跑、本 skill 沒有排進 Wave、目標是技術修正 plan 或被交辦修正時，對列出的每個輸入差異或交辦內容判斷連帶異動或不受影響，只把連帶異動列為這次的範圍。

### Phase 2 --- 分析介面

1. THINK 依 [API 分析規範](rules/API分析規範.md) 與憲法條款從這次範圍內的介面列、分析重點、涵蓋的 AC、前置產出、技術項與既有契約推導每個要新增、修改或移除的 API 的路徑、請求、回應、錯誤與需要內層讀寫的資料與檔案。

### Phase 3 --- 增修契約

1. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 inventory 盤點這次對 `specs/truth/contracts/` 的新增、修改與刪除，依差異判斷時另帶入這次的輸入差異。
2. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在分析或盤點中發現規格沒寫的行為、前置端點的產出錯了或缺了，或既有契約與程式不一致時，以 record 記錄。
3. WRITE 依 [契約拆檔規範](rules/契約拆檔規範.md) 與憲法條款與 [openapi.yaml](templates/openapi.yaml) 與 [openapi.example.yaml](templates/openapi.example.yaml) 與 [path.yaml](templates/path.yaml) 與 [path.example.yaml](templates/path.example.yaml) 與 [schema.yaml](templates/schema.yaml) 與 [schema.example.yaml](templates/schema.example.yaml) 依盤點結果增修 `specs/truth/contracts/` 的入口檔、路徑檔與 schema 檔。
4. DELEGATE 依 [check_openapi.py](scripts/check_openapi.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查契約的引用、入口檔的掛載、路徑檔的檔名與資料夾、每個操作的 `x-inner-needs` 與沒有被操作引用的檔案。
5. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對本 plan 動到的契約檔案是否整份符合憲法條款，並判斷腳本回報的問題是否與條款衝突。
6. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在依憲法改正會改變 PM 看得到的行為，或衝突的後續處理要由上游擁有者修正時，以 record 記錄。
7. WRITE 修正檢查與核對發現的問題。
8. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 record 把這次的異動記進 plan 的 `truth-changes.md` 並核對。

### Phase 4 --- 記錄結果

1. WRITE 回報這次的結果、產出、憲法核對結果與衝突，以及上游問題的位置、內容與應修正的擁有者。
2. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
3. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
