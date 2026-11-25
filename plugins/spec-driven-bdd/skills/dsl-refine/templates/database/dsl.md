# {{endpoint_name}} DSL

## 參數對照

多列句型共用的「業務值 → 技術目標」對照，型別名稱就是小標題。只有一兩列用到的對照，直接寫在該列。值中獨立的 N 代表數字，X 代表任意名稱。

<!-- 重複開始：每個共用型別一組 -->
### `{{type_reference}}`

| 值 | {{mapping_column}} |
|---|---|
<!-- 重複開始：每個值一列 -->
| {{type_value}} | {{technical_target}} |
<!-- 重複結束 -->
<!-- 重複結束 -->

## Given 句型

差異句：起點句（Background 或 Example 的第一句 Given）只建立起點，之後的 Given 用 When 句型把狀態推進到需要的樣子。step definition 要讓這些句型在 Given 與 When 都能使用；寫在 Given 時只執行動作，不算進「這次操作」，也不更新操作前的快照；失敗時不攔截錯誤，讓測試直接失敗。

| Given 句型 | 範例 | 句型參數 | Data Table 參數 | 測試撰寫語意 |
|---|---|---|---|---|
<!-- 重複開始：每個 Given 句型一列 -->
| `{{given_pattern}}` | {{given_example}} | {{given_parameters}} | {{given_data_table}} | {{given_semantics}} |
<!-- 重複結束 -->

## When 句型

| When 句型 | 範例 | 句型參數 | Data Table 參數 | 測試撰寫語意 |
|---|---|---|---|---|
<!-- 重複開始：每個 When 句型一列 -->
| `{{when_pattern}}` | {{when_example}} | {{when_parameters}} | {{when_data_table}} | {{when_semantics}} |
<!-- 重複結束 -->

## Then 句型

| Then 句型 | 範例 | 句型參數 | Data Table 參數 | 測試撰寫語意 |
|---|---|---|---|---|
<!-- 重複開始：每個 Then 句型一列 -->
| `{{then_pattern}}` | {{then_example}} | {{then_parameters}} | {{then_data_table}} | {{then_semantics}} |
<!-- 重複結束 -->

## Step 檔對照

每個句型歸屬一個模組與能力。Step 檔路徑相對於專案測試設定中本端點載入的 step 目錄；`shared` 只收不屬於任何模組領域的句型。

| 模組 | 能力 | Step 檔 | 句型 |
|---|---|---|---|
<!-- 重複開始：每個能力一列 -->
| {{module_name}} | {{capability_id}} | `{{step_file_path}}` | {{capability_patterns}} |
<!-- 重複結束 -->
