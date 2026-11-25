---

description: "照片相簿整理器的實作任務清單"
---

# 任務：照片相簿整理器

[紅燈]／[綠燈]／[重構]／[重跑]／[驗證] 由 implement 交給 `/bdd red|green|refactor|rerun|verify`，沒有標記的任務由 implement 直接實作；Phase 依編號、Phase 內依列出順序執行；Phase 標頭的 NFR 約束、預計修改與必讀適用於該 Phase 的每個任務

## Phase 1：Setup

- [ ] T001 建立根目錄 `package.json`（npm workspaces：`frontend`、`backend`、`e2e`；devDependencies `eslint@^9.0.0`、`prettier@^3.4.0`；scripts `dev`、`lint`、`format`）、`eslint.config.js` 與 `.prettierrc`
  - 📎 必讀：`techstack.md › 套件安裝清單 › 根目錄` — 根目錄的 devDependencies 與版本以此為準，不得增列清單以外的套件
- [ ] T002 建立 `backend/package.json`（dependencies `mysql2@^3.11.0`、`busboy@^1.6.0`、`exifr@^7.1.3`；scripts `start`、`test`）
  - 📎 必讀：`techstack.md › 套件安裝清單 › backend` — backend 的 dependencies 與版本以此為準，不得增列清單以外的套件
- [ ] T003 建立 `frontend/package.json`（devDependencies `vite@^6.0.0`、`vitest@^3.0.0`、`jsdom@^25.0.0`；scripts `dev`、`build`、`test`）與 `frontend/vite.config.js`（`/api` proxy 到 `:3000`）
  - 📎 必讀：`techstack.md › 套件安裝清單 › frontend` — frontend 的 devDependencies 與版本以此為準，不得增列清單以外的套件
- [ ] T004 建立 `e2e/package.json`（devDependencies `@cucumber/cucumber@^11.0.0`、`playwright@^1.49.0`、`@axe-core/playwright@^4.10.0`；scripts `test`）
  - 📎 必讀：`techstack.md › 套件安裝清單 › e2e` — e2e 的 devDependencies 與版本以此為準，不得增列清單以外的套件

## Phase 2：Foundational

- [ ] T005 實作 `backend/src/config.js`：讀取環境變數 `HOST`（預設 `127.0.0.1`）、`PORT`（預設 `3000`）、`DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`、`STORAGE_DIR`（預設 `backend/storage`），匯出凍結物件，並建立 `backend/.env.example`
  - NFR 約束：NFR-018
  - 📎 必讀：`research.md › R-16、R-18` — 環境變數載入方式與只監聽本機的決定以此為準
  - 📎 必讀：`spec.md › NFR-018` — 照片庫只能由使用者本人存取的要求以此為準
- [ ] T006 實作 `backend/src/db/pool.js` 與 `backend/src/db/migrate.js`：依檔名順序執行 `backend/src/db/migrations/*.sql` 並記錄已執行的版本，建立空的 `backend/src/db/migrations/001_init.sql`
  - 📎 必讀：`research.md › R-16` — 遷移機制的做法以此為準
- [ ] T007 實作 `backend/src/server.js`、`backend/src/app.js`、`backend/src/lib/router.js` 與 `backend/src/lib/http.js`：建立 http server、提供 `frontend/dist` 靜態檔，未知路由回 404 與繁中錯誤訊息的 JSON
  - NFR 約束：NFR-019
  - 📎 必讀：`research.md › R-02` — HTTP 伺服器與極簡路由器的做法以此為準
  - 📎 必讀：`spec.md › NFR-019` — 錯誤訊息須說明發生什麼事與如何處理的要求以此為準
- [ ] T008 實作 `frontend/src/main.js`、`frontend/src/router.js`（hash 路由）與 `frontend/src/styles/tokens.css`、`frontend/src/styles/base.css`：建立頁面掛載點與設計代幣
  - 📎 必讀：`research.md › R-13` — 前端架構與路由方式以此為準
  - 📎 必讀：`ui/ui-contract.md › 共用約定` — 設計代幣與共用版面以此為準
