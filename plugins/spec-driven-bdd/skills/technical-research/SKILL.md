---
name: technical-research
description: 使用者已有功能規格書（spec.md），要依指定的技術方向做技術研究、產出研究紀錄（research.md）並更新技術堆疊（techstack.md），或 plan-package 列出本 skill 待補跑、`技術項.md` 有交給本 skill 修正的行（含技術修正 plan），或呼叫 /technical-research 時使用此 skill。功能規格交由 specify，plan 的狀態檢查與記錄交由 plan-package，truth 異動的盤點與紀錄交由 truth-changes，研究中發現的問題交由 dev-finding，介面文檔與任務拆解不在範圍內。
---

## SOP

### Phase 1 --- 釐清技術方向

1. READ 讀取使用者指定的技術方向。
2. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得待補跑與本 skill 的輸入差異，被拒絕時停止。
3. READ 讀取這個 plan 的 spec.md（技術修正 plan 沒有）、已有的 research.md、`技術項.md` 中「修正：technical-research」的行與 `specs/truth/techstack.md`。
4. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取 research.md 與 techstack.md 適用的憲法條款。
5. THINK 依 [串接規範](../plan-package/rules/串接規範.md) 在 check 回報本 skill 有紀錄且是待補跑，或目標是技術修正 plan 時，對列出的每個輸入差異判斷連帶異動或不受影響，只把連帶異動列為這次的範圍。
6. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）在技術方向存在會改變架構的缺口時釐清缺口，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。

### Phase 2 --- 研究技術決策

1. THINK 依 [議題盤點規範](rules/議題盤點規範.md) 從這次範圍內的 spec.md 的 FR、NFR、SC、使用者故事、邊界情況、技術項、技術方向與既有的技術堆疊盤點需要技術決策的議題。
2. THINK 依 [技術決策規範](rules/技術決策規範.md) 與憲法條款為每個議題在技術方向的限制內選定決策、版本、理由與替代方案。
3. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）在議題於限制內找不到可行做法時，詢問使用者是否調整限制，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。

### Phase 3 --- 撰寫研究紀錄

1. WRITE 依 [研究紀錄撰寫規範](rules/研究紀錄撰寫規範.md) 與憲法條款與 [research.md](templates/research.md) 與 [research.example.md](templates/research.example.md) 在需求 plan 或技術修正 plan 有研究決策時撰寫 plan 資料夾的 research.md。
2. DELEGATE 依 [check_research.py](scripts/check_research.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查 research.md 的 R 編號、對應需求與取代欄的引用、殘留佔位符，並列出未被引用的需求。
3. THINK 判斷這次範圍內未被引用的需求中哪些需要技術決策卻未被涵蓋。
4. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 research.md 是否符合憲法條款，並判斷腳本回報的問題是否與條款衝突。
5. WRITE 修正檢查與核對發現的問題。

### Phase 4 --- 更新技術堆疊

1. READ 在這次的決策取代已交付 plan 的決策時，以舊編號搜尋 `specs/truth/` 中引用它的位置。
2. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 inventory 帶入這次的決策與舊編號的引用（依差異判斷時另帶入輸入差異），盤點這次對 `specs/truth/techstack.md` 的新增、修改與刪除。
3. WRITE 依 [技術堆疊撰寫規範](rules/技術堆疊撰寫規範.md) 與憲法條款與 [techstack.md](templates/techstack.md) 與 [techstack.example.md](templates/techstack.example.md) 依盤點結果增修 `specs/truth/techstack.md`。
4. DELEGATE 依 [dev-finding](../dev-finding/SKILL.md) 在研究、盤點或增修中發現規格沒寫的行為或既有 truth 與程式不一致，或其他 truth 擁有者的檔案引用了被取代的舊編號時，以 record 記錄。
5. WRITE 在 dev-finding 回覆應由本 skill 修正時，依回覆增修 `specs/truth/techstack.md`。
6. DELEGATE 依 [check_techstack.py](scripts/check_techstack.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查 techstack.md 的 R 編號、技術類型、套件版本與各 plan 的 research.md 一致、重述的識別碼與殘留佔位符。
7. THINK 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 逐條核對 techstack.md 是否符合憲法條款，並判斷腳本回報的問題是否與條款衝突。
8. WRITE 修正檢查與核對發現的問題。

### Phase 5 --- 記錄結果

1. DELEGATE 依 [truth-changes](../truth-changes/SKILL.md) 以 record 把這次的異動記進 plan 的 `truth-changes.md` 並核對。
2. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在這次的結果是「不能改」時，列出擋住的規則、條款或上游事實與應交給的擁有者、使用者或 PM，不記錄並停止。
3. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 record 記錄這次的結果是「改了」或「不用改」。
