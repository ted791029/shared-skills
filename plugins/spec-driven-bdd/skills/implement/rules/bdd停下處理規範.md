# bdd 停下處理規範

## Rule 1 -- bdd 停下即停止執行

**強度：MUST**

bdd 回報停下（含 `[驗證]` 的 `/bdd verify` 回報回歸），或結束時沒有回報該階段已完成時，除符合 Rule 2 與 Rule 5 的自動重試外，implement 必須停止執行：不得把該任務勾為 `[X]`、不得繼續下一個任務、不得改用其他 subcommand 或範疇重新呼叫 bdd，也不得自行修改 feature、dsl.md、`specs/truth/features/用語表.md`、測試設定、step definitions、Driver 或產品程式來排除停下原因。bdd 停下的情況以 bdd 的停下回報規範為準，包含 feature、dsl.md 或用語表有問題（含 dsl.md 與介面文檔矛盾）、失敗原因是其他端點尚未實作（red、green、refactor 皆是）、green 範疇內出現測試程式錯誤、rerun 判定既有 step 需要改、測試環境或測試設定未就緒、進入條件不成立、階段結尾任務驗證出現本階段不可修正的回歸、verify 出現回歸，以及 verify 結果有未執行或無法對應的 Example。

### Good Example

這個範例在 bdd 因測試資料庫無法連線停下後，T008 保持未勾選，沒有執行下一個任務，直接依停止回報樣板回報。

```text
T008 [紅燈] → /bdd red specs/truth/features/backend/改答案.feature
bdd 停下：測試環境未就緒，MySQL 127.0.0.1:3307 Connection refused（backend/.env 的 DATABASE_URL）
處理：T008 維持 [ ]，不執行 T009，依停止回報樣板回報
```

### Bad Example

這個範例在 bdd 停下後改把範疇縮小到不需要資料庫的 Rule 重新呼叫 bdd，再勾選 T008；feature 其他 Rule 從未進入紅燈，T009 綠燈的進入條件不成立，bdd 又會停下。

```text
bdd 停下：MySQL 127.0.0.1:3307 Connection refused
處理：改呼叫 /bdd red specs/truth/features/backend/改答案.feature:8 → 仍停下 → 跳過，T008 勾為 [X]，繼續 T009
```

## Rule 2 -- green 測試程式錯誤時重試一次

**強度：MUST**

bdd green 停下的類別是測試程式錯誤，且建議先對同一範疇執行 `/bdd red` 時，implement 不得停下，必須以該綠燈任務的範疇原文與同一份 Phase 標頭依序委派 `/bdd red <範疇>` 與 `/bdd green <範疇>` 各一次：red 回報完成才委派 green，green 回報完成即照一般流程勾選該綠燈任務。重試的 red 停下，或重試的 green 再次停下（不論類別）時，不得再重試，依 Rule 1 停止，停止回報的對照原文依序列出第一次 green、重試 red、重試 green 的停下或完成說明。重試期間 implement 不得自行修改測試程式、產品程式或規格，也不得變更同範疇紅燈任務的勾選狀態。其他停下類別，以及 red、refactor 的停下，一律不重試。

### Good Example

這個範例在 T012 綠燈因 red 時沒執行到的 step 才暴露 selector 錯誤而停下後，以同一範疇重跑 red 再重跑 green，green 完成後勾選 T012，T011 的勾選狀態不變。

```text
T012 [綠燈] → /bdd green specs/truth/features/frontend/改答案.feature（附 Phase 5 標頭）
bdd 停下：測試程式錯誤，frontend/tests/e2e/steps/modules/技能/改答案.js:42「"乙" 的畫面顯示提示 {提示}」getByTestId('skill-hint') 逾時找不到元素；建議先執行 /bdd red specs/truth/features/frontend/改答案.feature 修正測試程式，再執行 /bdd green
重試：/bdd red specs/truth/features/frontend/改答案.feature → red 完成
重試：/bdd green specs/truth/features/frontend/改答案.feature → green 完成 → T012 勾為 [X]（T011 維持 [X]）
```

### Bad Example

這個範例由 implement 自己改 step 的 selector 後反覆重跑 green，改過的 step 沒有經過 bdd 依 dsl.md 比對測試撰寫語意，也沒有確認紅燈，selector 可能被改成任何會通過的元素，而重跑沒有上限，錯誤持續時會一直循環。

