# 功能規格：{{feature_name}}

**Plan**：`{{plan_folder_name}}`

**建立日期**：{{created_date}}

## 釐清紀錄

<!-- 重複開始：每個釐清場次一段 -->
### 場次 {{session_date}}

<!-- 重複開始：每組問答一行 -->
- 問：{{clarify_question}} → 答：{{clarify_answer}}
<!-- 重複結束 -->
<!-- 重複結束 -->

**輸入**：使用者描述：「{{user_description}}」

## 使用者情境與測試 *（必填）*

<!-- 重複開始：每個使用者故事一段，依優先順序排列 -->
### 使用者故事 {{story_number}} - {{story_title}}（優先順序：{{story_priority}}）

{{story_description}}

**為何此優先順序**：{{priority_rationale}}

**獨立測試**：{{independent_test}}

**驗收情境**：

<!-- 重複開始：每個驗收情境一項 -->
{{scenario_number}}. **假設** {{scenario_given}}，**當** {{scenario_when}}，**那麼** {{scenario_then}}。
<!-- 重複結束 -->

**功能需求**：

<!-- 重複開始：每條功能需求一行 -->
- **FR-{{fr_number}}**：{{functional_requirement}}
<!-- 重複結束 -->

**非功能性需求**：

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**（{{nfr_category}}）：{{non_functional_requirement}}
<!-- 重複結束 -->

---
<!-- 重複結束 -->

### 邊界情況

<!-- 重複開始：每個邊界情況一行 -->
- {{edge_case_condition}}時：{{edge_case_handling}}
<!-- 重複結束 -->

## 全域需求

### 功能需求

<!-- 重複開始：每條功能需求一行 -->
- **FR-{{fr_number}}**：{{functional_requirement}}
<!-- 重複結束 -->

### 非功能性需求

#### 效能

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**：{{non_functional_requirement}}
<!-- 重複結束 -->

#### 容量

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**：{{non_functional_requirement}}
<!-- 重複結束 -->

#### 可靠性與資料完整性

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**：{{non_functional_requirement}}
<!-- 重複結束 -->

#### 安全與隱私

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**：{{non_functional_requirement}}
<!-- 重複結束 -->

#### 易用性與一致性

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**：{{non_functional_requirement}}
<!-- 重複結束 -->

#### 無障礙

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**：{{non_functional_requirement}}
<!-- 重複結束 -->

#### 相容性

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**：{{non_functional_requirement}}
<!-- 重複結束 -->

#### 可維護性與可測試性

<!-- 重複開始：每條非功能性需求一行 -->
- **NFR-{{nfr_number}}**：{{non_functional_requirement}}
<!-- 重複結束 -->

## 關鍵實體

<!-- 重複開始：每個實體一行 -->
- **{{entity_name}}**：{{entity_description}}
<!-- 重複結束 -->

## 成功標準 *（必填）*

### 可量測成果

<!-- 重複開始：每條成功標準一行 -->
- **SC-{{sc_number}}**：{{success_criterion}}
<!-- 重複結束 -->

## 假設

<!-- 重複開始：每條假設一行 -->
- {{assumption}}
<!-- 重複結束 -->

## 受影響的既有功能

<!-- 重複開始：每個受影響的既有功能一行 -->
- {{existing_function}}：{{impact_summary}}
<!-- 重複結束 -->
<!-- 重複開始：沒有受影響的既有功能時寫一次 -->
無
<!-- 重複結束 -->
