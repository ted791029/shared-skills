# 基準來源標示規範

## Rule 1 -- 非 Markdown 基準在檔頭以註解標示來源

**強度：MUST**

基準不是 Markdown 時（例如 `.yaml`、`.puml`、`.sql`），內容維持該格式原本的寫法，不規範條目結構；必須在檔案開頭以該格式的註解語法寫出來源與轉錄方式（「逐字」或「摘要」），來源沒有版本時改寫取得日期。格式規定第一行必須是特定內容時（例如 `.puml` 的 `@startuml`），註解緊接在其後。

### Good Example

這個範例在 YAML 開頭以 `#` 註解寫出來源與轉錄方式。

```yaml
# 來源：docs/api/openapi.yaml（2026-10 版）的 components.schemas.ErrorResponse
# 轉錄方式：逐字
ErrorResponse:
  type: object
  required: [code, message]
  properties:
    code:
      type: string
    message:
      type: string
```

### Bad Example

這個範例沒有標示來源，OpenAPI 文件更新後無從得知這份基準對應哪一版，也無法判斷能否逐字比對。

```yaml
ErrorResponse:
  type: object
  required: [code, message]
  properties:
    code:
      type: string
    message:
      type: string
```

## Rule 2 -- 無法寫註解的格式在索引檔標示來源

**強度：MUST**

基準的格式沒有註解語法時（例如 `.json`、圖片），必須在同一個資料夾的 `索引.md` 逐檔列出檔名、來源與轉錄方式，不得為了寫入來源而改變該檔案的內容或格式。

### Good Example

這個範例的 JSON 無法寫註解，來源寫在同資料夾的索引檔。

```markdown
# 錯誤回應樣本 索引

| 檔案 | 來源 | 轉錄方式 |
|---|---|---|
| order-not-found.json | `docs/api/samples/order-not-found.json`（2026-10 版） | 逐字 |
```

### Bad Example

這個範例為了標示來源在 JSON 加入來源沒有的欄位，基準不再與來源相同，逐字比對時會多出一個欄位。

```json
{ "_source": "docs/api/samples/order-not-found.json", "code": "ORDER_NOT_FOUND", "message": "找不到訂單 20261011-001" }
```
