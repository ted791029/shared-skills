# 技術堆疊

本文件列出系統目前採用的全部技術與專案自行實作的模組。各技術的選用理由見研究紀錄，編號寫成 `<plan>/R-xx`，對應 `specs/plans/<plan>-*/research.md`（例如 `002/R-08` 是編號 002 的 plan 的 research.md 中的 R-08）。API 路徑、資料表、元件與檔案名稱、遷移版本不在本文件，以各端點的介面文檔與程式為準。

---

## 執行環境

| 項目 | 技術 | 版本 | 研究紀錄 |
|------|------|------|----------|
<!-- 重複開始：每個執行環境項目一列 -->
| {{environment_item}} | {{environment_technology}} | {{environment_version}} | {{plan_decision_refs}} |
<!-- 重複結束 -->

<!-- 重複開始：每個技術層級一節 -->
## {{layer_name}}

| 項目 | 技術 | 類型 | 版本 | 研究紀錄 |
|------|------|------|------|----------|
<!-- 重複開始：每項技術一列 -->
| {{tech_item}} | {{technology}} | {{tech_type}} | {{tech_version}} | {{plan_decision_refs}} |
<!-- 重複結束 -->

<!-- 重複結束 -->
## 套件安裝清單

| Workspace | 相依類型 | 套件與版本 |
|-----------|----------|------------|
<!-- 重複開始：每個 workspace 的每種相依類型一列 -->
| {{workspace}} | {{dependency_type}} | {{packages_with_versions}} |
<!-- 重複結束 -->
