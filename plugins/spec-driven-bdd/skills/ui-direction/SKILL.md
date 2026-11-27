---
name: ui-direction
description: 使用者已有功能規格書（spec.md）與技術堆疊（techstack.md），功能涉及前端畫面，要在系統分析前決定或延伸專案的設計方向、更新產品背景（`specs/truth/ui/PRODUCT.md`）與設計系統（`specs/truth/ui/DESIGN.md`），或 plan-package 列出本 skill 待補跑、`技術項.md` 有交給本 skill 修正的行，或呼叫 /ui-direction 時使用此 skill。視覺方向、產品背景與設計系統的撰寫交由 ui-design，需求缺口交由 dev-finding，plan 的狀態檢查與記錄交由 plan-package，truth 異動的盤點與紀錄交由 truth-changes，UI 契約與原型交由 ui-ux-plan。
---

## SOP

### Phase 1 --- 讀取輸入

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
2. READ 讀取這個 plan 的 spec.md（技術修正 plan 沒有）、已存在的 plan.md 中的前端介面列、已有的 `ui/設計方向.md` 與 `ui/方向候選.json`、`技術項.md` 中「修正：ui-direction」的行、`specs/truth/techstack.md`、`specs/truth/ui/PRODUCT.md` 與 `specs/truth/ui/DESIGN.md`。
3. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 `ui/設計方向.md`、`specs/truth/ui/PRODUCT.md` 與 `specs/truth/ui/DESIGN.md` 適用的憲法條款。
4. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 與 [設計範圍判斷規範](rules/設計範圍判斷規範.md) 判斷這次設計方向要建立、延伸、取代或不用改，以及產品背景要新增、修改、刪除的節，依差異時只把連帶異動列為這次的範圍。
5. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 與 [設計範圍判斷規範](rules/設計範圍判斷規範.md) 在 spec.md 缺少會改變設計的使用者、使用情境或功能時，以 record 記錄。

### Phase 2 --- 決定設計方向

1. DELEGATE 使用 ui-design skill（可由 ui-studio plugin 提供，或為與本 skill 資料夾同層的 `ui-design` 資料夾）在這次範圍需要產品背景或設計方向時，以 Step 4 判斷的設計方向範圍與產品背景異動、spec.md、憲法條款與 techstack.md 為產品背景的來源、`specs/truth/ui/PRODUCT.md` 為既有產品背景、`specs/truth/ui/DESIGN.md` 為既有視覺世界、plan 資料夾的 `ui/` 為選擇頁位置，並帶入使用者對選擇頁的回覆（有時），以決定設計方向為範圍（含搜尋參考候選、擲骰、選擇頁與選定素材來源），兩者都沒有時不得自行代替，停止並請使用者安裝 ui-studio plugin，agent 不支援 plugin 時改為把 `ui-design` 與 `ui-assets` 資料夾複製到同層。
2. ASK 在 ui-design 回報方向尚未選定時，請使用者開啟回報的選擇頁，把選定後頁面複製的文字貼回並重新執行本 skill，並停止。
3. WRITE 依 [設計方向紀錄規範](rules/設計方向紀錄規範.md) 與憲法條款與 [設計方向.md](templates/設計方向.md) 與 [設計方向.example.md](templates/設計方向.example.md) 在 ui-design 回報這次建立或取代設計方向時，依回報撰寫 plan 資料夾的 `ui/設計方向.md`。

### Phase 3 --- 更新產品背景與設計系統

1. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 在這次有產品背景異動或設計系統值異動時，以 inventory 帶入產品背景異動與決定的設計方向（依差異判斷時另帶入輸入差異），盤點這次對 `specs/truth/ui/PRODUCT.md`、`specs/truth/ui/DESIGN.md`、`tokens.css` 與 `tokens.json` 的新增、修改與刪除。
2. DELEGATE 使用 ui-design skill（可由 ui-studio plugin 提供，或為與本 skill 資料夾同層的 `ui-design` 資料夾）在盤點有異動時，依盤點結果、產品背景異動與決定的設計方向，以 `specs/truth/ui/PRODUCT.md` 為產品背景的位置、`specs/truth/ui/DESIGN.md` 為設計系統的位置、`specs/truth/ui/` 為 tokens 的輸出資料夾，以撰寫設計系統為範圍，兩者都沒有時不得自行代替，停止並請使用者安裝 ui-studio plugin，agent 不支援 plugin 時改為把 `ui-design` 與 `ui-assets` 資料夾複製到同層。
3. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 `ui/設計方向.md`、`specs/truth/ui/PRODUCT.md` 與 `specs/truth/ui/DESIGN.md` 是否符合憲法條款。
4. WRITE 修正核對發現的問題，改變設計方向時回到 Phase 2 Step 1，改到 `specs/truth/ui/PRODUCT.md` 或 `specs/truth/ui/DESIGN.md` 時回到 Step 2。

### Phase 4 --- 記錄結果

1. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 record 把這次的異動以 `ui/` 為本 skill 的路徑記進 plan 的 `truth-changes.md` 並核對。
2. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
3. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
