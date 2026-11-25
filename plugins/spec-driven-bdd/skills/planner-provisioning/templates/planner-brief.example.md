# Planner 委派簡報：api-plan

## 負責端點

後端：提供 API 給其他端點使用的伺服器端系統。

## Artifact 敘述

### `contracts/openapi.yaml`

- 歸屬：truth
- 格式：OpenAPI 3.1（YAML）
- 記載資訊：
  - 每個外層介面操作對應的 API 路徑、方法與用途
  - 請求參數、請求本文與回應本文的結構與型別
  - 錯誤回應的狀態碼與錯誤訊息結構
  - 分頁、排序與篩選的參數
  - 檔案上傳與二進位內容的請求與回應形式
  - 每個 API 需要讀寫的資料與檔案，供內層端點分析
- 範例取材：照片相簿整理器 `plan.md` 介面盤點的 API-01 匯入 API、API-02 相簿 API、API-03 照片 API

## 流程需求

### 呼叫介面

- 呼叫參數：`plan.md` 路徑、Wave 編號、端點名稱
- plan 狀態：第一步委派 plan-package 的 check，帶入 `plan.md` 所在的資料夾與本 Planner 的名稱，確認是進行中的 plan 並取得待補跑與本 Planner 的輸入差異，被拒絕時停止
- 讀取輸入：
  - `plan.md`「共用輸入」列出的文檔
  - `plan.md` 介面盤點中所屬端點為此端點的介面列，含「異動」欄
  - `plan.md` 該 Wave 的「分析重點」
  - `plan.md` 該 Wave「相依」列出的前置端點，依 planner-provisioning 的 Planner 配對規範找到負責的 Planner 並讀取它這次的產出
  - `specs/truth/` 中介面列涉及的既有文檔
- 產出位置：歸屬為 plan 的文檔寫在 `plan.md` 所在的 plan 資料夾，歸屬為 truth 的文檔寫在 `specs/truth/` 並只增修這次異動的內容
- truth 異動：修改 truth 前委派 truth-changes 的 inventory 盤點這次的新增、修改與刪除，修改後委派 truth-changes 的 record 記進 plan 的 `truth-changes.md` 並核對
- 依差異：check 回報本 Planner 在這個 plan 有紀錄且是待補跑時，依 plan-package 的串接規範只對列出的輸入差異逐項判斷連帶異動或不受影響；被交辦修正時，交辦內容就是這次的差異
- 上游問題：發現 `plan.md` 的介面列缺需求、需要新增或修改介面時，只回報 system-analysis，不自己修改 `plan.md`
- 開發發現：分析中發現規格沒寫的行為，或既有文檔與程式不一致時，委派 dev-finding 的 record
- 憲法：撰寫前依 constitution 的憲法套用規範讀取每份產出文檔適用的憲法條款，撰寫時遵循條款，寫入後逐條核對作用位置，並以條款的禁止事項掃描整份文檔，修正違反之處；與本 plan PM 核准的 AC、FR、NFR 衝突而無法同時符合時回報不能改，要上游擁有者修正的後續處理經 dev-finding 記成技術項
- 結尾：這次的結果是「不能改」（被規則或憲法擋住、上游事實錯了或缺了）時，列出擋住的規則、條款或上游事實與交辦對象，不記錄並停止；結果是「改了」或「不用改」時，最後一步委派 plan-package 的 record 記錄
- description：只寫觸發時機，寫明負責的端點類型與介面 ID 前綴，不寫產出與其他 skill

### 不在範圍

- 資料表欄位、索引與交易邊界（交由 data-plan）
- 原始檔與縮圖的目錄結構與命名規則（交由 storage-plan）
- 畫面配置、互動與文案（交由 ui-ux-plan）
- 程式碼實作與任務拆解（交由後續任務拆解）
