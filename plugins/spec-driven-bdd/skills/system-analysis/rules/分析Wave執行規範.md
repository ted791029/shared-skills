# 分析 Wave 執行規範

## Rule 1 -- Wave 依序執行範圍內的端點，同一個 Wave 並行

**強度：MUST**

必須依 plan.md 的 Wave 編號由小到大執行這次範圍內的端點（完整流程為全部端點，依差異時範圍外的端點不重跑），前一個 Wave 的所有 sub-agent 完成並通過產出確認後，才能開始下一個 Wave。同一個 Wave 必須為範圍內的每個端點各開一個 sub-agent 並行執行，每個 sub-agent 只呼叫依介面 ID 前綴對照出的 Planner，呼叫參數固定為 `plan.md` 路徑、Wave 編號與端點名稱；範圍內沒有排進 Wave 的端點排在所有 Wave 之後，Wave 編號寫「無」。

### Good Example

這個範例在完整流程的 Wave 3 同時開兩個 sub-agent；依差異時只重跑範圍內的後端，沒有排進 Wave 的資料庫端排在最後、Wave 編號寫「無」，每個 sub-agent 都帶入固定的呼叫參數。

```text
完整流程 Wave 3（並行）：
- sub-agent 1 → data-plan：specs/plans/001-photo-album-organizer/plan.md、Wave 3、資料庫端
- sub-agent 2 → storage-plan：specs/plans/001-photo-album-organizer/plan.md、Wave 3、檔案系統端

依差異（範圍：後端、沒有排進 Wave 的資料庫端）：
- Wave 1 前端不在範圍，不重跑
- Wave 2 → sub-agent → api-plan：specs/plans/004-chat-pin/plan.md、Wave 2、後端
- 最後 → sub-agent → data-plan：specs/plans/004-chat-pin/plan.md、Wave 無、資料庫端
```

### Bad Example

這個範例在 Wave 2 尚未完成時就開始 Wave 3，data-plan 讀不到後端這次的契約，只能自行猜測 API 需要的欄位。

```text
Wave 2 → api-plan（執行中）
Wave 3 → data-plan、storage-plan（同時開始）
```

## Rule 2 -- 以本次回傳確認產出，不齊全時停止

**強度：MUST**

每個 Wave 結束後，必須以本次每個 sub-agent 的回傳確認結果與產出：回傳寫出這次的結果（改了、不用改或不能改）、產出與 Planner 的憲法核對結果；結果為改了或不用改時，該 Planner 的 SKILL.md 撰寫產出的 Step 寫明的每份文檔都在它寫明的位置；沒有排進 Wave（Wave 為「無」）而結果為不用改的 Planner 不產出文檔，只確認回傳，寫進 truth 的 Planner 另確認它的一節。寫在 plan 資料夾的文檔必須存在；寫進 `specs/truth/` 的文檔以 plan 的 `truth-changes.md` 確認，該 Planner 的一節必須已有紀錄（異動的列，或一列「無異動」）。執行前就已存在的檔案與檢查腳本通過，都不能作為 Planner 已執行的證據。缺少回傳、有文檔缺漏、truth 的異動沒有紀錄或 sub-agent 回報失敗時，必須停止執行並回報缺漏的 Planner 與文檔，不得進入下一個 Wave，也不得自行補寫 Planner 的產出。結果為不能改時依 Rule 3 與 Rule 4 處理。

### Good Example

這個範例以 sub-agent 的回傳逐項確認，發現回傳缺少原型目錄後停止，沒有進入 Wave 2。

```text
Wave 1 確認：ui-ux-plan 寫明 plan 資料夾的 ui/ui-contract.md、ui/prototype/
- 回傳結果：改了；產出：ui/ui-contract.md；憲法核對：無適用條款
- 回傳沒有 ui/prototype/ → 停止，回報 ui-ux-plan 未產出 ui/prototype/
```

### Bad Example

這個範例沒有回傳可依據，只因 truth 中已有資料模型就判定完成；那是先前的 plan 留下的內容，`truth-changes.md` 也沒有 data-plan 的紀錄，本次 Planner 是否執行、改了什麼都無從得知。

```text
Wave 3 確認：specs/truth/data/ 已有資料模型、check_dbml.py 通過 → data-plan 完成，繼續下一個 Wave
```

## Rule 3 -- 上游問題在 Wave 結束後修正一次

**強度：MUST**

Planner 只回報上游問題，不修改 plan.md 或其他擁有者的產出；執行 Wave 期間，system-analysis 也不得修改 plan.md 或任何 Planner skill。同一個 Wave 的 sub-agent 全部回傳後，才處理回傳中的上游問題（不論該 Planner 的結果是改了或不能改），system-analysis 自己在執行中發現 plan.md 有誤時也一樣：問題在 plan.md 時，指向同一個介面列或 Wave 的回報合併成一次修正，依差異只修正那些節並通過 check_plan.py 與憲法核對；問題在前置 Wave 端點的產出時不改 plan.md，把回報交給該端點的 Planner 重跑。之後只重跑依差異判定的端點，再進入下一個 Wave。Planner 的產出不符其樣板時，必須停止並建議使用者以 skill-engineering（可由 skill-workshop plugin 提供，或為同層的 `skill-engineering` 資料夾） 優化該 Planner。憲法衝突依 Rule 4 處理。

