# 錯誤代碼表

- 來源：`docs/api/error-codes.md`（2026-10 版）
- 轉錄方式：逐字

| code | HTTP 狀態 | 訊息句型 |
|---|---|---|
| ORDER_NOT_FOUND | 404 | 找不到訂單 <訂單編號> |
| ORDER_CANCELLED | 409 | 訂單 <訂單編號> 已取消，無法再修改 |
| PAYMENT_DECLINED | 402 | 信用卡授權失敗，請改用其他付款方式 |