```text
bdd 停下：測試程式錯誤，改答案.js:42 getByTestId('skill-hint') 逾時；建議先執行 /bdd red …/frontend/改答案.feature
處理：把 改答案.js:42 改成 getByText('房主使用了改答案') → /bdd green … → 仍停下 → 再改 → /bdd green … → 仍停下 → …
```

## Rule 3 -- 停下說明照錄並寫出交辦對象

**強度：MUST**

停止回報的「對照原文」必須照錄 bdd 停下說明中的位置（`檔案:行號`）與原文，「停止原因」寫 bdd 的停下類別與問題說明，「交辦對象」與「建議下一步」依下表決定；bdd 已寫出建議下一步時照錄，再補上回到 implement 的指令。bdd 建議委派 dev-finding 時，交辦對象取 dev-finding 的 record 回覆寫明的應修正的擁有者，並把回覆列入對照原文。不得只寫「bdd 失敗」或改寫 bdd 的判定。

| bdd 停下類別 | 交辦對象 | 建議下一步 |
|---|---|---|
| feature、dsl.md 或用語表有問題（含同一個句子在其他 feature 有不同的意思、依賴的行為在其他端點沒有 Rule 驅動，以及 dsl.md 與介面文檔矛盾而 bdd 判斷錯在 dsl.md） | dsl-refine | 修正 bdd 指出的檔案，再依 plan-package check 列出的待補跑依序執行，之後執行 `/implement 從 <任務> 開始` |
| 規格沒寫的行為，或 dsl.md 與介面文檔矛盾而 bdd 判斷錯在介面文檔（bdd 建議委派 dev-finding） | dev-finding 的 record 回覆寫明的應修正的擁有者（介面文檔有誤時為該文檔的 Planner） | 由應修正的擁有者修正（擁有者是 dev-finding 時已由 record 寫入），再依 plan-package check 列出的待補跑依序執行，之後執行 `/implement 從 <任務> 開始` |
| rerun 判定既有 step 需要改（bdd 建議改排紅燈） | 照錄 bdd 寫出的對象：task，bdd 寫明句型的異動不是只改說明時先 dsl-refine | 以 task 的增量入口把這個 `[重跑]` 改排為修正 Phase 的紅燈、綠燈、重構（需要 dsl-refine 時先改正改動摘要），之後執行 `/implement 從 <任務> 開始` |
| 其他端點尚未實作，且依賴的行為有 Rule 驅動 | 依 Rule 4 對回的任務 | 依 Rule 4 寫出應先執行的任務 |
| green 範疇內測試程式錯誤（Rule 2 重試後仍停下） | 使用者 | 照錄 bdd 最後一次的停下說明與建議下一步，處理後執行 `/implement 從 <任務> 開始` |
| 測試環境或測試設定未就緒 | 使用者 | 照錄 bdd 指出的服務、套件或設定檔欄位，就緒後執行 `/implement 從 <任務> 開始` |
| 進入條件不成立 | 依 bdd 寫出要先執行的 subcommand：tasks.md 中同範疇、該階段的未完成任務；沒有這種任務時為使用者 | 先執行該任務；任務狀態與實際不符時以 task 修正任務 |
| 本階段不可修正的回歸、`[驗證]` 的 verify 回歸（Rule 5 重試後仍有，或不符合重試條件）、verify 有未執行或無法對應的 Example | 照錄 bdd 為每個回歸寫出的處理對象 | 照錄 bdd 為每個回歸的位置、Rule、失敗類別、AC 與建議下一步，再補上處理後執行 `/implement <[驗證] 任務>` 重新驗證 |

### Good Example

這個範例照錄 bdd 指出的服務與設定位置，依停下類別寫出交辦對象與回到 implement 的指令。

```text
停止原因：bdd 停下，測試環境未就緒：backend 與 database 端點的測試資料庫無法連線
對照原文：
- `backend/.env › DATABASE_URL`：mysql+aiomysql://root:testpass@127.0.0.1:3307/pvp_1a2b_test
- `bdd 停下說明`：MySQL 127.0.0.1:3307 Connection refused
交辦對象：使用者
建議下一步：以 `docker compose up -d` 啟動 docker-compose.yml 的 MySQL（主機埠 3307）後執行 `/implement 從 T008 開始`
```

這個範例在 bdd 判斷契約有誤而建議委派 dev-finding 時，依 record 回覆的應修正的擁有者交給 api-plan，而不是一律交給 dsl-refine。

