# 規格分析報告：照片相簿整理器

**Plan**：`001-photo-album-organizer` | **日期**：2026-11-14 | **產生方式**：`/analyze`

**結論**：可以進入 `/implement`。共 0 個 CRITICAL、1 個 HIGH，建議先處理 U1。

## 分析範圍

| 產物 | 產出 skill | 涵蓋介面 | 狀態 |
|------|-----------|---------|------|
| `spec.md` | specify、clarify-over-specs | — | ⚠️ C1、A1、I4、I5、D1、U2 |
| `features/acceptance/` | spec-by-example | — | ✅ |
| `research.md` | technical-research | — | ⚠️ I6 |
| `specs/truth/techstack.md` | technical-research | — | ✅ |
| `plan.md` | system-analysis | — | ⚠️ I1、I2、I3 |
| `ui/ui-contract.md` | ui-ux-plan | UI-01～UI-04 | ⚠️ I3 |
| `ui/prototype/` | ui-ux-plan | UI-01～UI-04 | ✅ |
| `specs/truth/contracts/`（truth-changes.md 的 api-plan 一節列出的檔案） | api-plan | API-01～API-03 | ⚠️ C2、C3、I2 |
| `specs/truth/data/`（data-plan 一節列出的檔案） | data-plan | DB-01、DB-02 | ⚠️ I4 |
| `specs/truth/storage/`（storage-plan 一節列出的檔案） | storage-plan | FS-01、FS-02 | ✅ |
| `features/涵蓋表.md` | dsl-refine | — | ✅ |
| `specs/truth/features/用語表.md` | dsl-refine | — | ✅ |
| `specs/truth/features/database/` | dsl-refine | DB-01、DB-02 | ✅ |
| `specs/truth/features/filesystem/` | dsl-refine | FS-01、FS-02 | ✅ |
| `specs/truth/features/backend/` | dsl-refine | API-01～API-03 | ✅ |
| `specs/truth/features/frontend/` | dsl-refine | UI-01～UI-04 | ✅ |
| `truth-changes.md` | technical-research、api-plan、data-plan、storage-plan、dsl-refine | — | ✅ |
| `tasks.md` | task | — | ⚠️ U1、C1、I1 |

## 前置檢查

| 檢查項目 | 結果 | 說明 |
|---------|------|------|
| plan 狀態（plan-package） | ✅ | 進行中 |
| 待補跑（plan-package） | ✅ | 無 |
| 交叉檢查（plan-package） | ✅ | 通過：dsl.md 識別碼、AC 測試、tasks.md 範疇、技術項、techstack 與 research |
| 必要產物 | ✅ | spec.md、research.md、plan.md、tasks.md、truth-changes.md、features/acceptance/、features/涵蓋表.md 與 specs/truth/ 的 techstack.md、features/用語表.md 都存在 |
| 端點資料夾 | ✅ | truth 用語表登記的 frontend、backend、database、filesystem 都含 dsl.md 與 feature；這次有異動介面的端點在涵蓋表都有案例 |
| 介面文檔 | ✅ | UI 的 ui/ 存在；api-plan、data-plan、storage-plan 在 truth-changes.md 都有紀錄，列出的檔案都存在 |
| plan.md 結構檢查（check_plan.py） | ✅ | 0 個問題 |
| tasks.md 結構檢查（check_tasks.py） | ✅ | 51 個任務，0 個問題 |
| 憲法 | — | 專案沒有 `.claude/constitution/CONSTITUTION.md`，沿用各 skill 的內建規範，不偵測憲法違反 |

## 與前次分析比較

| 變化 | 數量 | ID |
|------|------|----|
| 已解決 | 2 | I7、A2 |
| 仍存在 | 12 | U1、C1、C2、I1、A1、I2、I3、I4、I5、I6、D1、U2 |
| 新增 | 1 | C3 |

**已解決的問題**：

- **I7**（MEDIUM）：Phase 13 的驗收 AC 原本只寫 AC-08，涵蓋表的 AC 涵蓋表中 backend/刪除照片.feature 另有 AC-09，已以 `/task` 重新產出補上。
- **A2**（LOW）：NFR-009 的「明確提示」已改寫為顯示「無法預覽此格式」文字與檔名。

## 發現事項

