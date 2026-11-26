---
name: ui-direction
description: 使用者已有功能規格書（spec.md）與技術堆疊（techstack.md），功能涉及前端畫面，要在系統分析前決定或延伸專案的設計方向、產出 plan 的產品背景（`ui/PRODUCT.md`）並更新設計系統（`specs/truth/ui/DESIGN.md`），或 plan-package 列出本 skill 待補跑、`技術項.md` 有交給本 skill 修正的行，或呼叫 /ui-direction 時使用此 skill。視覺方向與設計系統的撰寫交由 ui-design，需求缺口交由 dev-finding，plan 的狀態檢查與記錄交由 plan-package，truth 異動的盤點與紀錄交由 truth-changes，UI 契約與原型交由 ui-ux-plan。
---

## SOP

### Phase 1 --- 讀取輸入

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
2. READ 讀取這個 plan 的 spec.md（技術修正 plan 沒有）、已存在的 plan.md 中的前端介面列、已有的 `ui/PRODUCT.md`、`技術項.md` 中「修正：ui-direction」的行、`specs/truth/techstack.md` 與 `specs/truth/ui/DESIGN.md`。
3. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 `ui/PRODUCT.md` 與 `specs/truth/ui/DESIGN.md` 適用的憲法條款。
4. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 與 [設計範圍判斷規範](rules/設計範圍判斷規範.md) 判斷這次要建立、延伸或取代設計方向，或只更新產品背景、不用改，依差異時只把連帶異動列為這次的範圍。
5. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 與 [設計範圍判斷規範](rules/設計範圍判斷規範.md) 在 spec.md 缺少會改變設計的使用者、使用情境或功能時，以 record 記錄。

### Phase 2 --- 決定設計方向

1. DELEGATE 使用 ui-design skill（可由 ui-studio plugin 提供，或為與本 skill 資料夾同層的 `ui-design` 資料夾）在這次範圍需要產品背景或設計方向時，以 spec.md、憲法條款與 techstack.md 為產品背景、plan 的 `ui/PRODUCT.md` 為產品背景的位置、`specs/truth/ui/DESIGN.md` 為既有視覺世界，以決定設計方向為範圍（含搜尋參考候選與選定素材來源），兩者都沒有時不得自行代替，停止並請使用者安裝 ui-studio plugin，agent 不支援 plugin 時改為把 `ui-design` 與 `ui-assets` 資料夾複製到同層。
2. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 inventory 帶入這次決定的設計方向（依差異判斷時另帶入輸入差異），盤點這次對 `specs/truth/ui/DESIGN.md`、`tokens.css` 與 `tokens.json` 的新增、修改與刪除。
3. DELEGATE 使用 ui-design skill（可由 ui-studio plugin 提供，或為與本 skill 資料夾同層的 `ui-design` 資料夾）依盤點結果與這次決定的設計方向，以 `specs/truth/ui/DESIGN.md` 為設計系統的位置、`specs/truth/ui/` 為 tokens 的輸出資料夾，以撰寫設計系統為範圍，兩者都沒有時不得自行代替，停止並請使用者安裝 ui-studio plugin，agent 不支援 plugin 時改為把 `ui-design` 與 `ui-assets` 資料夾複製到同層。
4. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 `ui/PRODUCT.md` 與 `specs/truth/ui/DESIGN.md` 是否符合憲法條款。
5. WRITE 修正核對發現的問題，改到 `specs/truth/ui/DESIGN.md` 時回到 Step 3 重新撰寫設計系統並轉出 tokens。

### Phase 3 --- 記錄結果

1. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 record 把這次的異動記進 plan 的 `truth-changes.md` 並核對。
2. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
3. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