- [ ] T009 建立 `e2e/cucumber.mjs` 收集 `specs/truth/features/frontend/*.feature` 與 `e2e/steps/`，`backend/tests/` 的執行設定收集 `specs/truth/features/backend/`、`database/`、`filesystem/`，並在測試 support 中提供資料庫重設與暫存 `STORAGE_DIR`
  - 📎 必讀：`research.md › R-15` — 各端點的測試工具與執行方式以此為準

## Phase 3：database/匯入與分組.feature

**驗收 AC**：無

**預計修改**：`backend/src/db/migrations/001_init.sql`

**📎 必讀**：

- `plan.md › 原始碼（repo 根目錄）` — 遷移檔的位置以此為準

- [ ] T010 [紅燈] 範疇：`specs/truth/features/database/匯入與分組.feature`：撰寫 3 條 Rule、3 個 Example 的 step definitions 與資料表 Driver，確認因 `albums` 資料表尚未建立而失敗
- [ ] T011 [綠燈] 範疇：`specs/truth/features/database/匯入與分組.feature`：在 `001_init.sql` 建立 `albums`、`photos`、`uk_albums_album_date`、`uk_photos_content_hash` 與 `fk_photos_album_id`，讓 feature 通過
- [ ] T012 [重構] 範疇：`specs/truth/features/database/匯入與分組.feature`：整理 `001_init.sql` 與資料表 Driver，不改變行為

## Phase 4：filesystem/匯入與分組.feature

**驗收 AC**：無

**預計修改**：`backend/src/services/fileStore.js`

**📎 必讀**：

- `research.md › R-04、R-17` — 儲存位置、暫存檔與原子搬移的做法以此為準
- `plan.md › 原始碼（repo 根目錄）` — `fileStore.js` 的位置以此為準

- [ ] T013 [紅燈] 範疇：`specs/truth/features/filesystem/匯入與分組.feature`：撰寫 4 條 Rule、6 個 Example 的 step definitions 與儲存區 Driver，確認因 `fileStore.createUpload` 尚未存在而失敗
- [ ] T014 [綠燈] 範疇：`specs/truth/features/filesystem/匯入與分組.feature`：實作 `fileStore.createUpload`：寫入暫存區、計算 SHA-256、依格式搬到原始檔正式路徑並寫入縮圖，讓 feature 通過
- [ ] T015 [重構] 範疇：`specs/truth/features/filesystem/匯入與分組.feature`：整理 `fileStore.js` 的路徑組合與儲存區 Driver，不改變行為

## Phase 5：backend/匯入與分組.feature

**驗收 AC**：AC-01、AC-02

**NFR 約束**：NFR-015、NFR-017

**預計修改**：`backend/src/routes/photos.js`、`albums.js`，`backend/src/services/importService.js`、`albumService.js`，`backend/src/repositories/albumRepository.js`、`photoRepository.js`，`backend/src/lib/sniff.js`、`takenDate.js`

**📎 必讀**：

- `data/data-model.dbml › Project photo_album_organizer › 交易邊界 › 匯入一張照片` — 建立相簿與插入照片的交易範圍以此為準
- `data/相簿.dbml › Table albums、Table photos` — 欄位與唯一索引以此為準
- `storage/storage-contract.md › FS-01 原始檔儲存區、FS-02 縮圖儲存區` — 呼叫 `fileStore` 的方式與失敗時的清理以此為準
- `research.md › R-06、R-08、R-09` — 拍攝日期推估、重複判定與格式判定的做法以此為準
- `spec.md › NFR-015、NFR-017` — NFR 約束的原文以此為準
- `plan.md › 原始碼（repo 根目錄）` — 路由、服務與儲存庫的位置以此為準

