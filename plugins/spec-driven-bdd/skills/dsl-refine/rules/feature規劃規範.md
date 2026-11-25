# feature 規劃規範

## Rule 1 -- 端點內依功能分 feature 且沿用 acceptance 檔名

**強度：MUST**

同一端點的 Example 依使用者操作的功能分 feature，從某份 acceptance feature 衍生的 Example 放在與它同名的 feature（例如 `acceptance/改答案.feature` 衍生到 `backend/改答案.feature`）；補充案例放進它所屬功能的 feature；`specs/truth/features/` 既有的 Rule 已描述同一條規則時，留在它原本所在的 feature；整份 feature 被刪除而其中仍成立的 Rule，移到它所屬功能的 feature，盤點記為原本位置的刪除與新位置的新增。不得依 AC 編號、使用者故事、介面 ID、起點或品質面向（速度、用語、無障礙）分檔；只有無法歸到單一功能的全域要求，才集中到一份「整體品質要求」。以下 Example 皆對照此 acceptance：

```text
features/acceptance/改答案.feature
features/acceptance/連猜三次.feature
features/acceptance/技能特效.feature
```

### Good Example

這個範例每個端點都沿用 acceptance 的檔名，讀者從 acceptance 的「改答案」能直接找到每個端點對應的 feature。

```text
frontend/改答案.feature
frontend/連猜三次.feature
backend/改答案.feature
backend/連猜三次.feature
```

### Bad Example

這個範例依 AC 編號分檔，同一功能的規則散在多份，改答案的補充案例不知該放哪一份，讀者也無法從 acceptance 對回來。

```text
backend/AC-01.feature
backend/AC-02.feature
backend/AC-03.feature
```

## Rule 2 -- Background 只在所有 Example 共用起點時才抽

**強度：MUST**

同一份 feature 的 Example 全部寫完後，所有 Example 的起點句相同時才把起點句抽成 Background，不在規劃階段決定；只要有一個 Example 需要不同起點，就不寫 Background，每個 Example 的第一句寫 `Given 系統處於 {起點}`，起點句上方以 `# 預設值：` 註解寫出起點包含的資料。不得為了抽出 Background 把 Example 拆到另一份 feature，也不得讓 Example 從它不需要的狀態出發來湊出共同起點。以下 Example 皆對照此 feature 的 Example 起點：

```text
backend/改答案.feature
  甲送出新答案 12：從 對戰開始輪到甲
  雙方各猜兩次後甲送出新答案 1123：從 雙方各猜兩次
```

### Good Example

這個範例的兩個 Example 起點不同，因此不寫 Background，各自以起點句開頭並註明預設值，同一條 Rule 的兩種情境留在同一份 feature。

```gherkin
Feature: 改答案

  Rule: 不符合四碼規則的新答案必須被拒絕

    Example: 甲送出新答案 12
      # 預設值：房主甲的祕密答案為 0123、加入者乙的祕密答案為 5678，第 1 回合輪到甲；雙方的改答案與連猜三次各剩 1 次
      Given 系統處於 "對戰開始輪到甲"
      When "甲" 送出新答案 "12"
      Then 系統拒絕這次"改答案"，因為 "四碼規則不符（格式）"

    Example: 雙方各猜兩次後甲送出新答案 1123
      # 預設值：房主甲的祕密答案為 0123、加入者乙的祕密答案為 5678，雙方依序猜了 1234、0132、1357、3210，第 3 回合輪到甲；雙方的改答案與連猜三次各剩 1 次
      Given 系統處於 "雙方各猜兩次"
      When "甲" 送出新答案 "1123"
      Then 系統拒絕這次"改答案"，因為 "四碼規則不符（重複數字）"
```

### Bad Example

這個範例為了讓每份都有 Background 而依起點拆成兩份，同一條 Rule 分散在兩個檔案，讀者在任何一份都看不到這條規則的全部情境，增加情境時也不知道該放哪一份。

