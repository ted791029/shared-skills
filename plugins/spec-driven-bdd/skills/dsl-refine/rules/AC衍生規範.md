# AC 衍生規範

## Rule 1 -- 每組 When 依端點決定衍生 Example 的動作

**強度：MUST**

AC 的 Example 以 When 分段：從一句 When 到下一句 When 之前為一組。每組 When 在分派到的每個端點各衍生至少一個 Example，該組之前所有在本端點有行為的動作改寫成 Given 差異句。前端的 When 保留該組全部動作，因為畫面上的操作順序本身就是驗收內容。後端的 When 只放這條 Rule 要驗的一個動作：通常是該組最後一個在本端點有行為的動作；斷言在本端點要再做一個動作才觀察得到時（例如畫面上的停用狀態，在後端是再使用一次會被拒絕），就是那個動作，該組原本的動作全部改寫成 Given。在本端點沒有行為的動作（ui-contract.md 寫明不呼叫 API 的開啟、取消、按下）直接省略，並在涵蓋表「AC 句型對照」登記為「本端點不適用」。不得把兩組 When 合併成一個 Example。以下 Example 皆對照此 AC 與 ui-contract.md：

```gherkin
    Example: AC-01 甲在第 1 回合把答案從 0123 改為 4567 後猜 5679，乙接著猜 0123
      When "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"
      When "乙" 猜 "0123"
      Then "甲" 的 "改答案" 為停用並說明 "本局次數已用完"
```

```text
ui-contract.md：開啟改答案只顯示輸入框，不呼叫 API；送出新答案呼叫 POST /api/rooms/{room_id}/skills/change-secret
```

### Good Example

這個範例的前端第 2 組把第 1 組整組改寫成 Given；後端省略不呼叫 API 的開啟改答案，第 3 組要驗的停用在後端以再送一次新答案觀察，該動作成為 When，乙的猜測改寫成 Given。

```gherkin
# frontend/改答案.feature
    Example: 甲把答案從 0123 改為 4567 後猜 5679
      Given "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"

# backend/改答案.feature
    Example: 甲把答案改為 4567，雙方各猜一次後甲再送出新答案 1357
      Given "甲" 送出新答案 "4567"
      And "甲" 猜 "5679"
      And "乙" 猜 "0123"
      When "甲" 送出新答案 "1357"
      Then 系統拒絕這次"改答案"，因為 "本局次數已用完"
```

```markdown
| `"甲" 開啟改答案` | backend | 本端點不適用 |
```

### Bad Example

這個範例在後端照搬整組 When，開啟改答案在後端什麼都不做，乙的猜測與要驗的停用無關，回應斷言只能驗乙的回報，Rule 的結果被擠到額外的查證句才驗得到。

```gherkin
# backend/改答案.feature
    Example: 甲把答案改為 4567 並猜 5679 後乙猜 0123
      Given "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      And "甲" 猜 "5679"
      When "乙" 猜 "0123"
      Then 系統回覆 "0A0B"
      And "甲" 之後使用 "改答案" 會被拒絕，因為 "本局次數已用完"
```

## Rule 2 -- AC 的每個斷言都必須落到衍生 Example

**強度：MUST**

AC 每組 When 底下的每一句 Then 與 And（含表格的每一列），都必須出現在至少一個端點的衍生 Example 的 Then；同一組的斷言依規則拆到多個 Example 時，所有 Example 合起來要涵蓋全部斷言。不得省略、合併成較弱的斷言或改驗其他結果。以下 Example 皆對照此 AC 片段：

```gherkin
      When "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      And 雙方畫面顯示技能剩餘次數：
        | 玩家 | 改答案 | 連猜三次 |
        | 甲   | 0      | 1        |
        | 乙   | 1      | 1        |
      And "乙" 的畫面看不到 "甲" 的新答案與舊答案
```

### Good Example