- [ ] T016 [紅燈] 範疇：`specs/truth/features/backend/匯入與分組.feature`：撰寫 9 條 Rule、14 個 Example 的 step definitions 與 Driver，確認因 `POST /api/photos` 回 404 而失敗
- [ ] T017 [綠燈] 範疇：`specs/truth/features/backend/匯入與分組.feature`：新增匯入與相簿列表路由，實作格式判定、拍攝日期推估、重複略過與依日期建立相簿的匯入服務，讓 feature 通過
- [ ] T018 [重構] 範疇：`specs/truth/features/backend/匯入與分組.feature`：整理匯入服務、儲存庫與 step，不改變行為

## Phase 6：frontend/匯入與分組.feature

**驗收 AC**：AC-01、AC-02

**NFR 約束**：NFR-001、NFR-014、NFR-019、NFR-021

**預計修改**：`frontend/src/pages/homePage.js`，`frontend/src/components/importPanel.js`、`albumCard.js`、`toast.js`，`frontend/src/lib/uploadQueue.js`、`thumbnail.js`、`formatAlbumDate.js`，`frontend/src/api/client.js`

**📎 必讀**：

- `contracts/paths/照片/api_photos.yaml › importPhoto` — 畫面匯入照片呼叫的 API、回應與錯誤代碼以此為準
- `contracts/paths/相簿/api_albums.yaml › listAlbums` — 畫面列出相簿呼叫的 API 與回應以此為準
- `research.md › R-07、R-10` — 前端產生縮圖與並行上傳的做法以此為準
- `spec.md › NFR-001、NFR-014、NFR-019、NFR-021` — NFR 約束的原文以此為準
- `plan.md › 原始碼（repo 根目錄）` — 頁面、元件與 lib 的位置以此為準

- [ ] T019 [紅燈] 範疇：`specs/truth/features/frontend/匯入與分組.feature`：撰寫 10 條 Rule、15 個 Example 的 step definitions 與頁面 Driver，確認因主頁沒有匯入按鈕而失敗
- [ ] T020 [綠燈] 範疇：`specs/truth/features/frontend/匯入與分組.feature`：實作主頁相簿列表、空狀態、匯入對話框與進度、略過結果與相簿卡片，讓 feature 通過
- [ ] T021 [重構] 範疇：`specs/truth/features/frontend/匯入與分組.feature`：整理匯入對話框、上傳佇列與 step，不改變行為

## Phase 7：backend/平鋪預覽.feature

**驗收 AC**：AC-03、AC-04

**NFR 約束**：NFR-013

**預計修改**：`backend/src/routes/photos.js`，`backend/src/services/photoService.js`，`backend/src/repositories/photoRepository.js`

**📎 必讀**：

- `data/相簿.dbml › Table photos › ix_photos_album_taken` — 相簿內游標分頁的排序與索引以此為準
- `storage/storage-contract.md › FS-01 原始檔儲存區、FS-02 縮圖儲存區` — 讀取原始檔與縮圖的路徑以此為準
- `spec.md › NFR-013` — NFR 約束的原文以此為準
- `plan.md › 原始碼（repo 根目錄）` — 路由、服務與儲存庫的位置以此為準

- [ ] T022 [紅燈] 範疇：`specs/truth/features/backend/平鋪預覽.feature`：撰寫 5 條 Rule、8 個 Example 的 step definitions，確認因 `GET /api/albums/{albumId}/photos` 回 404 而失敗
- [ ] T023 [綠燈] 範疇：`specs/truth/features/backend/平鋪預覽.feature`：新增相簿內照片列表、原始檔與縮圖取得的路由與照片服務，讓 feature 通過
- [ ] T024 [重構] 範疇：`specs/truth/features/backend/平鋪預覽.feature`：整理照片服務的分頁查詢與 step，不改變行為

## Phase 8：frontend/平鋪預覽.feature

**驗收 AC**：AC-03、AC-04

**NFR 約束**：NFR-014、NFR-021

**預計修改**：`frontend/src/pages/albumPage.js`，`frontend/src/components/photoGrid.js`、`lightbox.js`，`frontend/src/lib/infiniteScroll.js`

**📎 必讀**：

