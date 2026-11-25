---
name: constitution
description: 使用者要為專案訂立或增修憲法（`.claude/constitution/`），約束 SDD 流程中各 skill 產出物的內容與格式，或呼叫 /constitution 時使用此 skill。修改 skill 本身的內建 Rule 交由 skill-engineering，產物間的一致性檢查交由 analyze。
---

## SOP

### Phase 1 --- 釐清需求

1. READ 讀取使用者這次的憲法需求與 `.claude/constitution/` 既有的憲法（存在時）。
2. THINK 依 [增量範圍判斷規範](rules/增量範圍判斷規範.md) 判斷需求涉及的產出物與作用位置，以及與既有條款的重複或衝突。
3. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）在涉及的產出物、作用位置、強度、條款內容或起因需求（使用者遇到的問題）存在缺口時，只針對這些缺口訪談使用者，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。

### Phase 2 --- 撰寫條款

1. READ 讀取涉及產出物的產出 skill 的樣板與 `rules/`。
2. THINK 依 [條款落點判斷規範](rules/條款落點判斷規範.md) 判斷每條條款寫入產出物條款檔或共通條款檔，並決定條款 ID。
3. WRITE 依 [條款撰寫規範](rules/條款撰寫規範.md) 與 [product-clauses.md](templates/product-clauses.md) 與 [product-clauses.example.md](templates/product-clauses.example.md) 撰寫或修改 `.claude/constitution/skills/<產出 skill>/<產出物>.md`。
4. WRITE 依 [條款撰寫規範](rules/條款撰寫規範.md) 與 [shared-clauses.md](templates/shared-clauses.md) 與 [shared-clauses.example.md](templates/shared-clauses.example.md) 在需要共通條款時撰寫或修改 `.claude/constitution/shared/<主題>.md`。
5. WRITE 依 [目錄與版本更新規範](rules/目錄與版本更新規範.md) 與 [constitution-index.md](templates/constitution-index.md) 與 [constitution-index.example.md](templates/constitution-index.example.md) 更新 `.claude/constitution/CONSTITUTION.md` 的目錄、版本與修訂紀錄。

### Phase 3 --- 檢查與回報

1. DELEGATE 依 [check_constitution.py](scripts/check_constitution.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查目錄連結、產出物欄的寫法、條款 ID、共通條款引用與版本紀錄的一致性。
2. THINK 依 [憲法套用規範](rules/憲法套用規範.md) 與 [條款撰寫規範](rules/條款撰寫規範.md) 逐條核對本次異動的條款：下游 skill 依目錄的「產出物」欄載入得到它與它引用的共通條款，它的每個作用位置都對得到產出 skill 樣板中的位置，列為覆寫對象的 Rule 確實無法與它同時遵守。
3. WRITE 修正檢查與核對發現的問題。
4. WRITE 回報本次異動的檔案、條款、版本與未執行的建議。