這個範例在前端拆成三個 Example 各驗一條規則，三句斷言都有落點，表格逐列保留。

```gherkin
  Rule: 送出新答案後，畫面必須顯示新答案

    Example: 甲送出新答案 4567
      When "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"

  Rule: 送出新答案後，雙方的技能剩餘次數必須同步更新

    Example: 甲送出新答案 4567
      When "甲" 送出新答案 "4567"
      Then 雙方畫面顯示技能剩餘次數：
        | 玩家 | 改答案 | 連猜三次 |
        | 甲   | 0      | 1        |
        | 乙   | 1      | 1        |

  Rule: 對手不能看到改答案的內容

    Example: 甲送出新答案 4567
      When "甲" 送出新答案 "4567"
      Then "乙" 的畫面看不到 "甲" 的新答案與舊答案
```

### Bad Example

這個範例漏掉「乙看不到答案」的斷言，又把剩餘次數的表格弱化成只驗甲一列，AC 要驗收的保密規則與乙的次數不變，在衍生 feature 裡測不到。

```gherkin
  Rule: 送出新答案後，畫面必須顯示新答案

    Example: 甲送出新答案 4567
      When "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      And "甲" 的改答案剩餘次數為 0
```

## Rule 3 -- 衍生不得改變 AC 的語意

**強度：MUST**

衍生 Example 的動作、資料與預期結果必須與 AC 相同：不得更換 AC 使用的資料值，不得加入 AC 沒有寫的預期結果，不得把 AC 的條件改寬或改嚴。端點需要 AC 沒寫的細節（例如回應欄位、資料表內容）時，只能在該端點的 dsl.md 以技術對應補足，並列入待確認事項。以下 Example 皆對照此 AC 片段：

```gherkin
      When "乙" 猜 "0123"
      Then 雙方的猜測歷史依序為：
        | 回合 | 玩家 | 紀錄           |
        | 1    | 甲   | 使用改答案     |
        | 1    | 乙   | 猜 0123，0A0B |
```

### Good Example

這個範例在後端逐字沿用 AC 的句子、猜測值與回報，本端點的讀取方式只寫在 dsl.md。

```gherkin
      When "乙" 猜 "0123"
      Then 雙方的猜測歷史依序為：
        | 回合 | 玩家 | 紀錄           |
        | 1    | 甲   | 使用改答案     |
        | 1    | 乙   | 猜 0123，0A0B |
```

### Bad Example

這個範例把猜測值換成 4567、多加了 AC 沒有的「對局結束」預期，衍生 feature 驗的已經不是 PM 核准的情境，通過了也不代表 AC 成立。

```gherkin
      When "乙" 猜 "4567"
      Then 雙方的猜測歷史依序為：
        | 回合 | 玩家 | 紀錄           |
        | 1    | 甲   | 使用改答案     |
        | 1    | 乙   | 猜 4567，4A0B |
      And 對局結束
```

## Rule 4 -- 補充案例只能追溯到 spec.md 且分開登記

**強度：MUST**

AC 沒有涵蓋、但端點需要的失敗、邊界、非功能與儲存約束案例，只能來自 spec.md 的 FR、NFR 與邊界情況；介面文檔（如 data-model.dbml）寫出的約束，只有在文檔註明對應的需求編號，或該需求原文直接寫出同一個界限或唯一性時才算來源。每個補充案例登記為那條 spec 需求的編號，登記在涵蓋表「補充案例」並在回報中與 AC 衍生的 Example 分開列出；不得從追溯不到需求的介面文檔內容或自行想像補案例，也不得把補充案例寫進 AC 涵蓋表。以下 Example 皆對照此 spec.md 與 data-model.dbml 片段：

```text
FR-003 新答案不符合四碼規則時，系統不接受並顯示四碼規則提示，答案與剩餘次數不變
FR-012 連猜必須逐次進行，最多三次
data-model.dbml：ck_guesses_burst_index（burst_index 為 NULL 或介於 1 與 3）；ck_guesses_counts（a_count、b_count 介於 0 與 4）
openapi.yaml：錯誤碼 DUPLICATE_DIGIT
```

