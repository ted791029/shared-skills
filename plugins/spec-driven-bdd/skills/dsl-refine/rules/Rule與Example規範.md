# Rule 與 Example 規範

## Rule 1 -- Rule 必須拆到原子

**強度：MUST**

每條 Rule 只陳述一件必須成立的事，名稱寫成「…必須…」或「…不能…」。名稱要用「並」「而且」「，…時又…」才寫得出來時必須拆開；Example 標題聽起來像另一條規則時，也代表 Rule 還能再拆。acceptance 的 Rule 描述整段旅程，衍生時依它底下每組 When 的斷言拆成多條原子 Rule，不沿用旅程名稱。

### Good Example

這個範例把送出新答案的兩件事拆成兩條 Rule，各自可以單獨被違反。

```gherkin
  Rule: 送出新答案後，畫面必須顯示新答案
  Rule: 送出新答案後，雙方的技能剩餘次數必須同步更新
```

### Bad Example

這個範例沿用 acceptance 的旅程 Rule 名稱，畫面顯示正確但次數沒更新時，這條 Rule 算通過還是失敗無法判斷，報告也看不出是哪一件事壞了。

```gherkin
  Rule: 改答案後對手必須依新答案計算，且對局結束前看不到答案內容
```

## Rule 2 -- 一個 Example 只驗一條規則

**強度：MUST**

AC 一組 When 的斷言驗證多條規則時，拆成多個 Example，各放到對應的 Rule 底下，每個 Example 只保留驗證該規則的斷言。同一個結果換另一種管道再驗一次（例如回應與重新查詢）屬於同一條規則，留在同一個 Example。以下 Example 皆對照此 AC 片段：

```gherkin
      When "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      And 雙方畫面顯示技能剩餘次數：
        | 玩家 | 改答案 | 連猜三次 |
        | 甲   | 0      | 1        |
        | 乙   | 1      | 1        |
```

### Good Example

這個範例依規則拆成兩個 Example，各自只保留驗證該規則的斷言。

```gherkin
  Rule: 送出新答案後，畫面必須顯示新答案

    Example: 甲送出新答案 4567
      When "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      And "重新開啟頁面後"，"甲" 的畫面顯示目前答案 "4567"

  Rule: 送出新答案後，雙方的技能剩餘次數必須同步更新

    Example: 甲送出新答案 4567
      When "甲" 送出新答案 "4567"
      Then 雙方畫面顯示技能剩餘次數：
        | 玩家 | 改答案 | 連猜次數 |
        | 甲   | 0      | 1        |
        | 乙   | 1      | 1        |
```

### Bad Example

這個範例把兩條規則的斷言放在同一個 Example，次數沒更新時報告顯示的是「畫面顯示新答案」失敗，讀者會誤以為新答案沒有顯示。

```gherkin
  Rule: 送出新答案後，畫面必須顯示新答案

    Example: 甲送出新答案 4567
      When "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      And 雙方畫面顯示技能剩餘次數：
        | 玩家 | 改答案 | 連猜三次 |
        | 甲   | 0      | 1        |
        | 乙   | 1      | 1        |
```

## Rule 3 -- Example 標題只寫資料情境且不帶編號

**強度：MUST**

Example 標題寫「誰、在什麼狀態、用什麼資料、做了什麼」，不寫預期結果（被拒絕、成功、顯示…），也不與 Rule 名稱幾乎同句。標題不得以 AC、US、FR 等任何編號開頭，Example 上方也不得加 `# 涵蓋：` 之類的編號註解；AC 的追溯只記在涵蓋表的 AC 涵蓋表。同一條 Rule 有多個 Example 時，標題要點出彼此的資料差異；資料相同的 Example 標題可以相同，差別由所屬的 Rule 表達。

### Good Example

這個範例的標題只寫誰用什麼資料做了什麼，沒有編號，結果交給 Rule 與 Then。

```gherkin
  Rule: 不符合四碼規則的新答案必須被拒絕

    Example: 甲送出新答案 1123
```

### Bad Example

