# 實作計畫：照片相簿整理器

**Plan**：`001-photo-album-organizer` | **日期**：2026-10-22 | **規格**：[spec.md](./spec.md) | **研究紀錄**：[research.md](./research.md) | **技術堆疊**：[techstack.md](../../truth/techstack.md)

**輸入**：來自 `specs/plans/001-photo-album-organizer/spec.md` 的功能規格

## 專案結構

### 文件（這個 plan）

```text
specs/plans/001-photo-album-organizer/
├── spec.md              # 功能規格（由 /specify 產生）
├── research.md          # 技術決策與理由（由 /technical-research 產生）
├── truth-changes.md     # 這個 plan 對 truth 的異動紀錄（由修改 truth 的各個指令記錄）
├── plan.md              # 本文件
└── tasks.md             # 實作任務（由後續任務拆解產生，不由本指令建立）
```

### 原始碼（repo 根目錄）

```text
package.json                 # npm workspaces：frontend、backend、e2e；共用的 lint／dev 指令
eslint.config.js
.prettierrc

backend/
├── package.json
├── .env.example
├── src/
│   ├── server.js            # 進入點：建立 http server、提供 frontend/dist 靜態檔
│   ├── app.js               # 組合路由與錯誤處理
│   ├── config.js            # 讀取環境變數
│   ├── lib/
│   │   ├── router.js        # 極簡路由器
│   │   ├── http.js          # JSON 回應、錯誤回應（繁中訊息）
│   │   ├── sniff.js         # 檔頭判定 JPEG／PNG／HEIC
│   │   └── takenDate.js     # EXIF 日期解析與推估（R-06）
│   ├── db/
│   │   ├── pool.js
│   │   ├── migrate.js
│   │   └── migrations/001_init.sql
│   ├── repositories/
│   │   ├── albumRepository.js
│   │   ├── photoRepository.js
│   │   └── settingsRepository.js
│   ├── services/
│   │   ├── importService.js # 上傳、雜湊、去重、建立相簿
│   │   ├── albumService.js  # 列表、排序模式、移動位置
│   │   ├── photoService.js  # 查詢、前後張、刪除（含空相簿清除）
│   │   └── fileStore.js     # storage 目錄讀寫
│   └── routes/
│       ├── albums.js
│       └── photos.js
├── scripts/
│   ├── seed-large.js        # 10k 照片種子資料
│   └── perf.js              # API p95／p99 量測
├── storage/                 # 執行期產生（.gitignore）
└── tests/
    ├── unit/
    ├── integration/
    └── contract/

frontend/
├── package.json
├── vite.config.js           # /api proxy → :3000
├── index.html
├── src/
│   ├── main.js
│   ├── router.js            # hash 路由
│   ├── api/client.js        # fetch 包裝、錯誤轉換
│   ├── pages/
│   │   ├── homePage.js
│   │   └── albumPage.js
│   ├── components/
│   │   ├── albumCard.js
│   │   ├── photoGrid.js
│   │   ├── lightbox.js
│   │   ├── importPanel.js
│   │   ├── confirmDialog.js
│   │   └── toast.js
│   ├── lib/
│   │   ├── formatAlbumDate.js   # 「2026年10月1日（星期四）」
│   │   ├── sortable.js          # Pointer Events 拖放 ＋ 鍵盤狀態機
│   │   ├── thumbnail.js         # Canvas 縮圖
│   │   ├── uploadQueue.js       # 並行數 3 的上傳佇列
│   │   └── infiniteScroll.js
│   └── styles/
│       ├── tokens.css
│       ├── base.css
│       └── components.css
└── tests/unit/

e2e/
├── package.json
├── cucumber.mjs
├── features/                # # language: zh-TW
│   ├── 匯入與分組.feature
│   ├── 平鋪預覽.feature
│   └── 相簿排序.feature
├── steps/
├── support/                 # Playwright world、axe、DB 重設
└── fixtures/photos/
```