- `contracts/paths/相簿/api_albums_{albumId}_photos.yaml › listAlbumPhotos` — 畫面列出相簿內照片呼叫的 API 與分頁參數以此為準
- `contracts/paths/照片/api_photos_{photoId}_thumbnail.yaml › getPhotoThumbnail` — 畫面取得縮圖呼叫的 API 以此為準
- `contracts/paths/照片/api_photos_{photoId}_original.yaml › getOriginalPhoto` — 畫面取得原始檔呼叫的 API 以此為準
- `spec.md › NFR-014、NFR-021` — NFR 約束的原文以此為準
- `plan.md › 原始碼（repo 根目錄）` — 頁面、元件與 lib 的位置以此為準

- [ ] T025 [紅燈] 範疇：`specs/truth/features/frontend/平鋪預覽.feature`：撰寫 7 條 Rule、11 個 Example 的 step definitions 與頁面 Driver，確認因相簿頁沒有縮圖格線而失敗
- [ ] T026 [綠燈] 範疇：`specs/truth/features/frontend/平鋪預覽.feature`：實作相簿頁縮圖格線、佔位載入、無法預覽提示與燈箱的上一張、下一張、返回，讓 feature 通過
- [ ] T027 [重構] 範疇：`specs/truth/features/frontend/平鋪預覽.feature`：整理縮圖格線、燈箱與 step，不改變行為

## Phase 9：database/相簿排序.feature

**驗收 AC**：無

**預計修改**：`backend/src/db/migrations/001_init.sql`

**📎 必讀**：

- `plan.md › 原始碼（repo 根目錄）` — 遷移檔的位置以此為準

- [ ] T028 [紅燈] 範疇：`specs/truth/features/database/相簿排序.feature`：撰寫 1 條 Rule、1 個 Example 的 step definitions，確認因 `app_settings` 資料表尚未建立而失敗
- [ ] T029 [綠燈] 範疇：`specs/truth/features/database/相簿排序.feature`：在 `001_init.sql` 建立 `app_settings`、預設列 `album_order_mode = date` 與 `ix_albums_position`，讓 feature 通過
- [ ] T030 [重構] 範疇：`specs/truth/features/database/相簿排序.feature`：整理 `001_init.sql` 與資料表 Driver，不改變行為

## Phase 10：backend/相簿排序.feature

**驗收 AC**：AC-05、AC-06、AC-07

**NFR 約束**：NFR-013

**預計修改**：`backend/src/routes/albums.js`，`backend/src/services/albumService.js`，`backend/src/repositories/albumRepository.js`、`settingsRepository.js`

**📎 必讀**：

- `data/data-model.dbml › Project photo_album_organizer › 交易邊界 › 第一次自訂排序、移動相簿` — 排序寫入的交易範圍以此為準
- `data/相簿.dbml › Table albums、Table app_settings` — 位置欄位與排序模式以此為準
- `research.md › R-11` — 相簿排序模型以此為準
- `spec.md › NFR-013` — NFR 約束的原文以此為準
- `plan.md › 原始碼（repo 根目錄）` — 路由、服務與儲存庫的位置以此為準

- [ ] T031 [紅燈] 範疇：`specs/truth/features/backend/相簿排序.feature`：撰寫 6 條 Rule、9 個 Example 的 step definitions，確認因移動相簿的 `moveAlbum` 端點回 404 而失敗
- [ ] T032 [綠燈] 範疇：`specs/truth/features/backend/相簿排序.feature`：新增移動相簿路由，實作第一次自訂排序、位置位移與新相簿置前的相簿服務，讓 feature 通過
- [ ] T033 [重構] 範疇：`specs/truth/features/backend/相簿排序.feature`：整理相簿服務的位置計算與 step，不改變行為

## Phase 11：frontend/相簿排序.feature

**驗收 AC**：AC-05、AC-06、AC-07

**NFR 約束**：NFR-014、NFR-021、NFR-022

**預計修改**：`frontend/src/pages/homePage.js`，`frontend/src/components/albumCard.js`，`frontend/src/lib/sortable.js`

**📎 必讀**：