這個範例的標題以 AC 編號開頭、上方又加了涵蓋註解，標題還重述 Rule 的結論，讀者從標題得不到任何資料資訊，同一條 Rule 再加一筆 12 的資料時兩個標題會幾乎一樣。

```gherkin
  Rule: 不符合四碼規則的新答案必須被拒絕

    # 涵蓋：AC-02、FR-003
    Example: AC-02 不符合四碼規則時被拒絕
```

## Rule 4 -- 每個 Example 只有一句 When

**強度：MUST**

每個 Example 與 Scenario Outline 的 When 只能出現一次，同一組的後續動作用 And 接在 When 之後，Then 全部寫在最後一個動作之後，Then 之後不得再有 When。AC 的多組 When 依 AC 衍生規範拆成多個 Example，不得保留旅程形式。以下 Example 皆對照此 AC 片段：

```gherkin
      When "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"
```

### Good Example

這個範例每個 Example 只有一句 When，第二組把前一組的動作改寫成 Given。

```gherkin
    Example: 甲開啟改答案並送出 4567
      When "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"

    Example: 甲把答案改為 4567 後猜 5679
      Given "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"
```

### Bad Example

這個範例在 Then 之後再寫 When，一個 Example 跑了兩段旅程，第一段失敗時第二段不會執行，報告也看不出是哪一段失敗。

```gherkin
    Example: 甲改答案後猜 5679
      When "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"
```

## Rule 5 -- 一個 Example 只跑一個情境

**強度：MUST**

一組 When 或補充案例要依序跑多個獨立情境（多種輸入、多個起點、另一份資料）時，每個情境拆成一個 Example 或 Outline 的一列，不得在同一個 Example 依序跑完全部情境。以下 Example 皆對照此補充案例：

```text
FR-003：新答案 12、1123、abcd 都不符合四碼規則，系統都要拒絕
```

### Good Example

這個範例把三種輸入各寫成 Outline 的一列，每一列是獨立的測試。

```gherkin
    Scenario Outline: 甲送出新答案 <新答案>
      Given "甲" 開啟改答案
      When "甲" 送出新答案 "<新答案>"
      Then 系統拒絕這次改答案，因為 "四碼規則不符"

      Examples:
        | 新答案 |
        | 12     |
        | 1123   |
        | abcd   |
```

### Bad Example

這個範例在同一個 Example 依序送三種輸入，1123 失敗時 abcd 不會執行，報告也只顯示一筆失敗，看不出是哪一種輸入出錯。

```gherkin
    Example: 甲送出三種不合規則的新答案
      Given "甲" 開啟改答案
      When "甲" 送出新答案 "12"
      Then 系統拒絕這次改答案，因為 "四碼規則不符"
      When "甲" 送出新答案 "1123"
      Then 系統拒絕這次改答案，因為 "四碼規則不符"
```

## Rule 6 -- 只差資料的 Example 才合成 Outline

**強度：MUST**

同一條 Rule 底下，步驟的句數、順序與句型完全相同、只差參數值的 Example 合成 Scenario Outline；步驟不同的不合併，也不得為了合併新增一欄「狀態」或「操作」來代替不同的步驟。Outline 標題以 `<欄位>` 表達每列的資料差異，Examples 表只列資料欄，不加編號欄。以下 Example 皆對照此兩個補充案例：

```text
FR-003：新答案 1123 不符合四碼規則 → 拒絕，答案不變
FR-004：對手回合送出新答案 → 拒絕，答案不變
```

### Good Example

這個範例兩個案例的步驟不同（一個差新答案、一個差回合），各自保留 Example，不硬合併。

```gherkin
  Rule: 不符合四碼規則的新答案必須被拒絕

    Example: 甲送出新答案 1123
      Given "甲" 開啟改答案
      When "甲" 送出新答案 "1123"
      Then 系統拒絕這次改答案，因為 "四碼規則不符"

  Rule: 不是自己的回合時不能改答案

    Example: 輪到乙時甲送出新答案 4567
      Given "甲" 猜 "5679"
      And "甲" 開啟改答案
      When "甲" 送出新答案 "4567"
      Then 系統拒絕這次改答案，因為 "不是你的回合"
```

### Bad Example

