# feature 規劃規範

## Rule 1 -- 依使用者操作的功能分 feature

**強度：MUST**

驗收 feature 依使用者操作的功能分檔，例如匯入照片、瀏覽相簿、相簿排序、刪除照片，檔名使用中文功能名稱；不得依使用者故事編號、優先順序、前後端或起點分檔。一個使用者故事橫跨多個功能時，其旅程放到旅程主要操作的功能底下。

### Good Example

這個範例依功能分檔，PM 想看「排序」怎麼驗收時只要開一份檔案。

```text
features/acceptance/匯入照片.feature
features/acceptance/瀏覽相簿.feature
features/acceptance/相簿排序.feature
features/acceptance/刪除照片.feature
```

### Bad Example

這個範例依使用者故事分檔，「自訂順序後匯入新日期」同時屬於 US1 與 US3，不知該放哪一份，PM 找排序的驗收流程得翻遍多份檔案；依起點拆成「匯入照片（已有相簿）」也是同樣的問題。

```text
features/acceptance/使用者故事1.feature
features/acceptance/使用者故事3.feature
```

## Rule 2 -- Background 只在所有 AC 共用起點時才抽

**強度：MUST**

每個 AC 從它的旅程需要的起點出發撰寫，起點在動筆前不預先決定。同一份 feature 的 AC 全部寫完後，所有 AC 的起點句相同時才把起點句抽成 Background；只要有一個 AC 的起點不同，就不寫 Background，每個 AC 的第一句寫 `Given 系統處於 "<起點名稱>"`。不得為了抽出 Background 把 AC 拆到另一份 feature，也不得讓 AC 從它不需要的狀態出發（例如取所有 AC 共同經過的最深狀態）來湊出共同起點。以下 Example 皆對照此匯入照片的旅程：

```text
AC-01 第一次匯入資料夾：需要還沒有任何相簿
AC-02 匯入含重複檔名的資料夾：需要三天各有照片的相簿
```

### Good Example

這個範例的兩個 AC 起點不同，因此不寫 Background，各自以起點句開頭，同一功能的兩段旅程留在同一份 feature。

```gherkin
Feature: 匯入照片

  Rule: 匯入後必須依拍攝日期建立相簿

    # 涵蓋：US1、FR-001、FR-002
    Example: AC-01 第一次匯入含三天照片的資料夾
      Given 系統處於 "無相簿"
      When 匯入資料夾 "D:/photos/trip"
      Then 主頁依序顯示下列相簿：
        | 相簿                    | 照片數 |
        | 2026年10月1日（星期四） | 5      |

  Rule: 重複檔名的照片必須略過

    # 涵蓋：US1、FR-003
    Example: AC-02 再匯入一個含重複檔名的資料夾
      # 預設值：已匯入 2026-10-01 的 P1～P5、2026-10-02 的 Q1～Q3、2026-10-03 的 R1～R2
      Given 系統處於 "三日十張"
      When 匯入資料夾 "D:/photos/trip2"
      Then 顯示略過 2 張重複檔名的照片
```

### Bad Example

這個範例為了讓每份都有 Background，把起點不同的 AC-02 拆到另一份 feature，PM 想看匯入照片怎麼驗收得開兩份檔案，新增匯入的旅程時也不知道該放哪一份。

```text
features/acceptance/匯入照片.feature            Background：無相簿
features/acceptance/匯入照片（已有相簿）.feature  Background：三日十張
```

## Rule 3 -- 起點內容必須寫在預設值註解

**強度：MUST**

起點句寫在 Background 或 AC 的第一句，起點名稱是業務名稱，不含技術說法；起點不是「無資料」時，必須在起點句上方以 `# 預設值：` 註解寫出起點包含的資料，讓 PM 不用查其他文件就能知道起點長什麼樣子。

### Good Example

這個範例在起點句上方列出三天的照片，PM 能直接看懂後續斷言中的照片數從哪來。

```gherkin
  Background:
    # 預設值：已匯入 2026-10-01 的 P1～P5、2026-10-02 的 Q1～Q3、2026-10-03 的 R1～R2，主頁尚未自訂順序
    Given 系統處於 "三日十張"
```

### Bad Example

這個範例只寫起點名稱，PM 看到斷言中「照片數 5」時無從得知這 5 張是哪一天的照片，也無法判斷斷言是否正確。

```gherkin
  Background:
    Given 系統處於 "三日十張"
```

## Rule 4 -- 功能與起點的名稱沿用 truth 已有的

**強度：MUST**

`specs/truth/features/` 已有同一個功能的 feature 時，驗收 feature 沿用它的檔名與 Feature 名稱；只有新功能才以功能另取名稱。被移除的功能不再有自己的 feature，驗收它已不存在的旅程放在使用者實際操作的既有功能底下。AC 的起點與 truth 用語表「端點」表登記的可用起點是同一個狀態時，沿用它的起點名稱，起點的內容以 truth 中使用它的各 feature 的 `# 預設值：` 註解共同的部分為準；這次的需求只是為既有起點拿掉被移除的功能，或加上新資料的初始狀態（例如還沒有任何紀錄）時，名稱不變，在預設值註解寫出改變後的內容。核心狀態不同時才取新的起點名稱。專案的第一個 plan 沒有 truth 的 feature，名稱自行決定。以下 Example 皆對照此 truth 現況與需求：

```text
specs/truth/features/frontend/：匯入照片.feature、瀏覽相簿.feature、相簿排序.feature、刪除照片.feature
truth 用語表的可用起點：系統處於 "無相簿"、系統處於 "三日十張"
truth 中「三日十張」的預設值：已匯入 2026-10-01 的 P1～P5、2026-10-02 的 Q1～Q3、2026-10-03 的 R1～R2，主頁尚未自訂順序
這次的需求：照片可以加上標籤並依標籤篩選；移除相簿的自訂排序，主頁一律依日期排列
```

### Good Example

這個範例的新功能以功能命名；移除自訂排序後，主頁依日期排列的旅程放在使用者實際操作的瀏覽相簿，沿用 truth 的檔名；起點沿用「三日十張」，預設值拿掉「主頁尚未自訂順序」。

```gherkin
# features/acceptance/照片標籤.feature
Feature: 照片標籤

# features/acceptance/瀏覽相簿.feature
Feature: 瀏覽相簿

  Background:
    # 預設值：已匯入 2026-10-01 的 P1～P5、2026-10-02 的 Q1～Q3、2026-10-03 的 R1～R2
    Given 系統處於 "三日十張"
```

### Bad Example

這個範例另取檔名與起點名稱；下游把旅程衍生到一份新的 feature，truth 同一個狀態有「三日十張」與「三天的照片」兩個名稱，舊名稱的預設值仍寫著自訂順序，兩者的測試會各自維護。

```gherkin
# features/acceptance/主頁依日期排列.feature
Feature: 主頁依日期排列

  Background:
    # 預設值：已匯入 2026-10-01 的 P1～P5、2026-10-02 的 Q1～Q3、2026-10-03 的 R1～R2
    Given 系統處於 "三天的照片"
```
