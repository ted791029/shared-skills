# 開發發現 AC 規範

## Rule 1 -- 不得更動 PM 提出的 AC

**強度：MUST**

只能新增、改寫或刪除帶 `@開發發現` 標籤的驗收案例。沒有這個標籤的 Rule、Example、Background 與步驟一律不得修改、搬移或刪除，即使它與發現的行為矛盾；矛盾寫在新增的驗收案例與它的依據，由 PM 決定。以下 Example 皆對照此既有的 AC 與發現：

```gherkin
  Rule: 客人必須能取消自己的預約

    # 涵蓋：US1、FR-005
    Example: AC-02 "王小明" 取消 19:00 的預約
      Given 系統處於 "一筆已成立的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "預約已取消"
```

```text
發現：用餐前 2 小時內按「取消預約」，畫面顯示「用餐前 2 小時內無法取消」，預約維持成立
```

### Good Example

這個範例保留 AC-02 原樣，另外新增帶標籤的驗收案例。

```gherkin
  Rule: 客人必須能取消自己的預約

    # 涵蓋：US1、FR-005
    Example: AC-02 "王小明" 取消 19:00 的預約
      Given 系統處於 "一筆已成立的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "預約已取消"

  Rule: 用餐前 2 小時內不能取消預約

    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消，`specs/truth/contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml` 沒有這個回應
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
      Given 系統處於 "一筆 1 小時後用餐的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "用餐前 2 小時內無法取消"
```

### Bad Example

這個範例把發現的行為改進 PM 提出的 AC-02，PM 看過的驗收案例在沒有告知的情況下被改變，也分不出哪一句是開發加的。

```gherkin
  Rule: 客人必須能取消自己的預約

    # 涵蓋：US1、FR-005
    Example: AC-02 "王小明" 取消 19:00 的預約
      Given 系統處於 "一筆已成立的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "預約已取消"
      But 用餐前 2 小時內客人 "王小明" 看到 "用餐前 2 小時內無法取消"
```

## Rule 2 -- 放進所屬功能的 feature 並自成一條 Rule

**強度：MUST**

驗收案例放進使用者操作這個行為的功能所屬的 acceptance feature，在該 feature 最後新增一條 Rule，名稱寫出這個行為要成立的規則，不得放在 PM 提出的 Rule 之下。這個 plan 還沒有該功能的 acceptance feature 時新增一份：`specs/truth/features/` 已有這個功能的 feature 時沿用它的檔名與 Feature 名稱，沒有時以功能命名。以下 Example 皆對照此發現與既有的檔案：

```text
發現：用餐前 2 小時內按「取消預約」，畫面顯示「用餐前 2 小時內無法取消」，預約維持成立
這個 plan 的 features/acceptance/：只有 候補名單.feature
specs/truth/features/frontend/：建立預約.feature、取消預約.feature（內有取消預約的 Rule）
```

### Good Example

這個範例沿用 truth 中取消預約所在的 feature 名稱新增檔案，並自成一條 Rule。

```gherkin
# features/acceptance/取消預約.feature
Feature: 取消預約

  Rule: 用餐前 2 小時內不能取消預約

    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消，`specs/truth/contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml` 沒有這個回應
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
```

### Bad Example

這個範例把驗收案例塞進不相干的候補名單 feature，還放在 PM 提出的 Rule 之下；PM 分不出這條 Rule 哪些部分是自己提的，下游以同名的 feature 對應 truth 時，也會把取消預約的行為寫進候補名單的 feature。

```gherkin
# features/acceptance/候補名單.feature
Feature: 候補名單

  Rule: 額滿的時段必須能加入候補

    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消，`specs/truth/contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml` 沒有這個回應
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
```

## Rule 3 -- 以註解、標籤與編號標示每個發現

**強度：MUST**

每個發現只對應一個 Example。Example 上方依序為一行 `# 開發發現：<發現的 skill>；<依據>` 註解與 `@開發發現` 標籤；這行註解取代其他驗收案例的 `# 涵蓋：` 註解，標籤只放在 Example 上。標題以接續本 plan 最大 AC 編號的新編號開頭，使用過的編號不得重用。

### Good Example

這個範例依序有註解、標籤與接續的 AC 編號，沒有 `# 涵蓋：` 註解。

```gherkin
    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消，`specs/truth/contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml` 沒有這個回應
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
```

### Bad Example

這個範例把標籤放在 Rule 上，註解沒有寫發現的 skill，標題也沒有 AC 編號；檢查無法把它列為開發發現，下游也無法以編號引用它。

```gherkin
  @開發發現
  Rule: 用餐前 2 小時內不能取消預約

    # 開發發現：程式在用餐前 2 小時內拒絕取消
    Example: "王小明" 在用餐前 1 小時取消預約
```