| ID | 類別 | 嚴重度 | 位置 | 摘要 | 建議 |
|----|------|--------|------|------|------|
| U1 | 規格不足 | HIGH | tasks.md:L23（T005）、L29（T007） | `STORAGE_DIR` 預設值 `backend/storage` 與靜態檔路徑 `frontend/dist` 都是相對路徑。`backend/package.json` 的 `start` script 在 workspace 中以 `backend/` 為工作目錄執行，會解析成 `backend/backend/storage` | 在 T005、T007 規定相對路徑以 repo 根目錄（或 `import.meta.url`）為基準解析 |
| C1 | 覆蓋缺口 | MEDIUM | spec.md:L192（NFR-013）vs tasks.md:L73（Phase 5 NFR 約束） | NFR-013 要求匯入、開啟相簿、拖放排序都符合回應時間。Phase 7、Phase 10 的標頭有 NFR-013，T046 量測相簿列表 p95；但匯入的 Phase 5 標頭只有 NFR-015、NFR-017，匯入回應時間（SC-001）沒有落點 | 用 `/task` 更新 tasks.md，在 Phase 5 的 NFR 約束補上 NFR-013 |
| C2 | 覆蓋缺口 | MEDIUM | specs/truth/contracts/paths/相簿/api_albums_{albumId}.yaml:L2（getAlbum） | `GET /api/albums/{albumId}` 沒有被 specs/truth/features/backend/dsl.md 或任何 feature 操作，也沒有任何必讀指向，綠燈不會實作它 | 畫面需要單本查詢時，用 `/dsl-refine` 補上對應案例後重新執行 `/task`；不需要時用 `/api-plan` 移除這個路徑檔 |
| C3 | 覆蓋缺口 | MEDIUM | specs/truth/contracts/paths/照片/api_photos.yaml:L41（importPhoto 的 415） | 契約定義匯入不支援的檔案格式時回 415 `unsupported_format`，backend 沒有任何 Rule 驗證這個回應，綠燈不會實作格式檢查的錯誤回應，前端依錯誤碼顯示的提示也從未被驗證 | 需要拒絕不支援的格式時，用 `/dsl-refine` 補上補充案例後重新執行 `/task`；不需要時用 `/api-plan` 移除這個回應 |
| I1 | 不一致 | MEDIUM | plan.md:L11-18（原始碼結構）vs tasks.md:L73（Phase 5 預計修改） | Phase 5 的預計修改列了 `backend/src/lib/sniff.js`，plan 的原始碼結構沒有這個檔案，實作時不知道它該放在哪一層 | 在 plan.md 的原始碼結構補上 sniff.js，或修正 Phase 5 的預計修改 |
| A1 | 模糊 | MEDIUM | spec.md:L243（SC-003「無明顯卡頓」）、L244（SC-004「感受不到延遲」）、L98（NFR-006「明顯跳動」） | 使用主觀形容詞。量化值（p95 200ms、CLS ≤ 0.1）只寫在 research.md R-14，spec 本身沒有 | 把 R-14 的量化門檻寫回 spec 的 SC／NFR |
| I2 | 不一致 | LOW | plan.md:L120（API-02「列表、排序」）vs specs/truth/contracts/paths/相簿/api_albums_{albumId}.yaml:L2（getAlbum） | 契約在 API-02 下多了單本查詢 `GET /api/albums/{albumId}`，plan 介面盤點的 API-02 描述沒有提到 | 與 C2 一併決定：保留時把 API-02 描述改為「列表、單本、排序」 |
| I3 | 不一致 | LOW | plan.md:L115（UI-01 依據需求）vs ui/ui-contract.md › UI-01 › 文案與無障礙 | ui-contract 的 UI-01 卡片顯示相簿名稱（`formatAlbumDate`），但 plan 介面盤點的 UI-01 依據需求沒有列 FR-006 | 在 plan 介面盤點的 UI-01 補上 FR-006 |
| I4 | 不一致 | LOW | spec.md:L231-232（關鍵實體「照片」）vs specs/truth/data/相簿.dbml:L31（Table photos） | 照片屬性列了「在相簿內的排序位置」，但 FR-010 與假設都規定固定依拍攝時間排序，photos 資料表也沒有這個欄位 | 從關鍵實體移除這個屬性，或改寫成「依拍攝時間排序」 |
| I5 | 不一致 | LOW | spec.md:L233（相簿定義）vs spec.md FR-003 | 相簿定義寫「同一日期區間」，FR-003 是「以天為單位」 | 改為「同一拍攝日期」 |
| I6 | 不一致 | LOW | research.md:L95、L154、L166、L195 | research.md 引用「憲法原則 II／III／IV」，但 repo 裡沒有任何 constitution 檔案 | 移除 research.md 的憲法引用，或改寫成引用的實際依據 |
| D1 | 重複 | LOW | FR-018 / 邊界情況 L174 / US4 情境 3；FR-016 / 邊界情況 L177 / 假設 L263；NFR-012 與 FR-017 | 同一條規則在多處重述（內容一致，不影響執行） | 可保留，或只留在 FR，其他地方改用引用 |
| U2 | 規格不足 | LOW | spec.md:L7 | 已經產出 tasks，spec 狀態仍是「草稿」 | 更新狀態 |