這個範例為了合併加了一欄「前提」代替不同的 Given，step definition 得在一個句型裡做兩種完全不同的前置動作。

```gherkin
    Scenario Outline: 在<前提>送出新答案 <新答案>
      Given <前提>
      When "甲" 送出新答案 "<新答案>"
      Then 系統拒絕這次改答案，因為 "<原因>"

      Examples:
        | 前提                 | 新答案 | 原因         |
        | 甲開啟改答案         | 1123   | 四碼規則不符 |
        | 甲猜過後開啟改答案   | 4567   | 不是你的回合 |
```

## Rule 7 -- Background 只放起點

**強度：MUST**

寫 Background 時，只寫在 Feature 層級，內容只有起點句上方的 `# 預設值：` 註解與建立起點的一句起點句（或沒有起點資料時的系統層級前提）；不放差異句、紀錄或觀察設定，也不在 Rule 底下另寫 Background。

### Good Example

這個範例的 Background 只建立起點，其他前提都留在各 Example 的 Given。

```gherkin
Feature: 改答案

  Background:
    # 預設值：房主甲的祕密答案為 0123、加入者乙的祕密答案為 5678，雙方已進入對戰畫面，第 1 回合輪到甲；雙方的改答案與連猜三次各剩 1 次
    Given 系統處於 "對戰開始輪到甲"
```

### Bad Example

這個範例把只有部分 Example 需要的猜測與錄影設定放進 Background，不需要猜測的 Example 也被迫先猜，讀者還誤以為每個 Example 都在驗證推播。

```gherkin
Feature: 改答案

  Background:
    Given 系統處於 "對戰開始輪到甲"
    And "甲" 猜 "5679"
    And 開始記錄雙方收到的推播
```

## Rule 8 -- 必須先決定的執行環境用標籤

**強度：MUST**

必須在 Background 建立起點之前決定的執行環境，例如瀏覽器、裝置或語系，以標籤標在 Example 上，不寫成 Given 步驟。

### Good Example

這個範例以標籤指定裝置，測試框架在建立起點前就能決定要開哪些瀏覽器。

```gherkin
    @桌面與手機
    Example: 甲開啟改答案並送出 4567
      When "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
```

### Bad Example

這個範例把裝置寫成 Given 步驟，Background 已經用預設瀏覽器建好對局，這一步才要切換裝置，只能重開瀏覽器，Background 建立的狀態也跟著遺失。

```gherkin
    Example: 甲開啟改答案並送出 4567
      Given 測試分別在桌面與手機瀏覽器上執行
      When "甲" 開啟改答案
```

## Rule 9 -- 起點句一律與 acceptance 相同且名稱對應唯一的建立方式

**強度：MUST**

所有端點的起點句，不論寫在 Background 或 Example 的第一句 Given，都用 acceptance 的句型 `系統處於 {前置狀態}`。同一個端點資料夾中，不同建立方式的起點必須使用不同的起點名稱，dsl.md 中該句型的那一列逐一寫出每個起點名稱的建立方式；不得讓同一個起點名稱在不同 feature 代表不同的建立方式。以下 Example 皆對照此後端 dsl.md 的起點句型列：

```markdown
| `系統處於 {前置狀態}` | 系統處於 {"對戰開始輪到甲"} | ・**前置狀態** `{前置狀態}`（字串）：起點名稱，只限 對戰開始輪到甲、單一行程已啟動 | 不支援 | 動作：只寫在 Background 或 Example 的第一句 Given。「對戰開始輪到甲」在測試行程內建立應用程式、清空測試資料庫後以 API 建立對局；「單一行程已啟動」另外啟動 uvicorn 單一行程，不建立任何對局 |
```

### Good Example

這個範例中，API 測試與需要另外啟動行程的容量 feature 都用 `系統處於`，但各自使用 dsl.md 中建立方式不同的起點名稱。

```gherkin
Feature: 改答案

  Background:
    Given 系統處於 "對戰開始輪到甲"

Feature: 容量

  Background:
    Given 系統處於 "單一行程已啟動"
```

### Bad Example

