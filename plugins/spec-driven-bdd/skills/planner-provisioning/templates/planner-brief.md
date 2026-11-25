# Planner 委派簡報：{{planner_name}}

## 負責端點

{{endpoint_type_description}}

## Artifact 敘述

<!-- 重複開始：每份產出文檔一節 -->
### `{{output_doc_path}}`

- 歸屬：{{output_ownership}}
- 格式：{{output_doc_format}}
- 記載資訊：
<!-- 重複開始：每項資訊一行 -->
  - {{recorded_information}}
<!-- 重複結束 -->
- 範例取材：{{example_source}}
<!-- 重複結束 -->

## 流程需求

### 呼叫介面

- 呼叫參數：`plan.md` 路徑、Wave 編號、端點名稱
- plan 狀態：第一步委派 plan-package 的 check，帶入 `plan.md` 所在的資料夾與本 Planner 的名稱，確認是進行中的 plan 並取得待補跑與本 Planner 的輸入差異，被拒絕時停止
- 讀取輸入：
  - `plan.md`「共用輸入」列出的文檔
  - `plan.md` 介面盤點中所屬端點為此端點的介面列，含「異動」欄
  - `plan.md` 該 Wave 的「分析重點」
  - `plan.md` 該 Wave「相依」列出的前置端點，依 planner-provisioning 的 Planner 配對規範找到負責的 Planner 並讀取它這次的產出
<!-- 重複開始：有歸屬為 truth 的文檔時一行，沒有則省略 -->
  - `specs/truth/` 中介面列涉及的既有文檔
<!-- 重複結束 -->
- 產出位置：歸屬為 plan 的文檔寫在 `plan.md` 所在的 plan 資料夾，歸屬為 truth 的文檔寫在 `specs/truth/` 並只增修這次異動的內容
<!-- 重複開始：有歸屬為 truth 的文檔時一行，沒有則省略 -->
- truth 異動：修改 truth 前委派 truth-changes 的 inventory 盤點這次的新增、修改與刪除，修改後委派 truth-changes 的 record 記進 plan 的 `truth-changes.md` 並核對
<!-- 重複結束 -->
- 依差異：check 回報本 Planner 在這個 plan 有紀錄且是待補跑時，依 plan-package 的串接規範只對列出的輸入差異逐項判斷連帶異動或不受影響；被交辦修正時，交辦內容就是這次的差異
- 上游問題：發現 `plan.md` 的介面列缺需求、需要新增或修改介面時，只回報 system-analysis，不自己修改 `plan.md`
- 開發發現：分析中發現規格沒寫的行為，或既有文檔與程式不一致時，委派 dev-finding 的 record
- 憲法：撰寫前依 constitution 的憲法套用規範讀取每份產出文檔適用的憲法條款，撰寫時遵循條款，寫入後逐條核對作用位置，並以條款的禁止事項掃描整份文檔，修正違反之處；與本 plan PM 核准的 AC、FR、NFR 衝突而無法同時符合時回報不能改，要上游擁有者修正的後續處理經 dev-finding 記成技術項
- 結尾：這次的結果是「不能改」（被規則或憲法擋住、上游事實錯了或缺了）時，列出擋住的規則、條款或上游事實與交辦對象，不記錄並停止；結果是「改了」或「不用改」時，最後一步委派 plan-package 的 record 記錄
- description：只寫觸發時機，寫明負責的端點類型與介面 ID 前綴，不寫產出與其他 skill

### 不在範圍

<!-- 重複開始：每項一行 -->
- {{out_of_scope_item}}（交由 {{responsible_party}}）
<!-- 重複結束 -->
