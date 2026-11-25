# 實作計畫：{{feature_name}}

**Plan**：`{{plan_folder_name}}` | **日期**：{{plan_date}} | **規格**：[spec.md](./spec.md) | **研究紀錄**：[research.md](./research.md) | **技術堆疊**：[techstack.md](../../truth/techstack.md)

**輸入**：來自 `specs/plans/{{plan_folder_name}}/spec.md` 的功能規格

## 專案結構

### 文件（這個 plan）

```text
{{plan_docs_tree}}
```

### 原始碼（repo 根目錄）

```text
{{source_tree}}
```

**結構決策**：{{structure_decision}}

## 分析流程規劃

### 介面盤點

| 介面 ID | 介面 | 所屬端點 | 異動 | 依據需求 |
|---|---|---|---|---|
<!-- 重複開始：每個介面一列 -->
| {{interface_id}} | {{interface_name}} | {{endpoint_name}} | {{change_type}} | {{requirement_refs}} |
<!-- 重複結束 -->

### 分析 Wave

**共用輸入**（每個 Wave 的 sub-agent 皆須讀取）：`spec.md`、`specs/truth/techstack.md`

<!-- 重複開始：每個 Wave 一節 -->
**Wave {{wave_number}} — {{wave_endpoints_with_interface_ids}}**

- 分析重點：{{analysis_focus}}
- 相依：{{dependency_endpoint_outputs}}
- 委派：開 {{sub_agent_count}} 個 sub-agent，分別分析{{wave_endpoint_names}}。

<!-- 重複結束 -->
共盤點 {{endpoint_count}} 個端點、{{interface_count}} 個介面、{{wave_count}} 個 Wave，介面之間沒有循環依賴。