這個範例的前端改用 `畫面處於`，與 acceptance 的起點句對不上，AC 句型對照得多登記一句，同一個起點在兩個端點看起來像兩種狀態。

```gherkin
Feature: 改答案

  Background:
    Given 畫面處於 "對戰開始輪到甲"
```

## Rule 10 -- 同一條規則只開一個 Rule 區塊

**強度：MUST**

同一份 feature 中，驗證同一條規則的 Example 與 Scenario Outline（包括依 Rule 2、Rule 5 拆出來的）全部放在同一個 Rule 區塊底下，Rule 名稱在同一份 feature 只出現一次。

### Good Example

這個範例把兩個起點不同的拒絕 Example 放在同一個 Rule 底下，讀者一眼看出兩者驗的是同一條規則。

```gherkin
  Rule: 不符合四碼規則的新答案必須被拒絕

    Example: 甲送出新答案 1123
      Given "甲" 開啟改答案
      When "甲" 送出新答案 "1123"
      Then "甲" 的畫面顯示四碼規則提示

    Example: 甲送出新答案 12
      Given "甲" 開啟改答案
      When "甲" 送出新答案 "12"
      Then "甲" 的畫面顯示四碼規則提示
```

### Bad Example

這個範例每拆一個 Example 就重開一個同名 Rule，報告中同一條規則出現兩次，讀者會以為是兩條不同的規則，修改規則時也得改兩處。

```gherkin
  Rule: 不符合四碼規則的新答案必須被拒絕

    Example: 甲送出新答案 1123

  Rule: 不符合四碼規則的新答案必須被拒絕

    Example: 甲送出新答案 12
```

## Rule 11 -- Rule 名稱不寫會變動的文案與數值

**強度：MUST**

Rule 名稱寫這條規則要成立的行為，不寫 UI 契約的文案（提示、按鈕、錯誤訊息的文字）與需求的數值（次數、秒數、字數、人數），要提到時寫它們的意思（例如「已滿的提示」），文案與數值由 Example 的步驟帶入。名稱符合這條時，文案或數值改變只改 Example，名稱不變。既有名稱寫了文案或數值、這次又要改到這條 Rule 時，一併改成只寫行為的名稱：新名稱陳述的規則必須與 Example 驗證的內容相同，不得多於或少於它；依跨端點一致規範 Rule 2，其他端點的同名 Rule 一併改成相同的名稱；改名依 truth-changes 的紀錄撰寫規範記錄。以下 Example 皆對照此需求、UI 契約與既有 Rule：

```text
FR-003：房間滿員時，再加入的玩家看到已滿的提示，不能進入房間
002/UI-01 的文案「房間已滿」，本 plan 改為「房間已滿，請換一個暗號」
既有 Rule：backend/房間.feature 與 frontend/房間.feature 都有 Rule「房間滿員時必須顯示「房間已滿」」，Example 驗證 "丙" 看到 "房間已滿"
```

### Good Example

這個範例改提示時一併把兩個端點的名稱改成只寫行為，新名稱與 Example 驗證的「看到已滿的提示」相同，新的文案由步驟帶入。

```gherkin
# backend/房間.feature
  Rule: 房間滿員時再加入的玩家必須看到已滿的提示

    Example: 第三位玩家以暗號加入已滿的房間
      When "丙" 以暗號 "1234" 加入房間
      Then "丙" 看到 "房間已滿，請換一個暗號"

# frontend/房間.feature
  Rule: 房間滿員時再加入的玩家必須看到已滿的提示
```

### Bad Example

這個範例只把新的文案換進 backend 的名稱；每次改文案都要再改一次名稱，漏記改名時 task 會把舊名稱當成撤回的 Rule，為已實作的程式排出移除任務，frontend 的同名 Rule 也與 backend 不再一致。

```gherkin
# backend/房間.feature
  Rule: 房間滿員時必須顯示「房間已滿，請換一個暗號」

    Example: 第三位玩家以暗號加入已滿的房間
      When "丙" 以暗號 "1234" 加入房間
      Then "丙" 看到 "房間已滿，請換一個暗號"

# frontend/房間.feature
  Rule: 房間滿員時必須顯示「房間已滿」
```