## 需求覆蓋

| 需求 | plan 介面 | 任務 | 狀態 | 備註 |
|------|----------|------|------|------|
| FR-001 | UI-02、API-01 | T017、T020 | ✅ | |
| FR-002 | UI-03、API-01、DB-02 | T017 | ✅ | |
| FR-003 | API-01、DB-01 | T011、T017 | ✅ | |
| FR-004 | API-01、DB-02 | T011、T017 | ✅ | |
| FR-005 | DB-02 | T011 | ✅ | 設計上不提供移動照片的 API |
| FR-006 | UI-03、API-02 | T017、T020 | ✅ | 見 I3 |
| FR-007 | UI-01、API-02、DB-01 | T017、T020、T032 | ✅ | |
| FR-008 | UI-02、API-01、DB-02 | T011、T017、T020 | ✅ | |
| FR-009 | UI-02、API-01 | T014、T017、T020 | ✅ | |
| FR-010 | UI-03、API-03、FS-02 | T023、T026 | ✅ | |
| FR-011 | UI-04、API-03 | T023、T026 | ✅ | |
| FR-012 | UI-04 | T026 | ✅ | |
| FR-013 | UI-01、API-02 | T032、T035 | ✅ | |
| FR-014 | UI-01 | T035 | ✅ | |
| FR-015 | API-02、DB-01 | T029、T032 | ✅ | |
| FR-016 | UI-01、API-02、DB-01 | T032、T035 | ✅ | |
| FR-017 | UI-03、UI-04、API-03、FS-01 | T038、T041、T044 | ✅ | |
| FR-018 | UI-03、API-03、DB-01 | T041、T044 | ✅ | |
| FR-019 | UI-01、DB-01 | T020 | ✅ | |
| FR-020 | UI-01～UI-04 | T008、T020、T026、T035、T044 | ✅ | |
| NFR-001 | UI-02 | T020 | ✅ | Phase 6 的 NFR 約束 |
| NFR-002 | API-01、FS-01 | T014、T017 | ✅ | |
| NFR-003 | API-01 | T020 | ✅ | |
| NFR-004 | UI-01 | T020 | ✅ | |
| NFR-005 | API-01、FS-01 | T014 | ✅ | |
| NFR-006 | UI-03 | T026、T047 | ✅ | 見 A1 |
| NFR-007 | UI-04 | T026 | ✅ | |
| NFR-008 | UI-03 | T026 | ✅ | |
| NFR-009 | UI-03 | T026 | ✅ | |
| NFR-010 | API-02 | T032 | ✅ | |
| NFR-011 | UI-01 | T035 | ✅ | |
| NFR-012 | API-03、FS-01、FS-02 | T038、T041 | ✅ | |
| NFR-013 | — | T023、T032、T046 | ⚠️ 部分 | 匯入的回應時間沒有落點（C1） |
| NFR-014 | — | T020、T026、T035、T044 | ✅ | 各前端 Phase 的 NFR 約束 |
| NFR-015 | UI-02 | T017、T046 | ✅ | Phase 5 的 NFR 約束，T046 以 10,000 張照片量測 |
| NFR-016 | DB-01、DB-02 | T011、T029 | ✅ | |
| NFR-017 | — | T017 | ✅ | 跨領域需求，Phase 5 的 NFR 約束 |
| NFR-018 | — | T005 | ✅ | 跨領域需求，T005 的 NFR 約束；見 U1 |
| NFR-019 | — | T007、T020、T044、T048 | ✅ | 跨領域需求 |
| NFR-020 | UI-01 | T048 | ✅ | |
| NFR-021 | — | T020、T026、T035、T044、T049 | ✅ | 跨領域需求 |
| NFR-022 | — | T035 | ✅ | 跨領域需求，Phase 11 的 NFR 約束 |
| NFR-023 | — | T046、T051 | ✅ | 驗收情境由各 feature 與 Verify 驗證，效能由 T046 量測 |
| SC-001 | — | T017 | ⚠️ 部分 | 匯入速度沒有 NFR 約束與量測（C1） |
| SC-002 | API-01 | T017 | ✅ | |
| SC-003 | — | T023、T046 | ✅ | 見 A1 |
| SC-004 | — | T032、T046 | ✅ | 見 A1 |
| SC-006 | UI-01～UI-04 | T035、T049 | ✅ | frontend/相簿排序.feature 的鍵盤排序與螢幕閱讀器告知 Rule 驗證無障礙 |
| SC-007 | — | T046 | ✅ | |
| SC-008 | API-01、FS-01 | T014、T017 | ✅ | |
| SC-009 | — | T005 | ✅ | |

