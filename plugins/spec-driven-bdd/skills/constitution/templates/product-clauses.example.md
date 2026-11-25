# api-plan › specs/truth/contracts/

**引用共通條款**：[C-SH-01 欄位命名風格](../../shared/欄位命名風格.md)

## C-API-01 -- 成功回應一律包成 data 與 meta

**強度：MUST**
**作用位置**：`paths/*/*.yaml › *.responses.2XX.content.application/json.schema`、`paths/*/*.yaml › *.parameters`
**覆寫對象**：無（增補）

所有 2XX 回應的 schema 頂層必須是含 `data`、`meta` 兩個必填屬性的物件，資源本體放在 `data`。回傳多筆的操作，`parameters` 必須引用 `components/parameters/Page.yaml` 與 `components/parameters/PageSize.yaml`，`meta` 必須含 `total`、`page`、`pageSize`；回傳單筆的操作，`meta` 為空物件。

### Good Example

這個範例的列表操作以共用參數接收分頁，回應把相簿陣列放在 `data`、分頁資訊放在 `meta`，前端可以用同一個函式拆解所有回應。

```yaml
  parameters:
    - $ref: ../../components/parameters/Page.yaml
    - $ref: ../../components/parameters/PageSize.yaml
  responses:
    "200":
      content:
        application/json:
          schema:
            type: object
            required: [data, meta]
            properties:
              data:
                type: array
                items:
                  $ref: ../../components/schemas/Album.yaml
              meta:
                $ref: ../../components/schemas/PageMeta.yaml
```

### Bad Example

這個範例直接回傳陣列，沒有 `meta` 可以放總筆數，前端無法得知還有沒有下一頁。

```yaml
  responses:
    "200":
      content:
        application/json:
          schema:
            type: array
            items:
              $ref: ../../components/schemas/Album.yaml
```

## C-API-02 -- 錯誤回應必須附業務錯誤代碼

**強度：MUST**
**作用位置**：`components/schemas/Error.yaml`
**覆寫對象**：無（增補）

Error 必須含必填的 `code` 與 `message`。`code` 為 `大寫領域_大寫原因` 格式的字串，並以 `enum` 列出本產出物用到的全部代碼。

### Good Example

這個範例的 Error 列舉了所有代碼，前端可以依 `code` 分流處理，不必比對訊息文字。

```yaml
type: object
required: [code, message]
properties:
  code:
    type: string
    enum: [ROOM_FULL, ROOM_NOT_FOUND, SESSION_MISSING, NAME_INVALID]
  message:
    type: string
    description: 繁體中文。說明發生什麼事，以及可以怎麼做。
    examples:
      - 房間已滿，請換一個暗號再試一次。
      - 找不到這間房間，可能已經關閉。
```

### Bad Example

這個範例只有 `message`，前端要判斷「房間已滿」只能比對中文字串，文案一改，判斷就失效。

```yaml
type: object
required: [message]
properties:
  message:
    type: string
    description: 繁體中文。說明發生什麼事，以及可以怎麼做。
    examples:
      - 房間已滿，請換一個暗號再試一次。
      - 找不到這間房間，可能已經關閉。
```
