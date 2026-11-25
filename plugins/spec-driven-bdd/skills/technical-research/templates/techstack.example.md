# 技術堆疊

本文件列出系統目前採用的全部技術與專案自行實作的模組。各技術的選用理由見研究紀錄，編號寫成 `<plan>/R-xx`，對應 `specs/plans/<plan>-*/research.md`（例如 `002/R-08` 是編號 002 的 plan 的 research.md 中的 R-08）。API 路徑、資料表、元件與檔案名稱、遷移版本不在本文件，以各端點的介面文檔與程式為準。

---

## 執行環境

| 項目 | 技術 | 版本 | 研究紀錄 |
|------|------|------|----------|
| 執行環境 | Node.js | 22 LTS | 001/R-01 |
| 程式語言 | JavaScript（ES Modules） | ES2022 | 001/R-01 |
| 資料庫 | MySQL | 8.0 以上 | 001/R-01 |
| 套件管理 | npm workspaces（`frontend`、`backend`、`e2e`） | 隨 Node 22 | 001/R-16 |

## 前端

| 項目 | 技術 | 類型 | 版本 | 研究紀錄 |
|------|------|------|------|----------|
| 建置工具 | `vite`（開發時以 proxy 把 API 請求轉發至後端） | 套件 | ^6.0.0 | 001/R-13 |
| 介面 | 原生 HTML、CSS、JavaScript | 內建 | — | 001/R-13 |
| 路由 | hash 路由 | 自行實作 | — | 001/R-13 |
| 縮圖產生 | `createImageBitmap` ＋ `OffscreenCanvas` | 內建 | — | 001/R-07 |
| 拖放排序 | Pointer Events | 自行實作 | — | 001/R-12 |
| 無限捲動 | `IntersectionObserver` | 內建 | — | 001/R-14 |
| 設計代幣 | CSS 自訂屬性 | 內建 | — | 001/R-16 |

## 後端

| 項目 | 技術 | 類型 | 版本 | 研究紀錄 |
|------|------|------|------|----------|
| HTTP 伺服器 | `node:http` ＋ 極簡路由器 | 自行實作 | — | 001/R-02 |
| 資料庫驅動 | `mysql2`（Promise API） | 套件 | ^3.11.0 | 001/R-03 |
| 上傳解析 | `busboy` | 套件 | ^1.6.0 | 001/R-03 |
| EXIF 讀取 | `exifr` | 套件 | ^7.1.3 | 001/R-03、001/R-06 |
| 內容雜湊 | `node:crypto`（SHA-256） | 內建 | — | 001/R-08 |
| 檔案格式判定 | 檔頭魔術位元組比對 | 自行實作 | — | 001/R-09 |
| 檔案儲存 | 本機檔案系統 | 內建 | — | 001/R-04 |
| 原子寫入與殘檔清理 | `node:fs`（暫存檔 ＋ `rename`）、啟動時清理 | 自行實作 | — | 001/R-17 |
| 存取範圍 | `node:http` 的監聽位址設定 | 內建 | — | 001/R-18 |
| 環境變數 | Node 的 `--env-file` | 內建 | — | 001/R-16 |
| 資料庫遷移 | 依檔名順序執行 SQL 遷移檔的自寫腳本 | 自行實作 | — | 001/R-16 |

## 測試

| 項目 | 技術 | 類型 | 版本 | 研究紀錄 |
|------|------|------|------|----------|
| 後端 BDD 的 HTTP 呼叫 | `fetch` | 內建 | — | 001/R-15 |
| 後端與前端 BDD | `@cucumber/cucumber` | 套件 | ^11.0.0 | 001/R-15 |
| 瀏覽器自動化 | `playwright` | 套件 | ^1.49.0 | 001/R-15 |
| 無障礙 | `@axe-core/playwright` | 套件 | ^4.10.0 | 001/R-15 |
| 效能 | `fetch` 量測腳本、`PerformanceObserver` | 自行實作 | — | 001/R-15 |

## 開發工具

| 項目 | 技術 | 類型 | 版本 | 研究紀錄 |
|------|------|------|------|----------|
| Lint | `eslint`（flat config） | 套件 | ^9.0.0 | 001/R-16 |
| 格式化 | `prettier` | 套件 | ^3.4.0 | 001/R-16 |

## 套件安裝清單

| Workspace | 相依類型 | 套件與版本 |
|-----------|----------|------------|
| `frontend` | dependencies | （無） |
| `frontend` | devDependencies | `vite@^6.0.0` |
| `backend` | dependencies | `mysql2@^3.11.0`、`busboy@^1.6.0`、`exifr@^7.1.3` |
| `backend` | devDependencies | （無） |
| `.` | devDependencies | `eslint@^9.0.0`、`prettier@^3.4.0` |
| `e2e` | devDependencies | `@cucumber/cucumber@^11.0.0`、`playwright@^1.49.0`、`@axe-core/playwright@^4.10.0` |
