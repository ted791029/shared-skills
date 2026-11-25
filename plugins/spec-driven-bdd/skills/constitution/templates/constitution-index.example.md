# 專案憲法

**版本**：1.2.0 ｜ **最後修訂**：2026-10-25

本憲法只約束 SDD 流程中各 skill 的產出物內容與格式，不改變流程本身。

- `skills/<產出 skill>/<產出物>.md` 約束該 skill 的一份產出物；檔案不存在代表該產出物沿用 skill 內建規範。
- 任何寫入該產出物的 skill 都受同一份憲法檔約束，例如 clarify-over-specs 寫回 spec.md 時也遵循 `skills/specify/spec.md`。
- `shared/` 的共通條款不會自動生效，只有被產出物檔的「引用共通條款」列出時才約束該產出物。
- 覆寫內建 Rule 的條款必須在「覆寫對象」寫明被覆寫的 Rule。

## 目錄

| 產出物 | 憲法檔 | 條款 | 引用共通條款 |
| --- | --- | --- | --- |
| spec.md | [skills/specify/spec.md](skills/specify/spec.md) | C-SPEC-01、C-SPEC-02 | — |
| specs/truth/contracts/ | [skills/api-plan/contracts.md](skills/api-plan/contracts.md) | C-API-01、C-API-02 | C-SH-01 |
| specs/truth/data/ | [skills/data-plan/data.md](skills/data-plan/data.md) | C-DATA-01、C-DATA-02 | C-SH-01 |

## 共通條款

| 條款 | 檔案 |
| --- | --- |
| C-SH-01 | [shared/欄位命名風格.md](shared/欄位命名風格.md) |

## 修訂紀錄

| 版本 | 日期 | 異動條款 | 起因需求 |
| --- | --- | --- | --- |
| 1.0.0 | 2026-10-20 | 新增 C-SPEC-01、C-SPEC-02 | 規格書的安全與隱私、無障礙常被留白；回應時間只寫平均值，驗收時無法比對。 |
| 1.1.0 | 2026-10-22 | 新增 C-API-01、C-API-02 | 前端要用同一個函式拆解所有成功回應，並依錯誤代碼分流，不再比對訊息文字。 |
| 1.2.0 | 2026-10-25 | 新增 C-DATA-01、C-DATA-02、C-SH-01；C-API 引用 C-SH-01 | API 欄位與資料表欄位各自取名，後端實作時要另外記對應關係。 |