## Rule 4 -- 依據必須可查證

**強度：MUST**

註解中的依據必須寫出現象在哪裡被觀察到，以及規格哪裡沒有寫或互相矛盾：程式寫到檔案與行號，規格寫到檔案與需求編號或 Rule 名稱。不得只寫無法回頭查證的說明。

### Good Example

這個範例寫出程式的位置與沒有寫到這個行為的規格檔案。

```gherkin
    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消，`specs/truth/contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml` 沒有這個回應
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
```

### Bad Example

這個範例的依據無法查證，PM 或審閱者想確認現象是否屬實時找不到出處。

```gherkin
    # 開發發現：api-plan；分析 API 時發現的
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
```

## Rule 5 -- 只驗這個發現的行為

**強度：MUST**

驗收案例從最接近的起點出發，只寫觸發這個行為所需的操作與使用者看得到的結果，顆粒度與 PM 提出的 AC 相同，PM 可以照著現場 Demo。結果寫程式的現況；還沒有實作時寫發現者判斷最合理的結果；發現者提議改變既有的行為時（發現分類規範 Rule 1 的提議），結果寫提議改成的結果，現況寫在依據，讓 PM 看到的是要決定的那一個結果。不得寫成選項或待定。不得順帶驗證其他行為，也不得寫入狀態碼、資料表內容等畫面上看不到的斷言。

### Good Example

這個範例從最接近的起點出發，只有一個操作與客人看得到的確定結果。

```gherkin
    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消，`specs/truth/contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml` 沒有這個回應
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
      Given 系統處於 "一筆 1 小時後用餐的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "用餐前 2 小時內無法取消"
      And 客人 "王小明" 的預約仍顯示為 "已成立"
```

### Bad Example

這個範例的斷言是狀態碼與資料表內容，PM 現場 Demo 時看不到，無法據此決定要不要這個行為。

```gherkin
    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消，`specs/truth/contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml` 沒有這個回應
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
      Given 系統處於 "一筆 1 小時後用餐的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 回應的狀態碼為 409
      And bookings 資料表中這筆預約的狀態仍為 "confirmed"
```

## Rule 6 -- 刪除與改寫只動使用者指定的 AC

**強度：MUST**

使用者表示這個 plan 不處理的 AC，連同它上方的註解與標籤整個刪除；它所在的 Rule 沒有其他 Example 時連 Rule 一起刪除，feature 沒有其他 Rule 時連檔案一起刪除。使用者要修改的 AC，照使用者的說法改寫標題、步驟與它所在 Rule 的名稱，標籤與 AC 編號保留，並在註解的依據後面補上使用者的修改。使用者沒有提到的 AC 一律不動，也不得自行修改 truth 或程式來配合。以下 Example 皆對照此既有內容與回覆：

```gherkin
  Rule: 用餐前 2 小時內不能取消預約

    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消
    @開發發現
    Example: AC-08 "王小明" 在用餐前 1 小時取消預約
      Given 系統處於 "一筆 1 小時後用餐的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "用餐前 2 小時內無法取消"

  Rule: 候補成功的客人必須看到通知

    # 開發發現：dsl-refine；`features/acceptance/候補名單.feature` 的 AC-05 沒有寫候補成功時客人看到什麼
    @開發發現
    Example: AC-09 "李小華" 候補的時段有人取消
      Given 系統處於 "一個額滿且有人候補的時段"
      When 客人 "王小明" 取消預約
      Then 客人 "李小華" 看到 "你候補的時段已有名額"
```

```text
使用者的回覆：AC-08 改成 3 小時；AC-09 不要
```

### Good Example

這個範例把 AC-08 的標題、步驟與 Rule 名稱改為 3 小時，保留標籤與編號並在依據後面補上使用者的修改；AC-09 連同它的 Rule 一起刪除。

```gherkin
  Rule: 用餐前 3 小時內不能取消預約

    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消；使用者改為 3 小時
    @開發發現
    Example: AC-08 "王小明" 在用餐前 2 小時取消預約
      Given 系統處於 "一筆 2 小時後用餐的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "用餐前 3 小時內無法取消"
```

### Bad Example

這個範例把使用者不要的 AC-09 留下並拿掉標籤，它變成看起來像 PM 提出的驗收案例，下游會照它實作。

