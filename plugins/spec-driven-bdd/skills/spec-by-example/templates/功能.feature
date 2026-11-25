Feature: {{feature_name}}

  # 重複開始：所有 AC 的起點句相同時寫一次
  Background:
    # 重複開始：起點內容需要說明時一行
    # 預設值：{{shared_start_state_note}}
    # 重複結束
    Given 系統處於 "{{shared_start_state_name}}"
  # 重複結束

  # 重複開始：每條 Rule 一組
  Rule: {{rule_statement}}

    # 重複開始：每個 Example 一組
    # 涵蓋：{{covered_story_and_requirement_ids}}
    Example: {{acceptance_id}} {{data_scenario}}
      # 重複開始：沒有 Background 時寫一次
      # 重複開始：起點內容需要說明時一行
      # 預設值：{{start_state_note}}
      # 重複結束
      Given 系統處於 "{{start_state_name}}"
      # 重複結束
      # 重複開始：每個差異句一組
      # 重複開始：這一句是受它影響的第一個步驟時，每個影響閱讀的預設值一行
      # 預設值：{{difference_default_value_note}}
      # 重複結束
      {{difference_keyword}} {{difference_step}}
        # 重複開始：差異句帶 Data Table 時每列一行，第一列為表頭
        | {{difference_table_cell}} |
        # 重複結束
      # 重複結束
      # 重複開始：旅程的每一段 When／Then 一組
      # 重複開始：這一段有待澄清處時，在受影響的步驟或表格正上方一行
      # [NEED CLARIFICATION] {{clarification_question}}？暫以「{{assumed_answer}}」撰寫
      # 重複結束
      # 重複開始：這一段有受它影響的第一個步驟時，在該步驟正上方，每個影響閱讀的預設值一行
      # 預設值：{{step_default_value_note}}
      # 重複結束
      When {{action_step}}
        # 重複開始：動作帶 Data Table 時每列一行，第一列為表頭
        | {{action_table_cell}} |
        # 重複結束
      # 重複開始：這一段的每個後續動作一行
      And {{additional_action_step}}
      # 重複結束
      Then {{outcome_step}}
        # 重複開始：結果帶 Data Table 時每列一行，第一列為表頭
        | {{outcome_table_cell}} |
        # 重複結束
      # 重複開始：這一段的每個後續結果一組
      And {{additional_outcome_step}}
        # 重複開始：後續結果帶 Data Table 時每列一行，第一列為表頭
        | {{additional_outcome_table_cell}} |
        # 重複結束
      # 重複結束
      # 重複結束
    # 重複結束
  # 重複結束
