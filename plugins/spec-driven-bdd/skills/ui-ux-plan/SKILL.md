---
name: ui-ux-plan
description: 執行 plan.md 分析 Wave 中前端（介面 ID 前綴 UI）的分析，或 plan-package 列出本 skill 待補跑、`技術項.md` 或 dev-finding 的回覆交給本 skill 修正（例如補上 dsl-refine 擬定的 testid，含技術修正 plan），或呼叫 /ui-ux-plan 時使用此 skill。plan.md 的介面列與 Wave 由 system-analysis 修正，本 skill 只回報；設計方向與設計系統交由 ui-direction，原型的視覺設計交由 ui-design，端點 feature 與 dsl.md 交由 dsl-refine。
---

## SOP

### Phase 1 --- 讀取輸入

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
2. READ 讀取呼叫參數指定的 plan.md（技術修正 plan 沒有）中的共用輸入、所屬端點的介面列與該 Wave 的分析重點（Wave 為「無」時沒有）、`features/acceptance/` 中涵蓋這些介面列依據需求的 AC、`技術項.md` 中「修正：ui-ux-plan」的行，以及 `ui/PRODUCT.md` 與 `specs/truth/ui/DESIGN.md`。
3. READ 依 [Planner 配對規範](../planner-provisioning/rules/Planner配對規範.md) 找到「相依」列出的前置端點的 Planner，讀取它這次的產出。
4. READ 依 [介面取代規範](rules/介面取代規範.md) 讀取介面列中異動為 MOD 或 DEL 的介面與技術項指出的介面在先前 plan 的 `ui/ui-contract.md` 中最近一次的描述。
5. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 `ui/ui-contract.md` 與 `ui/prototype/` 適用的憲法條款。
6. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 與 [依差異判斷規範](rules/依差異判斷規範.md) 在 check 回報本 skill 有紀錄且是待補跑、本 skill 沒有排進 Wave、目標是技術修正 plan 或被交辦修正時，對列出的每個輸入差異或交辦內容判斷連帶異動或不受影響，只把連帶異動列為這次的範圍。

### Phase 2 --- 分析介面

1. THINK 依 [UI 分析規範](rules/UI分析規範.md) 與憲法條款從這次範圍內的介面列、分析重點、涵蓋的 AC、前置產出與技術項推導每個介面的操作、狀態、文案、定位與需要內層提供的資料與動作。
2. READ 依 [介面取代規範](rules/介面取代規範.md) 在介面列有 MOD 或 DEL 時，以被修改介面的介面 ID 搜尋 `specs/truth/` 與本 plan 資料夾中引用它的位置。
3. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在分析中發現規格沒寫的行為，或其他擁有者的檔案與 UI 契約不一致（例如引用了這次改變或移除的部分）時，以 record 記錄。

### Phase 3 --- 撰寫產出

1. WRITE 依憲法條款與 [ui-contract.md](templates/ui-contract.md) 與 [ui-contract.example.md](templates/ui-contract.example.md) 在 plan 資料夾撰寫 `ui/ui-contract.md`。
2. DELEGATE 使用 ui-design skill（可由 ui-studio plugin 提供，或為與本 skill 資料夾同層的 `ui-design` 資料夾）在這次範圍有新增的頁面或畫面有變動的修改頁面時，以 `ui/ui-contract.md`、`ui/PRODUCT.md`、`specs/truth/ui/DESIGN.md`、憲法條款、[UI 分析規範](rules/UI分析規範.md) 的原型要求與 [index.html](templates/prototype.example/index.html) 與 [album.html](templates/prototype.example/album.html) 與 [states.html](templates/prototype.example/states.html) 的結構為依據，以撰寫原型與檢查為範圍、不可詢問的方式，tokens 取自 `specs/truth/ui/tokens.css`、素材位置為 `ui/prototype/assets/`、素材清單為 `ui/prototype/素材清單.md`、截圖放在系統暫存，在 plan 資料夾的 `ui/prototype/` 為每個頁面撰寫 HTML 原型與 `states.html` 狀態入口，並在 `ui/檢查報告.md` 撰寫檢查報告，兩者都沒有時不得自行代替，停止並請使用者安裝 ui-studio plugin，agent 不支援 plugin 時改為把 `ui-design` 與 `ui-assets` 資料夾複製到同層。
3. WRITE 依 [UI 分析規範](rules/UI分析規範.md) 在這次只為既有元素補上定位時，直接在原型的同一元素加上 `data-testid`。
4. THINK 依 [UI 分析規範](rules/UI分析規範.md) 逐頁核對 `ui/prototype/` 與 `ui/ui-contract.md` 的頁面、操作、狀態、文案與定位是否一致。
5. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 `ui/ui-contract.md` 是否符合憲法條款。
6. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 `ui/prototype/` 的每個 HTML 是否符合憲法條款。
7. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在依憲法改正會改變 PM 看得到的行為，或衝突的後續處理要由上游擁有者修正時，以 record 記錄。
8. WRITE 修正核對發現的問題。
9. DELEGATE 使用 ui-design skill（可由 ui-studio plugin 提供，或為與本 skill 資料夾同層的 `ui-design` 資料夾）在 Step 8 改到原型時，以只實測與檢查為範圍、不可詢問的方式重新實測 `ui/prototype/` 並更新 `ui/檢查報告.md`，兩者都沒有時不得自行代替，停止並請使用者安裝 ui-studio plugin，agent 不支援 plugin 時改為把 `ui-design` 與 `ui-assets` 資料夾複製到同層。

### Phase 4 --- 記錄結果

1. WRITE 回報這次的結果、產出、憲法核對結果與衝突，以及上游問題的位置、內容與應修正的擁有者。
2. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
3. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
