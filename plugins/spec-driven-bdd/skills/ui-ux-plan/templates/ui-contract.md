# UI 契約：{{feature_name}}

**Plan**：`{{plan_folder_name}}`

## 共用約定

<!-- 重複開始：每項共用約定一行 -->
- {{convention_topic}}：{{convention_rule}}
<!-- 重複結束 -->

<!-- 重複開始：每個介面一節 -->
## {{interface_id}} {{interface_name}}

**路由**：{{interface_route}}
**定位**：`{{interface_locator}}`

### 操作

| 操作 | 互動 | 需要內層提供 |
|---|---|---|
<!-- 重複開始：每個操作一列 -->
| {{operation_name}} | {{interaction_description}} | {{inner_needs}} |
<!-- 重複結束 -->

### 狀態

| 狀態 | 呈現 |
|---|---|
| 成功 | {{success_presentation}} |
| 載入 | {{loading_presentation}} |
| 空狀態 | {{empty_presentation}} |
| 錯誤 | {{error_presentation}} |

### 文案與無障礙

| 項目 | 文案 |
|---|---|
<!-- 重複開始：每項文案一列 -->
| {{copy_item}} | {{copy_text}} |
<!-- 重複結束 -->

<!-- 重複結束 -->