**結構決策**：採用前端 ＋ 後端兩個專案的 Web 應用程式結構，並以 npm workspaces 管理，另加 `e2e` 驗收測試專案。
後端分為路由 → 服務 → 儲存庫三層，讓核心商業邏輯（服務層）可以獨立測試，並達到 90% 覆蓋率要求。

## 分析流程規劃

### 介面盤點

| 介面 ID | 介面 | 所屬端點 | 異動 | 依據需求 |
|---|---|---|---|---|
| UI-01 | 主頁相簿列表介面（相簿卡片、空狀態、拖放與鍵盤排序） | 前端 | ADD | FR-007、FR-013、FR-014、FR-016、FR-019、FR-020、NFR-004、NFR-011、NFR-020 |
| UI-02 | 匯入對話框介面（選取檔案、進度、略過結果） | 前端 | ADD | FR-001、FR-008、FR-009、FR-020、NFR-001、NFR-015 |
| UI-03 | 相簿平鋪預覽介面（縮圖格線、佔位載入、刪除） | 前端 | ADD | FR-006、FR-010、FR-017、FR-018、FR-020、NFR-006、NFR-008、NFR-009 |
| UI-04 | 燈箱放大檢視介面（上一張／下一張、返回平鋪、刪除） | 前端 | ADD | FR-011、FR-012、FR-017、NFR-007 |
| API-01 | 匯入 API | 後端 | ADD | FR-001～FR-004、FR-008、FR-009、NFR-002、NFR-003、NFR-005 |
| API-02 | 相簿 API（列表、排序） | 後端 | ADD | FR-006、FR-007、FR-013、FR-015、FR-016、NFR-010 |
| API-03 | 照片 API（相簿內列表、前後張、刪除、原圖與縮圖取得） | 後端 | ADD | FR-010、FR-011、FR-017、FR-018、NFR-012 |
| DB-01 | 相簿資料表（含自訂排序） | 資料庫端 | ADD | FR-003、FR-007、FR-015、FR-016、FR-018、FR-019、NFR-016 |
| DB-02 | 照片資料表（拍攝日期、推估標記、內容雜湊） | 資料庫端 | ADD | FR-002、FR-004、FR-005、FR-008、NFR-016 |
| FS-01 | 原始檔儲存區 | 檔案系統端 | ADD | FR-017、NFR-002、NFR-005、NFR-012 |
| FS-02 | 縮圖儲存區 | 檔案系統端 | ADD | FR-010、NFR-012 |

### 分析 Wave

**共用輸入**（每個 Wave 的 sub-agent 皆須讀取）：`spec.md`、`specs/truth/techstack.md`

**Wave 1 — 前端（UI-01～UI-04）**

- 分析重點：每個畫面的操作、狀態（成功、錯誤、載入、空狀態）與繁中文案，以及每個操作需要後端提供哪些資料與動作。
- 相依：無
- 委派：開 1 個 sub-agent，分別分析前端。

**Wave 2 — 後端（API-01～API-03）**

- 分析重點：滿足 Wave 1 各畫面需要的端點、請求與回應格式、分頁與錯誤回應，以及每個端點需要讀寫哪些資料與檔案。
- 相依：Wave 1 前端的產出
- 委派：開 1 個 sub-agent，分別分析後端。

**Wave 3 — 資料庫端（DB-01～DB-02）、檔案系統端（FS-01～FS-02）**

- 分析重點：資料庫端分析滿足 Wave 2 API 讀寫的欄位、索引與交易邊界；檔案系統端分析原始檔與縮圖的目錄結構、命名規則與刪除連動。
- 相依：Wave 2 後端的產出
- 委派：開 2 個 sub-agent，分別分析資料庫端、檔案系統端。

共盤點 4 個端點、11 個介面、3 個 Wave，介面之間沒有循環依賴。