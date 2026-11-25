# API 分析規範

## Rule 1 -- 每個外層需要都必須有對應的 API

**強度：MUST**

前置產出中每一項需要內層提供的資料與動作，都必須對應到至少一個 API 操作；外層寫「無」的操作不得為其新增 API。API 與外層操作的對應關係寫在 plan 的 `truth-changes.md` 中 api-plan 一節的「改動摘要」欄，不寫進契約。

### Good Example

這個範例的每個外層需要都有對應的 API，對應關係寫在 truth 異動紀錄的改動摘要，契約本身不帶追溯。

```markdown
| 異動 | 對象 | 改動摘要 | 原因 |
|---|---|---|---|
| ADD | `contracts/paths/匯入/api_photos.yaml` | 整份檔案，1 個操作：POST /api/photos，服務 UI-02「開始匯入」 | FR-001 |
| ADD | `contracts/paths/相簿/api_albums.yaml` | 整份檔案，1 個操作：GET /api/albums，服務 UI-01「查看相簿列表」 | FR-007 |
```

### Bad Example

這個範例為前端已註明「無（前端先過濾）」的格式過濾另開路徑檔 `paths/匯入/api_photos_validate.yaml`，多出沒有呼叫者的端點，也讓前後端對過濾責任各有一套說法。

```yaml
post:
  tags:
    - 匯入
  summary: 檢查檔案格式
```

## Rule 2 -- x-inner-needs 只列資料名稱與存取方式

**強度：MUST**

每個 API 操作必須有 `x-inner-needs`：`data` 列出讀寫的資料名稱與存取方式（read、write、delete），`files` 列出讀寫的儲存區與存取方式。同一個名稱只列一次，同時讀寫時取較強的存取（delete 高於 write，write 高於 read）；不列欄位，欄位由 request 與 response 的 schema 表達。沒有對象時寫空陣列，不得省略此欄位，內層的 Planner 依它推導資料表與儲存區。

### Good Example

這個範例的刪除操作每個名稱只列一次並取最強的存取，沒有列欄位，資料與兩個儲存區都在。

```yaml
  x-inner-needs:
    data:
      - name: photos
        access: delete
      - name: albums
        access: delete
    files:
      - name: originals
        access: delete
      - name: thumbnails
        access: delete
```

### Bad Example

這個範例把 photos 依讀與刪各列一次並附上欄位清單，欄位與 schema 重複，改一個欄位就要改兩處，契約也因此長到難以閱讀。

```yaml
  x-inner-needs:
    data:
      - name: photos
        access: read
        fields: [id, album_id, content_hash, taken_at]
      - name: photos
        access: delete
        fields: [id]
      - name: albums
        access: delete
        fields: [id]
    files:
      - name: originals
        access: delete
      - name: thumbnails
        access: delete
```

## Rule 3 -- 錯誤回應必須使用共用結構並遵循文案要求

**強度：MUST**

每個可能失敗的操作必須列出對應的錯誤狀態碼，回應本文一律引用 `components/schemas/Error.yaml`；Error 的訊息語言與寫法必須遵循 spec.md 的要求，並以 `examples` 列出代表性訊息。

### Good Example

這個範例的錯誤回應引用共用結構，訊息例子說明發生什麼與可以怎麼做。

```yaml
    '415':
      description: 不支援的檔案格式
      content:
        application/json:
          schema:
            $ref: ../../components/schemas/Error.yaml
```

### Bad Example

這個範例為單一操作自訂錯誤結構，前端必須為每個 API 寫不同的錯誤處理。

```yaml
    '415':
      description: 不支援的檔案格式
      content:
        application/json:
          schema:
            type: object
            properties:
              err_code:
                type: integer
```

## Rule 4 -- 操作 description 只寫用途與介面約定

**強度：MUST**

操作的 `description` 以一到三句寫出這個操作做什麼，以及呼叫方必須知道、但結構表達不出的約定（例如要搭配哪個操作使用、成功後推播什麼事件）。不得寫介面 ID、UI 編號或 FR、NFR 等追溯編號，不得寫判定先後順序、寫入哪些欄位、鎖與交易，也不得寫業務規則；業務規則由 spec.md 的需求經 dsl-refine 成為 feature 的 Rule。