```text
backend/改答案.feature              Background：對戰開始輪到甲
  Rule: 不符合四碼規則的新答案必須被拒絕 → 甲送出新答案 12
backend/改答案（雙方各猜兩次）.feature  Background：雙方各猜兩次
  Rule: 不符合四碼規則的新答案必須被拒絕 → 甲送出新答案 1123
```

## Rule 3 -- Example 從它需要的起點出發

**強度：MUST**

每個 Example（AC 衍生與補充案例）從它需要的起點出發，起點名稱依 Rule 5 選用。起點之後，AC 的 Given 與該組 When 之前各組的動作，都改寫成 Example 的 Given 差異句；不得用 acceptance 沒有定義的狀態名稱代替差異句。以下 Example 皆對照此 AC 與 acceptance 登記的起點：

```gherkin
      When "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      Then "甲" 的畫面顯示目前答案 "4567"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"
```

```text
acceptance 登記的起點：對戰開始輪到甲、雙方各猜兩次
```

### Good Example

這個範例的 AC 衍生 Example 從 AC 的起點出發並把第 1 組改寫成差異句，讀者看得到新答案是怎麼來的；補充案例選用 acceptance 另一個起點「雙方各猜兩次」，驗證同一條猜測規則在第 3 回合也成立。

```gherkin
    Example: 甲把答案改為 4567 後猜 5679
      # 預設值：房主甲的祕密答案為 0123、加入者乙的祕密答案為 5678，第 1 回合輪到甲；雙方的改答案與連猜三次各剩 1 次
      Given 系統處於 "對戰開始輪到甲"
      And "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"

    Example: 雙方各猜兩次後甲把答案改為 4567 再猜 5679
      # 預設值：房主甲的祕密答案為 0123、加入者乙的祕密答案為 5678，雙方依序猜了 1234、0132、1357、3210，第 3 回合輪到甲；雙方的改答案與連猜三次各剩 1 次
      Given 系統處於 "雙方各猜兩次"
      And "甲" 開啟改答案
      And "甲" 送出新答案 "4567"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"
```

### Bad Example

這個範例在 Example 裡用自創的狀態名稱代替差異句，acceptance 沒有定義「已改答案」，寫測試的人只能猜新答案是什麼；為了讓起點看起來不同而自創起點名稱也是同樣的問題。

```gherkin
    Example: 甲把答案改為 4567 後猜 5679
      Given 系統處於 "已改答案"
      When "甲" 猜 "5679"
      Then 雙方畫面顯示輪到 "乙"
```

## Rule 4 -- 狀態是驗證資料時保留名稱

**強度：MUST**

Rule 本身要驗「在下列每一種狀態都要如何」時，狀態就是該 Rule 的測試資料，保留狀態名稱並列出（短名稱寫成以「、」分隔的列表參數，多欄資料用 Data Table，步驟只差資料時用 Scenario Outline），不改寫成差異句。只是前提的狀態仍依 Rule 3 改寫。

### Good Example

這個範例的 Rule 驗證四種畫面都沒有嚴重違規，畫面就是資料，因此保留畫面名稱、以列表參數列出。

```gherkin
  Rule: 所有畫面都不能有嚴重的無障礙違規

    Example: 首頁、等待畫面、準備畫面與對戰畫面
      When 掃描 "首頁、等待畫面、準備畫面、對戰畫面" 的無障礙問題
      Then 嚴重違規為 0 個
```

### Bad Example

這個範例把要驗證的四種畫面改寫成一長串差異句操作，Example 看不出「每一種畫面都要驗」，新增一種畫面時也得重寫整段步驟。

```gherkin
    Example: 首頁、等待畫面、準備畫面與對戰畫面
      Given 開啟首頁
      And 以暗號 "9876" 開房
      And 雙方進入準備畫面後開始遊戲
      When 掃描目前畫面的無障礙問題
      Then 嚴重違規為 0 個
```

## Rule 5 -- 起點名稱沿用 acceptance，儲存端點可自訂

**強度：MUST**

