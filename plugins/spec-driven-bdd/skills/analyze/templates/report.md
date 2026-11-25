# 規格分析報告：{{feature_name}}

**Plan**：`{{plan_name}}` | **日期**：{{analysis_date}} | **產生方式**：`/analyze`

**結論**：{{gate_conclusion}}

## 分析範圍

| 產物 | 產出 skill | 涵蓋介面 | 狀態 |
|------|-----------|---------|------|
<!-- 重複開始：每份產物一列，依 spec、acceptance、research、techstack、plan、wave-report、各介面文檔、data-migration、涵蓋表、用語表、各端點資料夾、truth-changes、技術項、tasks 排列，沒有的產物不列；plan 的檔案寫成 plan 資料夾內的路徑，truth 的檔案寫成 `specs/truth/…` -->
| `{{artifact_path}}` | {{producer_skills}} | {{covered_interface_ids}} | {{artifact_status}} |
<!-- 重複結束 -->

## 前置檢查

| 檢查項目 | 結果 | 說明 |
|---------|------|------|
| plan 狀態（plan-package） | {{plan_state_result}} | {{plan_state_detail}} |
| 待補跑（plan-package） | {{pending_owners_result}} | {{pending_owners_detail}} |
| 交叉檢查（plan-package） | {{cross_check_result}} | {{cross_check_detail}} |
| 必要產物 | {{required_artifacts_result}} | {{required_artifacts_detail}} |
| 端點資料夾 | {{feature_endpoints_result}} | {{feature_endpoints_detail}} |
| 介面文檔 | {{interface_docs_result}} | {{interface_docs_detail}} |
| plan.md 結構檢查（check_plan.py） | {{check_plan_result}} | {{check_plan_detail}} |
| tasks.md 結構檢查（check_tasks.py） | {{check_tasks_result}} | {{check_tasks_detail}} |
| 憲法 | {{constitution_result}} | {{constitution_detail}} |

<!-- 重複開始：同一對話中已有前次分析時出現一次，否則省略 -->
## 與前次分析比較

| 變化 | 數量 | ID |
|------|------|----|
| 已解決 | {{resolved_count}} | {{resolved_ids}} |
| 仍存在 | {{remaining_count}} | {{remaining_ids}} |
| 新增 | {{new_count}} | {{new_ids}} |

**已解決的問題**：

<!-- 重複開始：每個已解決的問題一行 -->
- **{{resolved_id}}**（{{previous_severity}}）：{{resolution_summary}}
<!-- 重複結束 -->
<!-- 重複結束 -->

## 發現事項

| ID | 類別 | 嚴重度 | 位置 | 摘要 | 建議 |
|----|------|--------|------|------|------|
<!-- 重複開始：每個發現事項一列，依嚴重度由高到低排列 -->
| {{finding_id}} | {{finding_category}} | {{severity}} | {{finding_locations}} | {{finding_summary}} | {{finding_recommendation}} |
<!-- 重複結束 -->

## 需求覆蓋

| 需求 | plan 介面 | 任務 | 狀態 | 備註 |
|------|----------|------|------|------|
<!-- 重複開始：每個 FR、NFR 與需要建置的 SC 一列，依編號排列 -->
| {{requirement_id}} | {{plan_interface_ids}} | {{task_ids}} | {{coverage_status}} | {{coverage_note}} |
<!-- 重複結束 -->

**不列入覆蓋的成功標準**：{{excluded_success_criteria}}

## 受影響的既有功能

<!-- 重複開始：spec.md 的「受影響的既有功能」為「無」時出現一次，否則省略 -->
spec.md 沒有受影響的既有功能。
<!-- 重複結束 -->

<!-- 重複開始：spec.md 有受影響的既有功能時出現一次，否則省略 -->
| 既有功能 | 影響 | 對應的異動 | 狀態 |
|---------|------|-----------|------|
<!-- 重複開始：每個受影響的既有功能一列，依 spec.md 的順序排列 -->
| {{affected_function}} | {{affected_impact}} | {{affected_changes}} | {{coverage_status}} |
<!-- 重複結束 -->
<!-- 重複結束 -->

## 介面文檔覆蓋

| 介面 | 異動 | 介面文檔 | 負責任務 | 狀態 | 備註 |
|------|------|---------|---------|------|------|
<!-- 重複開始：每個 plan.md 介面盤點的介面一列，依介面盤點順序排列；異動為「無」的狀態寫「—（不檢查）」，DEL 寫「—（由移除任務處理）」 -->
| {{interface_id}} | {{interface_change}} | {{interface_doc_sections}} | {{responsible_task_ids}} | {{coverage_status}} | {{coverage_note}} |
<!-- 重複結束 -->

## 反向覆蓋

**未對應需求的任務**：{{unmapped_tasks_summary}}

<!-- 重複開始：每個未對應需求的任務一行 -->
- {{unmapped_task_id}}（{{finding_id}}）
<!-- 重複結束 -->

**這次異動的介面文檔段落中，未被 feature 或必讀涵蓋的**：{{uncovered_sections_summary}}

<!-- 重複開始：每個未被涵蓋的段落一行 -->
- `{{uncovered_section_anchor}}`（{{finding_id}}）
<!-- 重複結束 -->

## 指標

| 指標 | 數值 |
|------|------|
| 需求總數 | {{requirement_total}} |
| 任務總數 | {{task_total}} |
| 需求覆蓋率 | {{requirement_coverage}} |
| 介面文檔覆蓋率 | {{interface_doc_coverage}} |
| 發現事項 | {{finding_total_by_severity}} |
| 各類別 | {{finding_total_by_category}} |

## 下一步

- {{gate_next_action}}
<!-- 重複開始：每組要處理的發現事項一行，依嚴重度由高到低排列 -->
- **{{finding_ids}}**：{{next_action}}
<!-- 重複結束 -->