### Good Example

這個範例的 FR-003 直接來自 spec.md；連猜次序的 CHECK 界限與 FR-012 原文「最多三次」相同，登記為 FR-012；A、B 數範圍在 spec.md 找不到對應需求，不補。

```markdown
| 來源需求 | 端點 | feature | Rule | 異動 |
|---|---|---|---|---|
| FR-003 | backend | 改答案 | 新答案不符合四碼規則時，系統必須拒絕且答案不變 | ADD |
| FR-012 | database | 連猜三次 | 連猜的猜測紀錄只能標為第 1 到第 3 次 | ADD |
```

### Bad Example

這個範例依 openapi 的錯誤碼與 data-model 的 CHECK 補了 spec.md 追溯不到的案例，PM 沒審過這兩條規則，實作者卻要為它們寫程式。

```markdown
| 來源需求 | 端點 | feature | Rule | 異動 |
|---|---|---|---|---|
| openapi 錯誤碼 DUPLICATE_DIGIT | backend | 改答案 | 新答案含重複數字時必須拒絕 | ADD |
| data-model ck_guesses_counts | database | 連猜三次 | A、B 數只能介於 0 與 4 | ADD |
```

## Rule 5 -- AC 與其他產物衝突時以 AC 為準

**強度：MUST**

AC 的步驟或斷言與 spec.md、plan.md 或介面文檔不一致時，衍生 Example 依 AC 撰寫，並把衝突列入待確認事項「AC 與產物衝突」，寫出 AC 的內容、產物的內容與 dev-finding 回覆的應修正的擁有者，這次的結果依待確認事項規範 Rule 5 是「不能改」；不得改寫衍生 Example 去配合產物，也不得自行選擇產物的版本。以下 Example 皆對照此衝突：

```text
AC-01 第 1 組：送出新答案後「雙方畫面顯示輪到 "甲"」
openapi.yaml：useSkill 的回應 next_turn 為對手
dev-finding 的回覆：直接修（違反 AC-01），應修正的擁有者 api-plan
```

### Good Example

這個範例依 AC 的「仍輪到甲」撰寫，並把 openapi 寫成換手的衝突與應修正的擁有者列出來。

```markdown
- AC 與產物衝突：AC-01 第 1 組「雙方畫面顯示輪到 "甲"」；openapi `useSkill` 回應 `next_turn` 為對手。衍生 Example 依 AC 撰寫，交 api-plan 修正
```

### Bad Example

這個範例發現衝突後改依 openapi 寫成換手，衍生 feature 與 PM 核准的驗收標準相反，實作依 feature 做完後 Demo 會不過。

```gherkin
      Then 雙方畫面顯示輪到 "乙"
```

## Rule 6 -- 每條 Rule 必須對照既有的 Rule 標示異動

**強度：MUST**

列出每個端點的 Rule 時，必須先對照 `specs/truth/features/` 該端點既有的 Rule，並在涵蓋表的「異動」欄填下表三個值之一。既有的 Rule 已描述同一條規則時，沿用它的名稱與所在的 feature（名稱寫了文案或數值、這次又要改到它時，依 Rule 與 Example 規範 Rule 11 改名，仍是同一條 Rule，不另開新的 Rule），不得在它旁邊另開一條描述同一條規則的 Rule；既有的 Example 已驗證 AC 經過的這條規則時，即使資料值與 AC 不同也標 `無`、不另外衍生 Example，AC 的斷言要求既有的 Example 沒有驗到的結果時才標 `MOD` 並在該 Rule 加上 Example。這次的需求、上游的 truth 異動或 spec.md「受影響的既有功能」使既有的 Rule 不再成立時，該 Rule 列入盤點的修改或刪除；被刪除的 Rule 不列在涵蓋表，只記在 `truth-changes.md`。專案的第一個 plan 沒有既有的 Rule，全部為 `ADD`。以下 Example 皆對照此 AC、需求與既有的 Rule：