**不列入覆蓋的成功標準**：SC-005 是易用性成果指標，上線後才能量測，不需要建置工作。

## 受影響的既有功能

spec.md 沒有受影響的既有功能。

## 介面文檔覆蓋

| 介面 | 異動 | 介面文檔 | 負責任務 | 狀態 | 備註 |
|------|------|---------|---------|------|------|
| UI-01 | ADD | ui/ui-contract.md › UI-01、ui/prototype/index.html | T019～T021、T034～T036、T047～T049 | ✅ | |
| UI-02 | ADD | ui/ui-contract.md › UI-02、ui/prototype/index.html › import-dialog | T019～T021 | ✅ | |
| UI-03 | ADD | ui/ui-contract.md › UI-03、ui/prototype/album.html | T025～T027、T043～T045、T047 | ✅ | |
| UI-04 | ADD | ui/ui-contract.md › UI-04 | T025～T027、T043～T045 | ✅ | |
| API-01 | ADD | specs/truth/contracts/ › importPhoto、getPhotoThumbnail | T016～T018、T022～T024 | ⚠️ 部分 | importPhoto 的 415 `unsupported_format` 沒有 Rule（C3） |
| API-02 | ADD | specs/truth/contracts/ › listAlbums、getAlbum、moveAlbum | T016～T018、T031～T033、T046 | ⚠️ 部分 | getAlbum 沒有 Rule 操作（C2） |
| API-03 | ADD | specs/truth/contracts/ › listAlbumPhotos、getPhoto、deletePhoto、getOriginalPhoto | T022～T024、T040～T042 | ✅ | |
| DB-01 | ADD | specs/truth/data/ › Table albums、Table app_settings | T010～T012、T028～T030 | ✅ | |
| DB-02 | ADD | specs/truth/data/ › Table photos、Ref fk_photos_album_id | T010～T012 | ✅ | |
| FS-01 | ADD | specs/truth/storage/ › FS-01 原始檔儲存區 | T013～T015、T037～T039，以及 Phase 5、7、13 標頭必讀的 T016～T018、T022～T024、T040～T042 | ✅ | |
| FS-02 | ADD | specs/truth/storage/ › FS-02 縮圖儲存區 | T013～T015，以及 Phase 5、7、13 標頭必讀的 T016～T018、T022～T024、T040～T042 | ✅ | |

## 反向覆蓋

**未對應需求的任務**：無。T001～T004、T006、T008、T009 是 Setup 與 Foundational 基礎建設，T049、T050 是 Polish 收尾，T051 是 Verify，屬於合理的支撐任務；這個 plan 沒有移除與技術項的任務。

**這次異動的介面文檔段落中，未被 feature 或必讀涵蓋的**：1 個。

- `specs/truth/contracts/paths/相簿/api_albums_{albumId}.yaml › getAlbum`（C2）

## 指標

| 指標 | 數值 |
|------|------|
| 需求總數 | 51（20 FR、23 NFR、8 個需要建置的 SC） |
| 任務總數 | 51 |
| 需求覆蓋率 | 100%（51/51，其中 2 項只部分涵蓋） |
| 介面文檔覆蓋率 | 82%（9/11 個介面完整涵蓋） |
| 發現事項 | 13（CRITICAL 0、HIGH 1、MEDIUM 5、LOW 7） |
| 各類別 | 覆蓋缺口 3、不一致 6、模糊 1、重複 1、規格不足 2 |

## 下一步

- 沒有 CRITICAL 問題，可以進入 `/implement`，建議先處理 HIGH。
- **U1**：`STORAGE_DIR` 相對路徑會在實作時直接造成錯誤，請手動修正 tasks.md 的 T005、T007。
- **C1**：用 `/task` 更新 tasks.md，在 Phase 5 的 NFR 約束補上 NFR-013。
- **C2、I2**：決定是否需要單本查詢；需要時用 `/dsl-refine` 補案例再用 `/task` 更新，不需要時用 `/api-plan` 移除 getAlbum。
- **C3**：決定是否要拒絕不支援的格式；需要時用 `/dsl-refine` 補案例再用 `/task` 更新，不需要時用 `/api-plan` 移除 importPhoto 的 415 回應。
- **I1、I3**：只需要更新 plan.md 的原始碼結構與介面盤點。
- **A1、I4、I5、U2**：spec 文字問題，可以用 `/clarify-over-specs` 處理，或手動修改 spec.md。
- **I6**：手動修改 research.md。
