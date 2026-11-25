---

description: "{{feature_name}}的實作任務清單"
---

# 任務：{{feature_name}}

[紅燈]／[綠燈]／[重構]／[重跑]／[驗證] 由 implement 交給 `/bdd red|green|refactor|rerun|verify`，沒有標記的任務由 implement 直接實作；Phase 依編號、Phase 內依列出順序執行；Phase 標頭的 NFR 約束、預計修改與必讀適用於該 Phase 的每個任務

<!-- 重複開始：需求 plan 才有 Setup 與 Foundational，技術修正 plan 沒有，可無 -->
## Phase 1：Setup

<!-- 重複開始：這次沒有新增或修改套件時只寫這一句，可無 -->
{{no_setup_task_reason}}

<!-- 重複結束 -->
<!-- 重複開始：每個 Setup 任務一項 -->
- [ ] {{task_id}} {{task_description}}
<!-- 重複開始：每個必讀位置一行 -->
  - 📎 必讀：`{{reference_anchor}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複結束 -->

## Phase 2：Foundational

<!-- 重複開始：這次沒有共用的骨架要建立時只寫這一句，可無 -->
{{no_foundational_task_reason}}

<!-- 重複結束 -->
<!-- 重複開始：每個 Foundational 任務一項 -->
- [ ] {{task_id}} {{task_description}}
<!-- 重複開始：任務有 NFR 約束時一行，可無 -->
  - NFR 約束：{{nfr_constraint_ids}}
<!-- 重複結束 -->
<!-- 重複開始：每個必讀位置一行 -->
  - 📎 必讀：`{{reference_anchor}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複結束 -->

<!-- 重複結束 -->
<!-- 重複開始：feature_summary.py 的 phases 每一項一個 Phase；標題取 phase（已有勾選階段任務的 feature 與技術修正 plan 是「修正 <端點資料夾>/<檔名>.feature」），範疇取 scope，綠燈的結尾在整份 feature 時是「讓 feature 通過」，以 Rule 名稱列出時是「讓這些 Rule 通過」 -->
## Phase {{phase_number}}：{{phase_title}}

**驗收 AC**：{{acceptance_ids_or_none}}

<!-- 重複開始：綠燈有 NFR 約束時一段，可無 -->
**NFR 約束**：{{nfr_constraint_ids}}

<!-- 重複結束 -->
**預計修改**：{{planned_file_paths}}

**📎 必讀**：

<!-- 重複開始：每個必讀位置一行 -->
- `{{reference_anchor}}` — {{reference_reason}}
<!-- 重複結束 -->

- [ ] {{red_task_id}} [紅燈] 範疇：`{{feature_scope}}`：撰寫 {{rule_count}} 條 Rule、{{example_count}} 個 Example 的 step definitions{{driver_suffix}}，確認因{{expected_failure_reason}}而失敗
- [ ] {{green_task_id}} [綠燈] 範疇：`{{feature_scope}}`：{{green_task_description}}，{{green_task_ending}}
- [ ] {{refactor_task_id}} [重構] 範疇：`{{feature_scope}}`：整理{{refactor_target}}，不改變行為

<!-- 重複結束 -->
<!-- 重複開始：feature_summary.py 有 reruns 時一個 Phase，可無 -->
## Phase {{rerun_phase_number}}：重跑

<!-- 重複開始：reruns 每一項一個任務 -->
- [ ] {{task_id}} [重跑] 範疇：`{{rerun_scope}}`：{{rerun_changes}}，確認既有 step 不用改後重新執行
<!-- 重複開始：rows 的每一列一行 -->
  - 📎 必讀：`truth-changes.md › {{changed_target}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複結束 -->

<!-- 重複結束 -->
## Phase {{remove_phase_number}}：移除

<!-- 重複開始：deletions 與 withdrawn 都沒有任何一項時只寫這一句，可無 -->
這個 plan 沒有要移除的內容。

<!-- 重複結束 -->
<!-- 重複開始：有不需要移除程式的項目時一段，可無 -->
**不另列任務**：

<!-- 重複開始：每個不需要移除程式的 DEL 列、只刪除 Example 的列或撤回的 Rule 一行 -->
- {{deleted_target_or_withdrawn_rule}}：{{no_task_reason}}
<!-- 重複結束 -->

<!-- 重複結束 -->
<!-- 重複開始：每個移除任務一項 -->
- [ ] {{task_id}} {{removal_description}}
<!-- 重複開始：這個任務處理的每一列 DEL 或只刪除 Example 的列一行，可無 -->
  - 📎 必讀：`truth-changes.md › {{deleted_target}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複開始：這個任務處理的每條撤回的 Rule 一行（實作它的已勾選任務），可無 -->
  - 📎 必讀：`tasks.md › {{implementing_task_id}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複開始：其他每個必讀位置一行，可無 -->
  - 📎 必讀：`{{reference_anchor}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複結束 -->

## Phase {{tech_phase_number}}：技術項

<!-- 重複開始：技術項.md 不存在或沒有任何一行時只寫這一句，可無 -->
這個 plan 沒有技術項。

<!-- 重複結束 -->
<!-- 重複開始：有不需要修改程式的技術項時一段，可無 -->
**不另列任務**：

<!-- 重複開始：每個不需要修改程式的技術項一行 -->
- {{tech_item_excerpt}}：{{no_task_reason}}
<!-- 重複結束 -->

<!-- 重複結束 -->
<!-- 重複開始：每個要修改程式的技術項一項 -->
- [ ] {{task_id}} {{task_description}}
  - 📎 必讀：`技術項.md › {{tech_item_excerpt}}` — {{reference_reason}}
<!-- 重複開始：其他每個必讀位置一行，可無 -->
  - 📎 必讀：`{{reference_anchor}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複結束 -->

<!-- 重複開始：需求 plan 才有 NFR 重構與 Polish，技術修正 plan 沒有，可無 -->
## Phase {{nfr_phase_number}}：NFR 重構

**不另列任務**：

<!-- 重複開始：每組不需另列任務的 NFR 一行 -->
- {{nfr_ids}}：{{no_task_reason}}
<!-- 重複結束 -->

<!-- 重複開始：每個不屬於重構的 NFR 工作（量測、門檻對照）一項，可無 -->
- [ ] {{task_id}} {{nfr_work_description}}
<!-- 重複開始：每個必讀位置一行 -->
  - 📎 必讀：`{{reference_anchor}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複結束 -->
<!-- 重複開始：每個有 NFR 需要重構的端點資料夾一項（行內的「NFR 編號：重構內容」每個 NFR 一組，以「；」接續），可無 -->
- [ ] {{task_id}} [重構] 範疇：`specs/truth/features/{{endpoint_folder}}/`：{{nfr_ids}}：{{nfr_refactor_item}}
<!-- 重複開始：每個必讀位置一行 -->
  - 📎 必讀：`{{reference_anchor}}` — {{reference_reason}}
<!-- 重複結束 -->
<!-- 重複結束 -->

## Phase {{polish_phase_number}}：Polish

<!-- 重複開始：每個 Polish 任務一項 -->
- [ ] {{task_id}} {{task_description}}
<!-- 重複結束 -->

<!-- 重複結束 -->
## Phase {{verify_phase_number}}：Verify

- [ ] {{task_id}} [驗證] 執行所有端點的完整測試並與上次結果比對