```gherkin
  Rule: 用餐前 3 小時內不能取消預約

    # 開發發現：api-plan；`backend/app/services/bookings.py:118` 在用餐前 2 小時內拒絕取消；使用者改為 3 小時
    @開發發現
    Example: AC-08 "王小明" 在用餐前 2 小時取消預約
      Given 系統處於 "一筆 2 小時後用餐的預約"
      When 客人 "王小明" 按 "取消預約"
      Then 客人 "王小明" 看到 "用餐前 3 小時內無法取消"

  Rule: 候補成功的客人必須看到通知

    Example: AC-09 "李小華" 候補的時段有人取消
      Given 系統處於 "一個額滿且有人候補的時段"
      When 客人 "王小明" 取消預約
      Then 客人 "李小華" 看到 "你候補的時段已有名額"
```

## Rule 7 -- 保留並取代交給矛盾那一方的擁有者

**強度：MUST**

review 列出 AC 前，逐一比對每個標 `@開發發現` 的 AC 與 PM 提出的 AC（含它所在 Rule 的名稱）、spec.md 的 FR 與 NFR，列出矛盾之處：雙方在同一個情況下要求不同的結果，寫出雙方的編號與互相衝突的步驟或句子。有矛盾的 AC 在使用者回覆保留、沒有提到，或修改後仍矛盾時，一律以「保留並取代」處理：dev-finding 不改 PM 提出的 AC 與 spec.md，矛盾的 FR、NFR 交給 clarify-over-specs，矛盾的 PM 提出的 AC 交給 spec-by-example；交辦內容寫出保留的 AC 編號與原文、被取代的編號，以及要依它改寫的步驟或句子；兩者都有時先交 clarify-over-specs 再交 spec-by-example。不得讓矛盾的兩方同時留在這個 plan。以下 Example 皆對照此既有內容與回覆：

```text
spec.md：FR-005 客人在用餐前任何時間都能取消自己的預約
AC-02（PM 提出）："王小明" 在用餐前 1 小時取消預約 → 客人 "王小明" 看到 "預約已取消"
AC-08（@開發發現，api-plan）："王小明" 在用餐前 1 小時取消預約 → 客人 "王小明" 看到 "用餐前 2 小時內無法取消"；依據寫出餐廳要在 2 小時前把名額釋出給候補，與 FR-005、AC-02 矛盾
使用者的回覆：AC-08 保留
```

### Good Example

這個範例列出 AC-08 與 FR-005、AC-02 的矛盾，使用者保留後先交 clarify-over-specs 改寫 FR-005，再交 spec-by-example 改寫 AC-02，dev-finding 沒有自己改它們。

```text
AC-08 保留並取代：
1. 交給 clarify-over-specs：PM 保留 AC-08「用餐前 1 小時取消時看到『用餐前 2 小時內無法取消』」，請依它改寫 FR-005「客人在用餐前任何時間都能取消自己的預約」，用餐前 2 小時內不能取消。
2. 交給 spec-by-example：請依 AC-08 改寫 AC-02 的「在用餐前 1 小時取消」與「看到 預約已取消」，使它不再與 AC-08 矛盾。
```

### Bad Example

這個範例只回報保留，FR-005、AC-02 與 AC-08 同時留在 plan；dsl-refine 會為同一個操作衍生結果相反的兩條 Rule，其中一條的測試永遠失敗，或被默默挑掉一條，PM 的決定沒有反映在需求與驗收中。

```text
AC-08 保留，FR-005 與 AC-02 不動。
```

## Rule 8 -- 回報必須列出異動、取代與待補跑

**強度：MUST**

回報逐一列出每個 AC 的結果：被刪除或改寫的 AC 列出它造成的每一列 truth 異動（owner、對象與改動摘要），保留並取代的 AC 列出交給了哪個擁有者、改寫了哪一條，其餘 AC 只回報保留。最後依 plan-package check 的順序列出每個待補跑的擁有者、變了的輸入與執行方式，並寫明這些擁有者補跑完成前不得繼續拆任務或交付；沒有待補跑時寫明可以繼續。不得自行推測要重跑的 skill。以下 Example 皆對照此處理結果：

```text
AC-08 已改寫為 3 小時；它造成的 truth 異動：api-plan MOD `contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml`（新增「用餐前 2 小時內無法取消」的回應）
AC-09 已刪除；它沒有造成 truth 異動；註解中的發現者是 dsl-refine；它的行為已由勾選的任務實作
AC-10 保留並取代：已交給 spec-by-example 依 AC-10 改寫 AC-03
AC-11 沒有被提到，也沒有矛盾
check 的待補跑：
1. api-plan：plan:features/acceptance/取消預約.feature＞AC-08 MOD；via：/system-analysis 的依差異入口只重跑這個端點，或直接執行 /api-plan
2. dsl-refine：plan:features/acceptance/取消預約.feature＞AC-08 MOD、plan:features/acceptance/候補名單.feature＞AC-09 DEL、plan:features/acceptance/取消預約.feature＞AC-03 MOD；via：/dsl-refine
3. task：同 dsl-refine 的三個 AC；via：/task 的增量入口
```

