# API 錯誤回應規範

## Rule 1 -- 錯誤回應必須使用統一結構

**強度：MUST**

所有 4xx 與 5xx 回應的 body 必須包含 `code` 與 `message` 兩個欄位，`code` 使用大寫蛇形字串。

### Good Example

這個範例包含 `code` 與 `message`，且 `code` 使用大寫蛇形字串。

```json
{ "code": "ORDER_NOT_FOUND", "message": "找不到訂單 20261011-001" }
```

### Bad Example

這個範例以單一 `error` 欄位取代 `code` 與 `message`，前端無法依 `code` 分流處理，只能解析字串猜測錯誤類型。

```json
{ "error": "order not found" }
```

## Rule 2 -- 錯誤訊息不得暴露內部細節

**強度：MUST**

`message` 只能描述使用者可理解的錯誤原因，不得包含 stack trace、SQL 語句、內部主機名稱或檔案路徑。

### Good Example

這個範例的 `message` 只說明使用者可理解的原因，沒有任何內部細節。

```json
{ "code": "PAYMENT_DECLINED", "message": "信用卡授權失敗，請改用其他付款方式" }
```

### Bad Example

這個範例在 `message` 夾帶 SQL 語句與主機名稱，攻擊者可據此推測資料表結構與內部網路配置。

```json
{ "code": "INTERNAL_ERROR", "message": "SQLException at db-prod-02: SELECT * FROM payments WHERE id = 381" }
```
