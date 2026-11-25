# Truth 異動紀錄：004-ranking

記錄這個 plan 對 truth 的新增（ADD）、修改（MOD）與刪除（DEL）。對象的路徑相對於 `specs/truth/`；原因是本 plan 的需求編號、開發發現的 AC 編號，或「技術：」加一句說明。

## technical-research（techstack.md）

| 異動 | 對象 | 改動摘要 | 原因 |
|---|---|---|---|
| 無異動 | — | — | 排行榜沿用既有的後端與資料庫技術，不需要新的技術 |

## api-plan（contracts/）

| 異動 | 對象 | 改動摘要 | 原因 |
|---|---|---|---|
| ADD | `contracts/paths/排行/api_rankings.yaml` | 新增查詢排行榜的操作，回傳前 10 名的暱稱與勝場數 | FR-001 |
| ADD | `contracts/components/schemas/RankingEntry.yaml` | 新增排行榜的一筆資料：名次、暱稱、勝場數 | FR-001 |
| MOD | `contracts/openapi.yaml` | 新增排行榜操作與 `RankingEntry` 的 `$ref`，移除連猜三次的 `$ref` | 技術：操作與 schema 必須掛進入口檔才會被打包 |
| MOD | `contracts/paths/房間/api_rooms_{roomId}_leave.yaml` | 新增「對局中不可離開房間」的回應 | AC-08 |
| MOD | `contracts/components/schemas/SkillCounts.yaml` | 刪除欄位 `tripleGuess`；`changeAnswer` 仍被改答案使用，保留 | FR-002 |
| DEL | `contracts/paths/技能/api_rooms_{roomId}_skills_triple-guess.yaml` | 刪除連猜三次的操作 | FR-002 |
| DEL | `contracts/components/schemas/TripleGuessRequest.yaml` | 只被連猜三次的操作使用，一併刪除 | FR-002 |

## data-plan（data/）

| 異動 | 對象 | 改動摘要 | 原因 |
|---|---|---|---|
| ADD | `data/排行.dbml` | 整份檔案，1 張資料表 `player_wins`（玩家暱稱、勝場數、最近獲勝時間） | FR-001 |
| MOD | `data/data-model.dbml` | 新增排行模組的引用 | 技術：模組檔必須由入口檔引用才會納入資料模型 |
| MOD | `data/對戰.dbml` ＞ Table `guesses` | 補上外鍵 `fk_guesses_room_id`（參照 `rooms.id`） | 技術：資料模型宣告的外鍵沒有建立 |
| DEL | `data/技能.dbml` ＞ Table `triple_guess_uses` | 刪除記錄連猜三次使用次數的資料表 | FR-002 |

## dsl-refine（features/）

| 異動 | 對象 | 改動摘要 | 原因 |
|---|---|---|---|
| ADD | `features/frontend/排行榜.feature` | 整份 feature，3 條 Rule | FR-001、NFR-001 |
| ADD | `features/backend/排行榜.feature` | 整份 feature，2 條 Rule | FR-001 |
| ADD | `features/backend/房間.feature` ＞ Rule「對局中的玩家不可離開房間」 | 新增一條 Rule，2 個 Example | AC-08 |
| MOD | `features/frontend/房間.feature` ＞ Rule「房間畫面必須顯示雙方的準備狀態」 | 畫面上方新增「排行榜」入口的斷言 | FR-001 |
| DEL | `features/frontend/技能.feature` ＞ Rule「連猜三次必須一次送出三組數字」 | 刪除整條 Rule | FR-002 |
| DEL | `features/backend/技能.feature` ＞ Rule「連猜三次必須依序回傳三筆結果」 | 刪除整條 Rule | FR-002 |
| MOD | `features/用語表.md` | 新增用語「排行榜」「勝場數」，刪除「連猜三次」 | FR-001、FR-002 |