### Good Example

這個範例逐一列出每個 AC 的結果、異動列與取代的交辦，依 check 的順序轉述待補跑，並寫明補跑完成前不得繼續。

```text
- AC-08 已改寫為 3 小時。受影響的 truth 異動：api-plan MOD `contracts/paths/預約/api_bookings_{bookingId}_cancel.yaml`（新增「用餐前 2 小時內無法取消」的回應）。
- AC-09 已刪除。沒有 truth 異動。
- AC-10 保留並取代：已交給 spec-by-example 依 AC-10 改寫 AC-03。
- AC-11 保留。

待補跑（依 plan-package check 的順序）：
1. api-plan：取消預約.feature 的 AC-08 改了。執行方式：/system-analysis 的依差異入口只重跑這個端點，或直接執行 /api-plan。
2. dsl-refine：AC-08 改了、AC-09 刪了、AC-03 改了。執行方式：/dsl-refine。
3. task：同上。執行方式：/task 的增量入口。

這些擁有者補跑完成前，請不要繼續拆任務或交付。
```

### Bad Example

這個範例自行推測要重跑的 skill，只寫了 AC-09 註解中的發現者；已經實作 AC-09 的 task 沒有列出，使用者重跑 dsl-refine 後就去交付，才被 plan-package 以待補跑擋下，PM 不要的行為要多走一輪才排出移除任務。

```text
- AC-08 已改寫為 3 小時。要重跑：api-plan。
- AC-09 已刪除。要重跑：dsl-refine（註解中的發現者）。

api-plan 與 dsl-refine 重跑完成前，請不要繼續。
```

## Rule 9 -- 已確認的 AC 不重複詢問

**強度：MUST**

review 只詢問三種 AC：check_findings.py 標為「未確認」的、標為「內容已改」的，以及與 PM 提出的 AC、FR 或 NFR 矛盾、而矛盾的對象不在它確認紀錄的「取代」之中的。已確認、內容沒有變、也沒有新矛盾的 AC 不再詢問，回報只列編號與「已確認」；它記下的取代對象仍然矛盾時，表示取代還沒完成，回報寫出由哪個擁有者待補跑完成，不再請使用者決定。使用者回覆後，以 check_findings.py 的 `--confirm` 記下這次詢問後保留或改寫的每個 AC 與它取代的對象；`.dev-finding.json` 只能由 `--confirm` 寫入，不得手動編輯。以下 Example 皆對照此情境：

```text
task 前的 review：PM 保留 AC-08（取代 AC-02）與 AC-09，已以 --confirm 記下
交付前的 review，check_findings.py 列出：
- AC-08：已確認，取代 AC-02；AC-02 已由 spec-by-example 改寫，兩者不再矛盾
- AC-09：已確認，內容沒有變；但 PM 在實作期間改寫了 AC-05，同一個情況下 AC-05 要求顯示「候補已滿」，AC-09 要求顯示「你候補的時段已有名額」
- AC-10：未確認（實作期間新增）
```

### Good Example

這個範例只詢問新增的 AC-10 與出現新矛盾的 AC-09，AC-08 只列為已確認；使用者回覆後以 --confirm 記下 AC-09 取代 AC-05。

```text
請確認以下開發發現（沒有提到的 AC 視為保留；有矛盾的 AC 保留時會以它取代矛盾的一方）：
- AC-10（未確認）："李小華" 在候補時段開放前 5 分鐘取消候補 …（Example 原文、發現的 skill 與依據）
- AC-09（已確認，但與 PM 改寫後的 AC-05 矛盾）："李小華" 候補的時段有人取消 …（Example 原文、發現的 skill、依據與矛盾的句子）
已確認、不再詢問：AC-08（取代 AC-02，已完成）

（使用者回覆：都保留）
uv run "D:/plugins/spec-driven-bdd/skills/dev-finding/scripts/check_findings.py" specs/plans/004-ranking --confirm AC-09=AC-05 --confirm AC-10
```

### Bad Example

這個範例把 task 前已確認、內容沒有變的 AC-08 再列一次；PM 每次 review 都要重讀已經決定過的內容，清單越來越長，新增的 AC-10 與 AC-09 的新矛盾反而容易被略過。

```text
請確認以下開發發現（沒有提到的 AC 視為保留）：
- AC-08："王小明" 在用餐前 1 小時取消預約 …
- AC-09："李小華" 候補的時段有人取消 …
- AC-10："李小華" 在候補時段開放前 5 分鐘取消候補 …
```
