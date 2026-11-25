# 子 agent 委派規範

## Rule 1 -- 無法開啟 sub-agent 時必須停止

**強度：MUST**

有端點資料夾要依 Rule 2 開 sub-agent 時，委派前必須取得開 sub-agent 的工具；工具未直接列出時先查詢可延後載入的工具。確定無法開啟時停止並向使用者回報，不得改由主 agent 自己依序撰寫各端點的 feature 與 dsl.md。

### Good Example

這個範例先查詢工具，確定無法開啟後停止回報，讓使用者決定下一步。

```text
工具清單沒有 Agent，查詢延後載入的工具也找不到。
無法開啟 sub-agent，各端點無法同時產生。已完成：When 組分派、用語表與涵蓋表。
請確認要改為依序產生，或在支援 sub-agent 的環境重新執行。
```

### Bad Example

這個範例找不到工具就自己依序撰寫三個端點，使用者以為各端點是同時產生的，主 agent 的 context 也被三個端點的內容塞滿，後面的合併檢查容易出錯。

```text
找不到 Agent 工具，改由我依序撰寫 frontend、backend、database。
```

## Rule 2 -- 要寫 Rule 或 Example 的端點各一個 sub-agent 並同時開啟

**強度：MUST**

異動範圍有 Example 或步驟要新增、修改或刪除，或有 Rule 要新增或刪除的端點資料夾（例如 `frontend`、`backend`、`database`）各開一個 sub-agent，全部在同一則訊息中同時開啟。不得把兩個端點資料夾交給同一個 sub-agent，也不得等一個 sub-agent 回傳後才開下一個。其餘有異動的端點資料夾依 Rule 5 由主 agent 直接修改。

### Good Example

這個範例在同一則訊息為三個端點資料夾各開一個 sub-agent，各自只寫自己資料夾的 feature 與 dsl.md。

```text
同一則訊息：
- Agent（frontend：AC-01 第 1～4 組、AC-02 第 1～3 組、AC-03 第 1～2 組、補充 FR-003）
- Agent（backend：AC-01 第 1～4 組、AC-02 第 1～3 組、AC-03 第 1～2 組、補充 FR-003、FR-004）
- Agent（database：補充 NFR-003、NFR-013）
```

### Bad Example

這個範例依序開啟 sub-agent，各端點資料夾的產生時間相加，失去同時產生的意義，案例最多的端點也無法提早開始。

```text
開 Agent（frontend）→ 等回傳
開 Agent（backend）→ 等回傳
開 Agent（database）→ 等回傳
```

## Rule 3 -- 只處理異動範圍列出的 Rule 與 Example

**強度：MUST**

委派內容只能包含這次要新增、修改、刪除的 Rule、Example 與句型：盤點列出的異動（依差異判斷時就是判為連帶異動的項目），以及同一個 plan 再次執行時 diff 列出的新增、修改、刪除 AC 依涵蓋表對應的 Rule；不在異動範圍的 Rule、Example 與既有句型（包括先前的 plan 留下的）不得重寫。受影響的 Example 被使用者手改過時，sub-agent 不得覆蓋，必須列為增量衝突回傳，附上這次的變更與手改的內容。不在異動範圍的 Example 或句型被 check_features.py 檢查出違反規則時，sub-agent 與合併階段都不修正，列入待確認事項「依新規則待改寫」，附上 feature、Rule、Example 標題（句型則附 dsl.md 與句型）與檢查項目。使用者明確要求依新規則全部重寫時，委派範圍為全部 Rule，手改過的 Example 仍列為增量衝突。

### Good Example

這個範例只委派盤點列出的異動、變更的 AC-02 第 1 組與要修改的句型，把手改過的 Example 列為衝突，並把不在異動範圍但檢查不通過的 Example 與句型列為待改寫，不動它們。

```text
委派 backend：
- 盤點 ADD：排行榜.feature（整份，2 條 Rule）
- 盤點 MOD：技能特效.feature::使用技能後，雙方必須收到寫明技能名稱的特效（移除連猜三次的 Example）
- 盤點 DEL：連猜三次.feature（整份）
- 盤點 MOD：句型「雙方的技能剩餘次數如下：」（改測試寫法：`change_answer_left` 改以整數比較）
- 修改 AC-02 第 1 組（新答案由 1123 改為 12）→ 更新 改答案.feature::不符合四碼規則的新答案必須被拒絕::甲送出新答案 1123
- 手改過：改答案.feature::不符合四碼規則的新答案必須被拒絕::甲送出新答案 1123 → 不覆蓋，列為增量衝突
- 檢查不通過、不在異動範圍：改答案.feature::對手不能看到改答案的內容::甲送出新答案 4567（multi_when）、dsl.md 的句型「系統處於 {前置狀態}」（acceptance_refs）→ 不修正，列入待確認事項「依新規則待改寫」
其他 Rule、Example 與句型：不動
```

