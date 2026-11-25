| Wave | 端點 | Planner | 產出 | 狀態 |
|---|---|---|---|---|
| 1 | 前端 | `ui-ux-plan` | `ui/ui-contract.md`、`ui/prototype/` | 完成 |
| 2 | 後端 | `api-plan` | `specs/truth/contracts/`：新增 18、修改 0、刪除 0，見 [truth-changes.md](./truth-changes.md) 的 api-plan 一節 | 完成 |
| 3 | 資料庫端 | `data-plan` | `specs/truth/data/`：新增 3、修改 0、刪除 0，見 [truth-changes.md](./truth-changes.md) 的 data-plan 一節；`data-migration.md` | 完成 |
| 3 | 檔案系統端 | `storage-plan` | — | 不能改 |

## 不能改

| 端點 | 擋住的規則、條款或上游事實 | 應交給 |
|---|---|---|
| 檔案系統端 | C-FS-02「刪除的原始檔保留 30 天後才清除」與 FR-017「刪除照片時一併刪除原始檔與縮圖」衝突，無法在不違反 FR-017 的前提下化解 | PM 決定以 clarify-over-specs 修改 FR-017，或由使用者以 constitution 修訂 C-FS-02 |

## 憲法衝突

| 端點 | 輸入文件與位置 | 衝突內容 | 條款 | 產出物處理 | 後續處理 |
|---|---|---|---|---|---|
| 後端 | plan.md「分析 Wave」Wave 2 分析重點 | 匯入失敗時只回傳 HTTP 狀態碼 | C-API-02 | 各錯誤回應加上 `code` 與 `message` | system-analysis 已修正 Wave 2 分析重點 |
| 資料庫端 | research.md R-03 | 主鍵使用自動遞增整數 | C-DATA-02 | albums、photos 主鍵改為 UUID | 已記成技術項（修正：technical-research），由 technical-research 改寫本 plan 的 R-03 |