### Good Example

這個範例用兩句寫出操作做什麼，以及 `beforeAlbumId` 為空時的約定，沒有追溯、實作細節或業務規則。

```yaml
  summary: 移動相簿順序
  operationId: moveAlbum
  description: 把指定相簿移到另一本之前；beforeAlbumId 為空表示移到最後。
```

### Bad Example

這個範例把追溯編號、判定順序、寫入欄位與業務規則都寫進 description，同一件事同時存在於 plan、資料模型與 feature，改一處就與其他處不一致，說明也長到難以閱讀。

```yaml
  summary: 移動相簿順序
  operationId: moveAlbum
  description: >-
    介面 API-02，對應 UI-02「拖曳排序」（FR-007）。在交易內依序判定：相簿存在（否則 404）→ beforeAlbumId 存在（否則 422）；
    成功時重算所有相簿的 position 並把 order_mode 改為 custom；自訂順序後新匯入的相簿一律排在最後（FR-009）。
```

## Rule 5 -- 回應與欄位說明只寫一行意義

**強度：MUST**

response 的 `description` 以一行寫出該狀態碼代表的結果與可能的 `code`；schema 屬性的 `description` 以一句寫出欄位意義，以及何時為 null 或有特殊值。不得寫追溯編號、計算方式或業務規則。需求決定的界限與列舉（例如每局可以使用的次數上限）只以 `minimum`、`maximum`、`enum` 等 schema 關鍵字表達，說明不再重述數值；契約對應哪些需求記在 truth-changes.md 的原因欄與 plan.md 的介面列，不在契約中以編號引用。

### Good Example

這個範例的回應說明一行寫出結果與 code，欄位說明一句寫出意義與 null 的時機；次數上限只寫在 `maximum`，說明不重述數值。

```yaml
    '409':
      description: 相簿已被刪除或順序已被改動（code 為 album_gone 或 order_conflict）
```

```yaml
  cover_photo_id:
    type: [string, "null"]
    description: 封面照片；相簿沒有照片時為 null
```

```yaml
  change_answer_left:
    type: integer
    minimum: 0
    maximum: 1
    description: 這一局還能使用改答案的次數；用完時為 0
```

### Bad Example

這個範例在欄位說明寫進追溯編號、後端的重算方式與前端的顯示行為，讀者要讀完一段才找到欄位意義，重算方式改了也不會有人記得回來改這裡。

```yaml
  cover_photo_id:
    type: [string, "null"]
    description: >-
      封面照片（FR-004、UI-01「相簿卡片」）。後端在每次匯入與刪除後，以 taken_at 最早的照片重算並寫入 albums.cover_photo_id；
      相簿沒有照片時為 null，前端改顯示預設圖。
```

## Rule 6 -- 上游問題只回報不自行修改

**強度：MUST**

分析或判斷差異時發現上游問題，必須只回報，不得自行修改上游的產物，也不得為受影響的 API 增修契約；不受影響的 API 照常完成，這次的結果是「不能改」。上游問題與交給的對象如下：

| 上游問題 | 交給 |
|---|---|
| 要新增、修改或移除的 API 所屬的資源在 plan.md 的介面盤點沒有 ADD、MOD、DEL 的列（包括標「無」的介面），或介面列的依據需求缺了驅動它的需求 | system-analysis：回報要新增或修改的介面列（介面、異動，以及依據需求或「技術：」開頭的原因） |
| 前置端點的產出錯了或缺了（例如 UI 契約的需要內層提供與畫面的操作互相矛盾） | 經 dev-finding 記錄，交給回覆寫明的應修正的擁有者 |

技術項或交辦要改的 API 所屬的介面在本 plan 已是 ADD 或 MOD 時，技術項就是依據，不算依據需求缺漏。多個介面的操作共用的 schema 沒有自己的介面列，以驅動這次修改的需求或技術項所在的介面列為依據：該列是 ADD 或 MOD 即可修改，引用它的其他介面不必也是 MOD，truth-changes 的改動摘要寫出受影響的其他操作。技術修正 plan 沒有 plan.md，介面盤點的問題不適用本條。以下 Example 皆對照此介面列與前置產出：

