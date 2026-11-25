| Wave | 端點 | Planner | 產出 | 狀態 |
|---|---|---|---|---|
<!-- 重複開始：每個 Wave 的每個端點一列，沒有排進 Wave 的端點排在最後 -->
| {{wave_number}} | {{endpoint_name}} | `{{planner_name}}` | {{planner_outputs}} | {{execution_status}} |
<!-- 重複結束 -->

## 不能改

| 端點 | 擋住的規則、條款或上游事實 | 應交給 |
|---|---|---|
<!-- 重複開始：每個回傳不能改的端點的每項擋住的對象一列 -->
| {{endpoint_name}} | {{blocking_rule_or_fact}} | {{handover_target}} |
<!-- 重複結束 -->

## 憲法衝突

| 端點 | 輸入文件與位置 | 衝突內容 | 條款 | 產出物處理 | 後續處理 |
|---|---|---|---|---|---|
<!-- 重複開始：每個 Planner 依條款化解的衝突一列 -->
| {{endpoint_name}} | {{input_location}} | {{conflict_content}} | {{clause_id}} | {{output_handling}} | {{follow_up}} |
<!-- 重複結束 -->
