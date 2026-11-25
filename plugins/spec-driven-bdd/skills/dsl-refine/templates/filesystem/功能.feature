@module:{{module_name}}
Feature: {{feature_name}}

  # 重複開始：所有 Example 共用同一個起點時寫一次
  Background:
    # 預設值：{{shared_start_defaults}}
    Given 系統處於 "{{shared_start_state}}"
  # 重複結束

  # 重複開始：每條 Rule 一組
  Rule: {{rule_statement}}

    # 重複開始：每個 Example 一組
    Example: {{data_scenario}}
      # 重複開始：沒有 Background 時寫一次
      # 預設值：{{start_defaults}}
      Given 系統處於 "{{start_state}}"
      # 重複結束
      # 重複開始：每個影響閱讀的預設值一行
      # 預設值：{{default_value_note}}
      # 重複結束
      # 重複開始：每個差異句一組
      {{difference_keyword}} {{difference_step}}
        # 重複開始：差異句帶 Data Table 時每列一行，第一列為表頭
        | {{difference_table_cell}} |
        # 重複結束
      # 重複結束
      When {{action_step}}
        # 重複開始：動作帶 Data Table 時每列一行，第一列為表頭
        | {{action_table_cell}} |
        # 重複結束
      # 重複開始：每個後續動作一行
      And {{additional_action_step}}
      # 重複結束
      Then {{assertion_step}}
        # 重複開始：斷言帶 Data Table 時每列一行，第一列為表頭
        | {{assertion_table_cell}} |
        # 重複結束
      # 重複開始：同一條規則的每個其他斷言一組
      And {{additional_assertion_step}}
        # 重複開始：斷言帶 Data Table 時每列一行，第一列為表頭
        | {{additional_assertion_table_cell}} |
        # 重複結束
      # 重複結束
    # 重複結束

    # 重複開始：每個只差資料的 Scenario Outline 一組
    Scenario Outline: {{outline_data_scenario}}
      # 重複開始：沒有 Background 時寫一次
      # 預設值：{{outline_start_defaults}}
      Given 系統處於 "{{outline_start_state}}"
      # 重複結束
      # 重複開始：每個差異句一行
      {{outline_difference_keyword}} {{outline_difference_step}}
      # 重複結束
      When {{outline_action_step}}
      Then {{outline_assertion_step}}
      # 重複開始：同一條規則的每個其他斷言一行
      And {{outline_additional_assertion_step}}
      # 重複結束

      Examples:
        | {{example_column}} |
        # 重複開始：每筆資料一列
        | {{example_value}} |
        # 重複結束
    # 重複結束
  # 重複結束