```text
本 plan 的介面列：
| UI-02 | 結果畫面介面（排行榜入口） | 前端 | ADD | FR-001 |
| API-01 | 房間 API（快照的戰績） | 後端 | MOD | FR-001 |
前置產出（ui/ui-contract.md 的 UI-02）：
- 「查看排行榜」需要內層提供排行榜（暱稱、勝場數、名次）
- 「顯示戰績」需要內層提供自己的勝場數，同一節的文案卻是「{勝場數} 勝 {敗場數} 敗」
```

### Good Example

這個範例照常完成不受影響的勝場數；文案與需要內層提供互相矛盾的敗場數經 dev-finding 交給 UI 契約的擁有者，排行榜沒有可以承接的介面列則回報 system-analysis，兩者都不自行補上，沒有記錄。

```text
API-01 勝場數 → 快照新增勝場數，契約完成並通過檢查與核對。
API-01 敗場數 → 不能改：UI-02 的文案用到敗場數，需要內層提供卻沒有列出；經 dev-finding 記錄，應修正的擁有者 ui-ux-plan，改正後再判斷。
排行榜 → 不能改：介面盤點沒有後端的排行 API，UI-02「查看排行榜」需要的操作沒有可以承接的介面列；交給 system-analysis 新增後端「排行 API（列出排行榜）」的 ADD 列（FR-001）並排入 Wave。
這次沒有記錄，api-plan 仍是待補跑。
```

### Bad Example

這個範例自己在 plan.md 補上 API-02 並新增排行榜的路徑檔；plan.md 的修改沒有經過 system-analysis 與 check_plan.py 的檢查，同一個 Wave 中回報同一個問題的其他 Planner 也會各自改寫 plan.md 而互相覆蓋。

```text
已在 plan.md 的介面盤點補上「API-02 排行 API | 後端 | ADD | FR-001」，並新增 contracts/paths/排行/api_rankings.yaml；記錄改了。
```

## Rule 7 -- 契約必須讓涵蓋的 AC 成立

**強度：MUST**

涵蓋本端點介面列依據需求的 AC，每個步驟與斷言都必須能由契約的操作與回應達成：AC 要求的結果（例如操作後資料保留在哪個狀態、回應要帶哪個欄位）要寫進操作的回應與 schema，不得只依 FR 的文字設計出與 AC 相反或做不到 AC 的契約。AC 與 spec.md 的需求或前置端點的產出矛盾時不自行選邊，經 dev-finding 記錄並交給回覆寫明的應修正的擁有者，這次的結果是「不能改」。以下 Example 皆對照此需求與 AC：

```text
FR-005：客人可以取消自己的預約
AC-02（# 涵蓋：US1、FR-005）："王小明" 按 "取消預約" → 看到 "預約已取消"，而且預約清單仍列出這筆預約並標為 "已取消"
```

### Good Example

這個範例依 AC-02 讓取消操作保留預約，回應已取消的預約，`Booking` 的狀態列舉含 `cancelled`。

```yaml
post:
  summary: 取消預約
  operationId: cancelBooking
  description: 取消自己的預約；預約保留在清單中，狀態改為 cancelled。
  responses:
    '200':
      description: 已取消，回傳狀態為 cancelled 的預約
      content:
        application/json:
          schema:
            $ref: ../../components/schemas/Booking.yaml
```

### Bad Example

這個範例只依 FR-005 的「取消」設計成刪除預約；清單再也取得不到已取消的預約，AC-02 的「仍列出並標為已取消」做不到，要等 dsl-refine 衍生 AC-02 時才發現，再經 dev-finding 交回 api-plan 多走一輪。

```yaml
post:
  summary: 取消預約
  operationId: cancelBooking
  description: 取消並刪除自己的預約。
  responses:
    '204':
      description: 已刪除
```