### Good Example

這個範例等 Wave 3 兩個並行的 Planner 都回傳後，把指向同一列的兩則回報合併，plan.md 只修正一次，再依序重跑受影響的後端與兩個回報的端點。

```text
Wave 3 回傳：
- data-plan：不能改，API-03 的依據需求缺 FR-017（刪除照片），契約沒有刪除操作，照片列的刪除無從設計
- storage-plan：不能改，API-03 的依據需求缺 FR-017，契約沒有刪除操作，原始檔的刪除連動無從設計
處理：兩則回報指向 API-03 → plan.md 的 API-03 依據需求補上 FR-017 一次 → check_plan.py 0 個問題
重跑：Wave 2 api-plan（API-03 屬後端）改了，新增刪除照片的操作 → Wave 3 data-plan、storage-plan 再判斷，皆改了
```

### Bad Example

這個範例讓兩個 Planner 各自在自己的 sub-agent 修改 plan.md，API-03 變成「FR-010、FR-017、FR-017」，修改沒有經過 check_plan.py；後端也沒有重跑，契約仍沒有刪除照片的操作，兩個 Planner 各自依想像的刪除操作設計連動。

```text
data-plan：在 plan.md 的 API-03 加上 FR-017，繼續設計照片列的刪除
storage-plan：在 plan.md 的 API-03 加上 FR-017，繼續設計原始檔的刪除連動
→ Wave 3 完成
```

## Rule 4 -- 憲法衝突能化解才繼續，不能改時停止 Wave

**強度：MUST**

Planner 依憲法套用規範處理的衝突分兩種。照條款撰寫後 PM 核准的需求（AC、FR 或 NFR）要的行為不變、Planner 依條款撰寫了產出（結果為改了或不用改）時，不屬於停止條件：保留它依條款撰寫的產出，把它依憲法套用規範 Rule 8 回報的每項衝突逐列記入 wave-report.md 的「憲法衝突」段後繼續。衝突的輸入文件是 plan.md 或前置端點的產出時依 Rule 3 處理；是其他上游擁有者的產物（例如 research.md、spec.md）時，必須以 dev-finding 記成技術項並寫上「修正：<擁有者>」，後續處理寫出已記成技術項，不得只留在報告裡。Planner 依憲法套用規範 Rule 7，因與 PM 核准的 AC 或需求衝突、無法同時符合而回傳不能改時，這個 Wave 算未完成：不得把衝突記下後繼續，也不得執行後續的 Wave，必須把該端點寫成「不能改」，在「不能改」段寫出擋住的條款與 AC 或需求，以及要做決定的使用者或 PM（修改 AC、需求，或修訂條款）。Planner 因其他規則，或 plan.md 與前置端點產出以外的上游事實而回傳不能改時，同樣停止，並在「不能改」段寫出應修正的擁有者。Planner 回傳不能改時，system-analysis 自己的結果依它自己的產出判定：plan.md 與 wave-report.md 都正確時以改了或不用改記錄，擋住的 Planner 沒有記錄、維持待補跑，之後以依差異入口只重跑它。

### Good Example

這個範例中 data-plan 照條款撰寫後使用者看到的行為不變，上游的研究決策經 dev-finding 記成技術項、衝突記入「憲法衝突」段後繼續；另一次執行的 api-plan 無法在不違反 AC-12 的前提下化解而回傳不能改，Wave 停止並交給 PM 決定。

```text
Wave 3 data-plan 回傳：改了；techstack.md「資料庫」列引用的 001/R-03 決定「主鍵使用自動遞增整數」，與 C-DATA-02 衝突 → 主鍵已改為 UUID，使用者看到的行為不變
→ 以 dev-finding 記成技術項：- 001/R-03 的主鍵使用自動遞增整數，與 C-DATA-02 衝突（data-plan；001 的 research.md R-03 與憲法 C-DATA-02；修正：technical-research）
→ 記入「憲法衝突」：資料庫端 | 001 的 research.md R-03 | 主鍵使用自動遞增整數 | C-DATA-02 | 各表主鍵改為 UUID | 已記成技術項（修正：technical-research）；001 已交付，由 technical-research 在本 plan 新增決策取代 001/R-03
→ 繼續下一個 Wave

Wave 2 api-plan 回傳：不能改；AC-12「聊天室一次列出全部訊息」與 C-API-03「列表 API 必須分頁」衝突，無法在不違反 AC-12 的前提下化解
→ wave-report：後端寫「不能改」，Wave 3 資料庫端寫「未執行」
→ 記入「不能改」：後端 | C-API-03 要求列表分頁，AC-12 要求一次列出全部訊息 | PM 決定以 spec-by-example 修改 AC-12，或由使用者以 constitution 修訂 C-API-03
→ 不執行 Wave 3
```

### Bad Example