- `contracts/paths/相簿/api_albums_{albumId}_position.yaml › moveAlbum` — 畫面移動相簿呼叫的 API 與失敗時的回應以此為準
- `contracts/paths/相簿/api_albums.yaml › listAlbums` — 畫面重新列出相簿呼叫的 API 以此為準
- `research.md › R-12` — 拖放與鍵盤操作的做法以此為準
- `spec.md › NFR-014、NFR-021、NFR-022` — NFR 約束的原文以此為準
- `plan.md › 原始碼（repo 根目錄）` — 頁面、元件與 lib 的位置以此為準

- [ ] T034 [紅燈] 範疇：`specs/truth/features/frontend/相簿排序.feature`：撰寫 8 條 Rule、12 個 Example 的 step definitions 與頁面 Driver，確認因相簿卡片不能拖放而失敗
- [ ] T035 [綠燈] 範疇：`specs/truth/features/frontend/相簿排序.feature`：實作相簿卡片的拖放、取消還原、鍵盤排序與螢幕閱讀器告知，讓 feature 通過
- [ ] T036 [重構] 範疇：`specs/truth/features/frontend/相簿排序.feature`：整理 `sortable.js` 的拖放與鍵盤狀態機與 step，不改變行為

## Phase 12：filesystem/刪除照片.feature

**驗收 AC**：無

**預計修改**：`backend/src/services/fileStore.js`

**📎 必讀**：

- `research.md › R-04` — 儲存位置與檔案命名以此為準
- `plan.md › 原始碼（repo 根目錄）` — `fileStore.js` 的位置以此為準

- [ ] T037 [紅燈] 範疇：`specs/truth/features/filesystem/刪除照片.feature`：撰寫 2 條 Rule、3 個 Example 的 step definitions，確認因 `fileStore.removeFiles` 尚未存在而失敗
- [ ] T038 [綠燈] 範疇：`specs/truth/features/filesystem/刪除照片.feature`：實作 `fileStore.removeFiles`，刪除照片的原始檔與縮圖且不影響其他照片的檔案，讓 feature 通過
- [ ] T039 [重構] 範疇：`specs/truth/features/filesystem/刪除照片.feature`：整理 `fileStore.js` 的刪除流程與儲存區 Driver，不改變行為

## Phase 13：backend/刪除照片.feature

**驗收 AC**：AC-08、AC-09

**預計修改**：`backend/src/routes/photos.js`，`backend/src/services/photoService.js`，`backend/src/repositories/photoRepository.js`、`albumRepository.js`

**📎 必讀**：

- `data/data-model.dbml › Project photo_album_organizer › 交易邊界 › 刪除照片` — 刪除照片與移除空相簿的交易範圍以此為準
- `storage/storage-contract.md › FS-01 原始檔儲存區、FS-02 縮圖儲存區` — 交易成功後刪除檔案的方式以此為準
- `plan.md › 原始碼（repo 根目錄）` — 路由、服務與儲存庫的位置以此為準

- [ ] T040 [紅燈] 範疇：`specs/truth/features/backend/刪除照片.feature`：撰寫 5 條 Rule、7 個 Example 的 step definitions，確認因 `DELETE /api/photos/{photoId}` 回 404 而失敗
- [ ] T041 [綠燈] 範疇：`specs/truth/features/backend/刪除照片.feature`：新增刪除照片路由，實作刪除照片、移除空相簿與交易成功後刪除檔案的照片服務，讓 feature 通過
- [ ] T042 [重構] 範疇：`specs/truth/features/backend/刪除照片.feature`：整理照片服務的刪除流程與 step，不改變行為

## Phase 14：frontend/刪除照片.feature

**驗收 AC**：AC-08、AC-09

**NFR 約束**：NFR-014、NFR-019、NFR-021

**預計修改**：`frontend/src/pages/albumPage.js`，`frontend/src/components/confirmDialog.js`、`photoGrid.js`、`lightbox.js`

**📎 必讀**：