### Bad Example

這個範例依目前的 acceptance 重產整份後端，先前的 plan 留下的 Rule 被改寫成另一種說法，使用者手改過的 Example 也被覆蓋；truth 的異動紀錄會多出一堆這次的需求沒有要求的修改。

```text
委派 backend：依目前 acceptance 重新產生全部 AC 的 feature 與 dsl.md。
```

## Rule 4 -- 委派必須指定端點的樣板資料夾

**強度：MUST**

委派時必須指定該端點使用的樣板資料夾 `templates/<端點資料夾名稱>/`。plan.md 的前綴在 `templates/` 沒有同名資料夾時，改用測試方式最接近的一組（直接呼叫服務介面的端點用 `backend`，直接讀寫資料表的用 `database`，讀寫檔案或儲存區的用 `filesystem`，操作畫面的用 `frontend`），並在委派中寫明採用的資料夾與理由。委派中的樣板資料夾與 SKILL.md 必須寫成 dsl-refine 的 SKILL.md 實際所在目錄底下的絕對路徑，不得假設位於 `.claude/skills/`，因為 skill 可能由 plugin 安裝在專案外。

### Good Example

這個範例為 plan.md 中沒有對應樣板的訊息佇列端點，指定最接近的 backend 樣板並寫明理由。

```text
委派 queue：樣板資料夾 D:/plugins/spec-driven-bdd/skills/dsl-refine/templates/backend/（以服務介面發送與接收訊息，測試方式最接近後端 API）
```

### Bad Example

這個範例沒有指定樣板資料夾，sub-agent 自己挑了 frontend 的樣板，在佇列的 dsl.md 寫出「等待：畫面出現」這類用不到的欄位。

```text
委派 queue：依 templates/ 的樣板撰寫 feature 與 dsl.md
```

## Rule 5 -- 只改說明、註解與 Rule 名稱的端點資料夾由主 agent 直接修改

**強度：MUST**

端點資料夾的異動範圍沒有任何 Example 或步驟要新增、修改或刪除，也沒有 Rule 要新增或刪除，只改 dsl.md（既有句型的測試撰寫語意、參數說明、參數對照與 Step 檔對照，或合併步驟不用改的重複句型）、feature 的註解（含 `# 預設值：` 註解）或既有 Rule 的名稱時，由主 agent 依 Phase 3 的規範直接修改該端點資料夾並通過 check_features.py，不開 sub-agent，在回報的「模式」寫明這個端點資料夾由主 agent 直接修改。用語表本來就由主 agent 增修，不影響判定。異動範圍有任何 Example 或步驟要變動，或有 Rule 要新增或刪除時，依 Rule 2 開 sub-agent。以下 Example 皆對照此異動範圍：

```text
技術修正 plan 005-dsl-cleanup 的異動範圍：
- frontend/dsl.md：句型「系統處於 {前置狀態}」的測試撰寫語意刪去「技能剩餘次數由後端給定為各 1 次」（只改說明）
- frontend/dsl.md：「進入第 {數字} 輪，輪到玩家 {玩家} 猜測」併入「進入第 {輪次} 輪，輪到玩家 {玩家} 猜測」，feature 的步驟同時符合兩者，不用改
- backend/房間.feature：Rule「房間滿員時必須顯示「房間已滿」」改名為「房間滿員時再加入的玩家必須看到已滿的提示」，Example 不變
- database/猜測紀錄.feature：Rule「每輪的猜測紀錄必須依序編號」新增一個 Example
```

### Good Example

這個範例只為要新增 Example 的 database 開 sub-agent；frontend 只改 dsl.md、backend 只改 Rule 名稱，由主 agent 直接修改並各自通過檢查，回報寫明。

```text
主 agent 直接修改：
- frontend/dsl.md：起點句型的說明刪去次數；刪除「進入第 {數字} 輪，輪到玩家 {玩家} 猜測」一列，Step 檔對照只留保留的句型 → check_features.py 通過
- backend/房間.feature：Rule 改名，Example 不變 → check_features.py 通過
開 sub-agent：database（Rule「每輪的猜測紀錄必須依序編號」新增 1 個 Example）
回報的模式：技術修正 plan，依差異執行；frontend、backend 由主 agent 直接修改
```

### Bad Example

這個範例為三個端點資料夾都開 sub-agent；frontend 與 backend 的 sub-agent 都要先讀完委派簡報、各份規範與整份 dsl.md，只為刪改幾段說明與一個名稱，成本與改動不成比例。

```text
同一則訊息：
- Agent（frontend：起點句型的說明刪去次數、合併重複句型）
- Agent（backend：Rule「房間滿員時必須顯示「房間已滿」」改名）
- Agent（database：Rule「每輪的猜測紀錄必須依序編號」新增 1 個 Example）
```