```text
停止原因：bdd 停下，feature 或 dsl.md 有問題（dsl.md 與介面文檔矛盾），bdd 判斷錯在介面文檔
對照原文：
- `specs/truth/contracts/components/schemas/SkillCounts.yaml:6`：change_answer_left：type: string、minimum: 0、maximum: 1
- `specs/truth/features/backend/dsl.md:101`：「雙方畫面顯示下列技能剩餘次數：」的改答案（整數，必填）
- `dev-finding 的 record 回覆`：看不到的技術問題，已在技術項.md 加一行；應修正的擁有者：api-plan
交辦對象：api-plan
建議下一步：由 api-plan 依這一行技術項修正 SkillCounts.yaml，再依 plan-package check 列出的待補跑依序執行，之後執行 `/implement 從 T009 開始`
```

### Bad Example

這個範例只寫 bdd 失敗，沒有位置、原文與交辦對象，使用者得自己重跑 bdd 才知道是資料庫沒有啟動，還可能以為是程式寫錯而交給 dsl-refine。

```text
停止原因：T008 的 bdd 紅燈失敗
建議下一步：請檢查後重新執行 /implement
```

## Rule 4 -- 其他端點未實作時對回任務

**強度：MUST**

bdd 因失敗原因是其他端點尚未實作而停下，且依賴的行為在其他端點的 feature 有 Rule 驅動時，必須依 bdd 寫出的端點資料夾與 Example，在 tasks.md 找出範疇涵蓋這些 Example 的綠燈任務，在「建議下一步」寫出這些任務編號與完成狀態。範疇涵蓋的判定：範疇是該 Example 所在的整份 feature、該 feature 所在的端點資料夾，或以行號、Rule 名稱指定的 Rule 包含該 Example 所屬的 Rule（修正 Phase 的任務多為這種範疇）。這些任務已完成時，代表內層綠燈沒有實作到被依賴的行為，交辦對象改為使用者，建議先以 `/bdd green <內層範疇>` 補上；這些任務排在目前停下的任務之後（tasks.md 順序）或不存在時，交辦對象改為 task，請它調整 Phase 排序或補上任務。不得只轉述 bdd 的端點名稱而不對回任務。

### Good Example

這個範例在 T011 前端紅燈因後端連猜端點 404 停下時，對回排在後面的 backend/連猜三次 綠燈 T018，判定排序衝突交給 task。

```text
bdd 停下：其他端點尚未實作；frontend/改答案.feature 的 Given 系統處於 "加入者下一回合不能行動" 呼叫 POST /api/rooms/r1/skills/burst → 404；依賴 backend 連猜三次.feature 的「連猜三次後對手下一回合不能行動」Rule
對回：T018 [綠燈] 範疇 `specs/truth/features/backend/連猜三次.feature`（未完成，排在 T011 之後）
交辦對象：task
建議下一步：以 task 調整 Phase 排序，讓 backend/連猜三次.feature 排在 frontend/改答案.feature 之前，再執行 `/implement 從 T011 開始`
```

### Bad Example

這個範例只轉述 bdd 的端點名稱，使用者得自己翻 tasks.md 找出 backend 的任務，也不知道 T018 排在 T011 之後，直接執行 T018 又會因前面任務未完成而被擋。

```text
建議下一步：backend 尚未實作，請先完成 backend 再執行 /implement
```

## Rule 5 -- [驗證] 的回歸屬已完成任務時重試一次

**強度：MUST**

`[驗證]` 委派的 `/bdd verify` 停下並回報回歸（只指 `regressions`）時，implement 逐一判定每個回歸的 Example：同時符合下列兩點才可自動重試，其餘一律依 Rule 1 停止。(1) 屬已完成任務：回歸的 Example 在 tasks.md 中已勾選 `[X]` 的階段任務的範疇內（整份 feature、其端點資料夾，或以行號、Rule 名稱指定的 Rule 包含它所屬的 Rule），或 bdd 寫出的失敗訊息位置指到這些任務改過的檔案；改過的檔案以 `tasks_state.py` 輸出的 `done_coverage.files` 為準（已勾選階段任務所屬 Phase 標頭的預計修改，加上已勾選無標記任務描述中的路徑，只寫檔名的以檔名比對）。(2) bdd 建議的下一步是 `/bdd green <位置>`（失敗類別為業務行為尚未實作）或 `/bdd red <位置>`（失敗類別為測試程式錯誤）。feature、dsl.md 或用語表有問題、環境問題、規格矛盾、其他端點尚未實作、`not_run` 或 `unmapped` 不為空、失敗訊息沒有指到任何檔案且不屬已勾選範疇時，不符合重試條件，直接停止。