- `contracts/paths/照片/api_photos_{photoId}.yaml › deletePhoto` — 畫面呼叫的 API 與錯誤代碼以此為準
- `spec.md › NFR-014、NFR-019、NFR-021` — NFR 約束的原文以此為準
- `plan.md › 原始碼（repo 根目錄）` — 頁面與元件的位置以此為準

- [ ] T043 [紅燈] 範疇：`specs/truth/features/frontend/刪除照片.feature`：撰寫 5 條 Rule、8 個 Example 的 step definitions 與頁面 Driver，確認因平鋪檢視沒有刪除按鈕而失敗
- [ ] T044 [綠燈] 範疇：`specs/truth/features/frontend/刪除照片.feature`：實作平鋪檢視與燈箱的刪除、確認對話框與刪除最後一張後回到主頁，讓 feature 通過
- [ ] T045 [重構] 範疇：`specs/truth/features/frontend/刪除照片.feature`：整理刪除流程、確認對話框與 step，不改變行為

## Phase 15：移除

這個 plan 沒有要移除的內容。

## Phase 16：技術項

這個 plan 沒有技術項。

## Phase 17：NFR 重構

**不另列任務**：

- NFR-001：並行數 3 的上傳佇列已是 Phase 6 的 NFR 約束，只涉及匯入流程
- NFR-014、NFR-022：已是各前端 Phase 的 NFR 約束，每個畫面在各自的綠燈中完成
- NFR-017、NFR-018：後端只監聽 `127.0.0.1` 且沒有任何外部呼叫，T005 與 Phase 5 已依約束實作
- NFR-023：驗收情境已由各 feature 自動化驗證，效能目標由 T046 的量測腳本驗證

- [ ] T046 建立 `backend/scripts/seed-large.js` 與 `backend/scripts/perf.js`，以 10,000 張照片量測相簿列表與開啟相簿的 p95，對照 SC-003 的門檻
  - 📎 必讀：`spec.md › NFR-013、NFR-015` — 回應時間與照片庫容量的要求以此為準
  - 📎 必讀：`research.md › R-14` — 效能策略與量測方式以此為準
- [ ] T047 [重構] 範疇：`specs/truth/features/backend/`：NFR-013：把 `backend/src/services/albumService.js` 的相簿列表改為一次取回照片數與封面的彙總查詢，消除每本相簿各查一次的 N+1
  - 📎 必讀：`spec.md › NFR-013` — 相簿列表回應時間的要求以此為準
  - 📎 必讀：`research.md › R-14` — 彙總查詢的效能策略以此為準
- [ ] T048 [重構] 範疇：`specs/truth/features/frontend/`：NFR-006：把縮圖格線與相簿卡片的佔位框統一為固定長寬比，集中到 `frontend/src/styles/components.css`，讓縮圖陸續載入時版面不跳動；NFR-019、NFR-020：把各頁的錯誤、空狀態與載入訊息集中到共用的狀態呈現與 `frontend/src/components/toast.js`，移除頁面中各自拼接的訊息；NFR-021：把焦點指示與文字對比集中到 `frontend/src/styles/tokens.css` 的代幣，移除元件中各自定義的焦點樣式
  - 📎 必讀：`spec.md › NFR-006` — 載入過程不得跳動的要求以此為準
  - 📎 必讀：`research.md › R-14` — 佔位與載入策略以此為準
  - 📎 必讀：`spec.md › NFR-019、NFR-020` — 訊息一致與四種狀態呈現的要求以此為準
  - 📎 必讀：`ui/ui-contract.md › 共用約定` — 共用文案與狀態呈現以此為準
  - 📎 必讀：`spec.md › NFR-021` — WCAG 2.1 AA 的要求以此為準

## Phase 18：Polish

- [ ] T049 在根目錄執行 `npm run lint` 與 `npm run format`，修正全專案問題
- [ ] T050 在 `frontend/` 執行 `npm run build`，修正建置錯誤並確認 `frontend/dist` 可由後端提供

## Phase 19：Verify

- [ ] T051 [驗證] 執行所有端點的完整測試並與上次結果比對