| 異動 | 判定 |
|---|---|
| `ADD` | truth 沒有這條 Rule，這次新增 |
| `MOD` | truth 已有這條 Rule，這次改變它的名稱、Example 或步驟 |
| `無` | truth 已有這條 Rule，AC 或需求經過它但不改變它 |

```text
AC-01 第 1 組：乙以暗號加入房間；第 2 組：雙方查看排行榜，甲的勝場數為 1
FR-002：移除連猜三次
既有的 backend Rule：
  進入房間.feature：以正確的暗號加入時，必須進入該房間
  技能特效.feature：使用技能後，雙方必須收到寫明技能名稱的特效（Example 含改答案與連猜三次）
  連猜三次.feature：3 條 Rule
```

### Good Example

這個範例的加入房間沿用既有的 Rule 標「無」，排行榜是新 Rule 標 ADD，因 FR-002 而要拿掉連猜三次 Example 的既有 Rule 標 MOD，整份刪除的 feature 只列在盤點。

```markdown
| AC | When 組 | 端點 | feature | Rule | 異動 |
|---|---|---|---|---|---|
| AC-01 | 1 | backend | `進入房間.feature` | 以正確的暗號加入時，必須進入該房間 | 無 |
| AC-01 | 2 | backend | `排行榜.feature` | 排行榜必須依勝場數由多到少列出玩家 | ADD |

| 來源需求 | 端點 | feature | Rule | 異動 |
|---|---|---|---|---|
| FR-002 | backend | `技能特效.feature` | 使用技能後，雙方必須收到寫明技能名稱的特效 | MOD |

盤點：DEL `features/backend/連猜三次.feature`（整份，3 條 Rule，FR-002）
```

### Bad Example

這個範例沒有對照既有的 Rule：加入房間另開一條同義的 Rule，兩條 Rule 驗同一件事；連猜三次的 feature 與特效 Rule 中連猜三次的 Example 沒有列入盤點，truth 留下已經不存在的行為，這些 Example 在實作移除連猜三次後會一直失敗。

```markdown
| AC | When 組 | 端點 | feature | Rule | 異動 |
|---|---|---|---|---|---|
| AC-01 | 1 | backend | `排行榜.feature` | 輸入正確暗號的玩家必須能進入房間 | ADD |
| AC-01 | 2 | backend | `排行榜.feature` | 排行榜必須依勝場數由多到少列出玩家 | ADD |
```

## Rule 7 -- 被刪除的 AC 獨佔的 Rule 必須還原

**強度：MUST**

同一個 plan 再次執行、diff 列出被刪除的 AC 時，必須以上次的涵蓋表找出它對應的 Rule。沒有其他 AC 或補充案例的列指向的 Rule 是它獨佔的 Rule，必須還原到這個 plan 開始前的樣子：異動為 `ADD` 的刪除；異動為 `MOD` 的改回 `.plan.json` 的基準 commit 中該 Rule 的內容（以 `git show <基準 commit>:<feature 路徑>` 取得）；異動為 `無` 的不動。仍有其他列指向的 Rule 不還原，只移除被刪除的 AC 的列。還原的 Rule 列入盤點與委派簡報的異動範圍。以下 Example 皆對照此 diff 與上次的涵蓋表：

```text
diff：刪除 AC-08（使用者在 /dev-finding review 回覆這個 plan 不處理）
上次的涵蓋表：
| AC-08 | 1 | backend | `進入房間.feature` | 以正確的暗號加入時，必須進入該房間 | 無 |
| AC-08 | 2 | backend | `排行榜.feature` | 勝場數相同時必須依達成時間由早到晚排列 | ADD |
| AC-08 | 3 | backend | `互猜對戰.feature` | 對局結束後必須回傳勝方與雙方的勝場數 | MOD |
| AC-02 | 3 | backend | `互猜對戰.feature` | 對局結束後必須回傳勝方與雙方的勝場數 | MOD |
```