這個範例把 api-plan 的不能改當成一般衝突記下後繼續，PM 還沒決定，data-plan 就依沒有分頁的契約設計了資料表與索引，下游建立在違反條款的設計上，wave-report 也看不出這個 Wave 沒有完成。

```text
Wave 2 api-plan 回傳：不能改；AC-12 與 C-API-03 衝突
→ 記入「憲法衝突」：後端 | acceptance AC-12 | 一次列出全部訊息 | C-API-03 | 暫不分頁 | PM 決定
→ 後端寫「完成」，繼續 Wave 3 data-plan
```

## Rule 5 -- wave-report 只依回傳填寫

**強度：MUST**

wave-report.md 每個端點的產出與狀態只能取自該端點 sub-agent 的回傳。狀態只能是「完成」（結果為改了或不用改，且通過 Rule 2 的確認）、「不能改」（結果為不能改）、「未完成」（回報失敗或沒有通過 Rule 2 的確認）或「未執行」（沒有回傳，或因停止而沒有執行）。產出欄中，寫在 plan 資料夾的文檔列出路徑，寫進 truth 的異動只寫位置與新增、修改、刪除各幾列，並指向 `truth-changes.md` 中該 Planner 的一節，不重抄異動內容，沒有產出時寫「—」；沒有排進 Wave 的端點，Wave 欄寫「無」。依差異時只改這次重跑的端點的列，其他列保留；沒有執行任何 Planner 時不改 wave-report.md。不得加入樣板以外的欄位，也不得寫出回傳中沒有的合憲結論；沒有不能改的端點時省略「不能改」段，所有 Planner 都沒有回報衝突時省略「憲法衝突」段。

### Good Example

這個範例依回傳填寫，truth 的異動只寫列數並指向 truth-changes.md，這次重跑的後端與沒有排進 Wave、Wave 欄寫「無」的資料庫端更新了列，沒有重跑的 Wave 1 保留上次的列。

```markdown
| Wave | 端點 | Planner | 產出 | 狀態 |
|---|---|---|---|---|
| 1 | 前端 | `ui-ux-plan` | `ui/ui-contract.md`、`ui/prototype/` | 完成 |
| 2 | 後端 | `api-plan` | `specs/truth/contracts/`：新增 0、修改 2、刪除 0，見 truth-changes.md 的 api-plan 一節 | 完成 |
| 無 | 資料庫端 | `data-plan` | `specs/truth/data/`：新增 0、修改 0、刪除 0，見 truth-changes.md 的 data-plan 一節 | 完成 |
```

### Bad Example

這個範例沒有 data-plan 的回傳，卻自行在 wave-report 加上「憲法」欄宣稱符合條款，使用者會誤以為產出已經過 Planner 核對。

```text
| 3 | 資料庫端 | `data-plan` | `specs/truth/data/`：新增 1、修改 1、刪除 0，見 truth-changes.md 的 data-plan 一節 | 完成 | 符合 C-DATA-02 |
```

## Rule 6 -- 委派必須由 sub-agent 完整執行 Planner

**強度：MUST**

委派是指由 sub-agent 讀取並完整執行 Planner 的 SKILL.md，並回傳這次的結果（改了、不用改或不能改）、產出（plan 資料夾中的文檔路徑，以及寫進 truth 的新增、修改、刪除各幾列）、Planner 對產出的憲法核對結果、回報的衝突與上游問題；Planner 的記錄由 sub-agent 照 Planner 的 SKILL.md 自己完成，system-analysis 不得替 Planner 記錄。執行 system-analysis 的 agent 自行讀取 Planner 的 SKILL.md、規範或樣板後撰寫產出，不算委派，一律不得為之；功能為前一功能的增量、改動小或使用者要求一次做完，都不構成例外。可用工具中沒有直接列出開 sub-agent 的工具時，必須先查詢可動態取得的工具；確定無法開 sub-agent 時，必須停止並回報，請使用者改在支援 sub-agent 的環境執行。

### Good Example

這個範例的功能是前一功能的增量，工具清單也沒有列出 sub-agent 工具，仍先查詢取得後開 sub-agent，由 sub-agent 完整執行 Planner 並自己記錄，回傳結果、產出、核對結果、衝突與上游問題。

```text
工具清單無 sub-agent 工具 → 查詢可動態取得的工具 → 取得 Task
Wave 3 → sub-agent：完整執行 data-plan 的 SKILL.md（plan.md、Wave 3、資料庫端，含它自己的記錄），回傳結果、產出、憲法核對結果、衝突與上游問題
```

### Bad Example

這個範例以「只是增量、一次寫完較快」為由，讀了 Planner 的 SKILL.md 開頭就自行撰寫產出並替它記錄，Planner 的規範、樣板、truth 異動的盤點與紀錄、憲法核對都沒有執行，產出違反憲法條款，wave-report 與串接紀錄卻都把 Planner 列為已執行。

```text
增量功能 → 讀 data-plan SKILL.md 前 40 行 → 自行修改 specs/truth/data/ → check_dbml.py 通過 → 替 data-plan 記錄改了 → wave-report 寫 data-plan 完成
```
