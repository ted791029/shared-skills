# 研究紀錄（Phase 0）：{{feature_name}}

<!-- 重複開始：需求 plan 寫一次 -->
**Plan**：`{{plan_folder_name}}` | **日期**：{{research_date}} | **規格**：[spec.md](./spec.md)
<!-- 重複結束 -->
<!-- 重複開始：技術修正 plan 寫一次 -->
**Plan**：`{{plan_folder_name}}` | **日期**：{{research_date}} | **技術項**：[技術項.md](./技術項.md)
<!-- 重複結束 -->

使用者於規劃階段指定的技術方向：

<!-- 重複開始：每個技術方向一行 -->
- {{tech_direction}}
<!-- 重複結束 -->

---

<!-- 重複開始：沒有需要技術決策的議題時寫一次 -->
這次沒有需要技術決策的議題，沿用 [techstack.md](../../truth/techstack.md)。
<!-- 重複結束 -->

<!-- 重複開始：每項技術決策一段，依 R 編號排列 -->
## R-{{decision_number}} {{decision_title}}

- **對應需求**：{{requirement_refs}}
<!-- 重複開始：取代已交付 plan 的決策時一行，沒有則省略 -->
- **取代**：{{replaced_decision}}
<!-- 重複結束 -->
- **決策**：{{decision}}

<!-- 重複開始：決策需要以表格比較多個項目時一張表，沒有則省略 -->
| {{decision_table_header}} |
|{{decision_table_divider}}|
<!-- 重複開始：每個比較項目一列 -->
| {{decision_table_row}} |
<!-- 重複結束 -->
<!-- 重複結束 -->

- **理由**：{{rationale}}
<!-- 重複開始：每個補充欄位一行（如已知限制、確定性），沒有則省略 -->
- **{{extra_field_name}}**：{{extra_field_content}}
<!-- 重複結束 -->
<!-- 重複開始：有可比較的方案時一行，沒有則省略 -->
- **考慮過的替代方案**：{{alternatives_considered}}
<!-- 重複結束 -->

<!-- 重複結束 -->