符合時，implement 對每個回歸的 Example 以 bdd 回報的位置依 tasks.md 順序各重試一次：建議 `/bdd green <位置>` 就委派 green，建議 `/bdd red <位置>` 就依序委派 red 與 green（同 Rule 2），委派時附上該 Example 所屬 feature 的 Phase 標頭；所有重試完成後只再委派 `/bdd verify` 一次。再次 verify 仍有回歸（含新出現的回歸）、重試的 bdd 停下，或再次 verify 停下時，不得再重試，依 Rule 1 停止，停止回報的對照原文依序列出第一次 verify、重試與再次 verify 的回歸或停下說明。重試期間 implement 不得自行修改程式、測試或規格，也不得變更任何任務的勾選狀態。

### Good Example

這個範例單獨執行 T027，回歸的 Example 在已勾選 T008～T010 的範疇內，符合重試條件，重試一次 green 後再 verify 沒有回歸。

```text
/implement T027 → /bdd verify 停下：1 個回歸
位置：specs/truth/features/backend/改答案.feature:45（Rule：改答案必須取代祕密答案且不轉移回合）
類別：業務行為尚未實作；AC：AC-01；建議下一步：/bdd green specs/truth/features/backend/改答案.feature:45
判定：done_coverage.scopes 含 specs/truth/features/backend/改答案.feature（T008～T010 已勾選）→ 符合重試
重試：/bdd green specs/truth/features/backend/改答案.feature:45（附 Phase 4 標頭）→ green 完成
再次 /bdd verify：regressions 0 → T027 勾為 [X]
```

### Bad Example

這個範例對類別是 dsl.md 句子撞句的回歸也重試 green，這類問題 green 無法解決，只是多花 16 分鐘 verify 又停下；重試仍失敗後還再重試第二輪，沒有上限。

```text
/bdd verify 停下：類別：feature、dsl.md 或用語表有問題（與 001 撞句），建議交由 dsl-refine
處理：/bdd green …改答案.feature:45 → /bdd verify → 仍有回歸 → /bdd green → /bdd verify → …
```

## Rule 6 -- 原始碼段以外的產品檔先交 system-analysis 再交 task

**強度：MUST**

bdd 的綠燈或重構完成說明，或直接實作的任務依實作範圍規範，列出「原始碼段以外的產品檔」（不是「無」）時，implement 不得直接繼續下一個任務：必須先委派 system-analysis，寫明「以原始碼段入口」並附上列出的每個檔案與原因，由它只修正 plan.md 的 `### 原始碼（repo 根目錄）` 與結構決策；system-analysis 完成後，再委派 task 以增量入口修正未勾選的任務；兩者都完成才勾選這個任務並重新取得下一個任務。system-analysis 或 task 停下（含回報不能改）時，依 Rule 1 停止，交辦對象照錄它們寫出的對象，這個任務維持未勾選。implement 不得自行修改 plan.md 或 tasks.md 的任務內容，也不得搬動產品檔讓它符合原始碼段。

### Good Example

這個範例在綠燈列出原始碼段以外的產品檔後，先交 system-analysis 修正原始碼段，再交 task 修正未勾選的任務，兩者完成才勾選並繼續。

```text
T006 [綠燈] → bdd green 完成；原始碼段以外的產品檔：backend/app/services/chat.py（plan.md 原始碼的 services/ 只列 rooms.py、snapshot.py）
→ /system-analysis 以原始碼段入口：backend/app/services/chat.py（訊息送出與頻率限制抽成獨立服務）→ 原始碼段補上 chat.py，check_plan.py 通過
→ /task 以增量入口修正未勾選的任務 → Phase 6 的預計修改補上 backend/app/services/chat.py
→ T006 勾為 [X]，重新取得 next：T007
```

### Bad Example

這個範例看到標記仍直接勾選並繼續，plan.md 與未勾選的任務仍指向舊位置，後續的綠燈照原始碼段把聊天推播寫進 rooms.py，同一功能的程式分散兩處，到收尾才發現。

```text
T006 [綠燈] → bdd green 完成；原始碼段以外的產品檔：backend/app/services/chat.py
→ T006 勾為 [X]，繼續 T007～T010
```