### Good Example

這個範例只還原 AC-08 獨佔的 Rule：新增的刪除，沒有改的不動，AC-02 也指向的 Rule 保留。

```text
排行榜.feature「勝場數相同時必須依達成時間由早到晚排列」：AC-08 獨佔、ADD → 刪除這條 Rule
進入房間.feature「以正確的暗號加入時，必須進入該房間」：無 → 不動
互猜對戰.feature「對局結束後必須回傳勝方與雙方的勝場數」：AC-02 也指向它 → 不還原，只移除 AC-08 的列
```

### Bad Example

這個範例只刪掉涵蓋表的列，AC-08 新增的 Rule 留在 truth；使用者已決定這個 plan 不處理的行為仍有測試，/task 會為它排任務。

```text
涵蓋表：移除 AC-08 的 3 列
排行榜.feature「勝場數相同時必須依達成時間由早到晚排列」：保留
```

## Rule 8 -- 與 PM 的需求矛盾的開發發現 AC 先不衍生

**強度：MUST**

標 `@開發發現` 的 AC 與 PM 提出的 AC、spec.md 的 FR 或 NFR 矛盾時（它的依據寫明與哪個編號矛盾，或同一個情況下兩者要求不同的結果），不得衍生它，也不得為它改寫 PM 提出的 AC 衍生的 Rule：PM 提出的 AC 照常衍生，這個 AC 列入回報的「開發發現」，寫出雙方的編號、衝突的句子與「未衍生，待 PM 在 dev-finding 的 review 決定」，這次的結果是「不能改」。PM 保留它時，矛盾的一方由它的擁有者依保留並取代改寫，矛盾消失後才衍生；PM 不要它時它會被刪除，不必衍生。以下 Example 皆對照此 acceptance：

```gherkin
  Rule: 客人必須能取消自己的預約

    # 涵蓋：US1、FR-005
    Example: AC-02 "王小明" 在用餐前 1 小時取消預約
      Given 系統處於 "一筆 1 小時後用餐的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "預約已取消"

  Rule: 用餐前 2 小時內不能取消預約

    # 開發發現：api-plan；餐廳要在 2 小時前把名額釋出給候補，與 FR-005、AC-02 矛盾
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
      Given 系統處於 "一筆 1 小時後用餐的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "用餐前 2 小時內無法取消"
```

### Good Example

這個範例照常衍生 AC-02，AC-08 不衍生，在回報的開發發現寫出矛盾與待 PM 決定，結果判為不能改。

```markdown
### 開發發現

- AC-08（`@開發發現`）的「用餐前 2 小時內無法取消」與 AC-02 的「預約已取消」、FR-005 在同一個情況下要求不同的結果：未衍生，待 PM 在 dev-finding 的 review 決定，應修正的擁有者 dev-finding

不能改：AC-08 與 AC-02、FR-005 矛盾，待 PM 決定。這次沒有記錄，dsl-refine 仍是待補跑；請先執行 /dev-finding review。
```

### Bad Example

這個範例把兩個 AC 都衍生成 Rule；truth 同時有在同一個情況下要求相反結果的兩條 Rule，其中一條的測試永遠失敗，PM 還沒決定，實作就可能先照 AC-08 拒絕取消，推翻 PM 核准過的 AC-02。

```markdown
| AC | When 組 | 端點 | feature | Rule | 異動 |
|---|---|---|---|---|---|
| AC-02 | 1 | backend | `取消預約.feature` | 客人必須能取消自己的預約 | 無 |
| AC-08 | 1 | backend | `取消預約.feature` | 用餐前 2 小時內不能取消預約 | ADD |
```