起點名稱（寫在 Background 或 Example 的第一句）與 `# 預設值：` 註解逐字沿用 acceptance 的起點；畫面與 API 端點不得新增 acceptance 沒有的起點名稱，需要更深的狀態時以差異句從既有起點推進。儲存端點（使用 `templates/database/` 或 `templates/filesystem/` 樣板的端點）可以沿用 acceptance 的起點，也可以使用本端點自訂的起點名稱，自訂起點只描述資料表列或檔案的內容，以業務用語命名，並在起點句上方以 `# 預設值：` 寫出起點資料。用語表「端點」的可用起點欄只列該端點用到的起點，自訂起點也登記在這一欄。這次的 acceptance 改變了某個起點的預設值時（例如拿掉被移除的功能），該端點所有使用這個起點的 feature 的 `# 預設值：` 註解都必須一併修改並列入盤點，不得只改這次有案例的 feature。以下 Example 皆對照此 acceptance 起點與用語表端點表：

```gherkin
  Background:
    # 預設值：房主甲的祕密答案為 0123、加入者乙的祕密答案為 5678，雙方已進入對戰畫面，第 1 回合輪到甲；雙方的改答案與連猜三次各剩 1 次
    Given 系統處於 "對戰開始輪到甲"
```

```markdown
| UI | `frontend` | … | `templates/frontend/` | 系統處於 "對戰開始輪到甲" |
| FS | `filesystem` | … | `templates/filesystem/` | 系統處於 "空儲存區" |
```

### Good Example

這個範例的前端逐字沿用 acceptance 的起點名稱與預設值註解，PM 對照衍生 feature 與 AC 時起點一致；檔案系統端使用登記在用語表的自訂起點，並以預設值註解寫出儲存區內容。

```gherkin
# frontend/改答案.feature
  Background:
    # 預設值：房主甲的祕密答案為 0123、加入者乙的祕密答案為 5678，雙方已進入對戰畫面，第 1 回合輪到甲；雙方的改答案與連猜三次各剩 1 次
    Given 系統處於 "對戰開始輪到甲"

# filesystem/照片檔案儲存.feature
  Background:
    # 預設值：儲存區根目錄為空，沒有任何原始檔、縮圖或暫存檔
    Given 系統處於 "空儲存區"
```

### Bad Example

這個範例的前端自創 acceptance 沒有的起點名稱，與 acceptance 對不上，「假 API」也讓讀 feature 的 PM 看不懂，換掉測試替身時所有 Background 都得改。

```gherkin
# frontend/改答案.feature
  Background:
    Given 系統處於 "對戰中（假 API、token 已注入）"
```

## Rule 6 -- 每份 feature 標一個模組標籤

**強度：MUST**

每份 feature 在 `Feature:` 上一行標一個 `@module:<模組名稱>`，模組名稱取自用語表「模組」段的繁體中文名稱，是這份 feature 描述的功能所屬的領域；不得標多個模組標籤，也不得使用用語表沒有登記的名稱。新的功能不屬於任何已登記的模組時，先在用語表新增模組再標示。模組名稱只能包含中文字、英文字母、數字與底線，不得含空白或標點符號。以下 Example 皆對照此用語表模組段：

```markdown
| 技能 | 改答案與連猜三次的使用、次數與特效 | frontend/改答案、backend/改答案、frontend/連猜三次、backend/連猜三次 |
| 對戰 | 猜測、回合歸屬、勝負與猜測紀錄資料表 | backend/猜測與勝負、database/猜測與勝負 |
```

### Good Example

這個範例的改答案屬於技能領域，只標一個用語表登記過的模組名稱。

```gherkin
@module:技能
Feature: 改答案

  Background:
    Given 系統處於 "對戰開始輪到甲"
```

### Bad Example

這個範例因為改答案後也會猜測就同時標兩個模組，還用了用語表沒有的「遊戲」，依模組篩選回歸測試時同一份 feature 會被重複執行，也找不到遊戲對應的 step 目錄。

```gherkin
@module:技能 @module:對戰 @module:遊戲
Feature: 改答案
```
