# 專案憲法

**版本**：{{constitution_version}} ｜ **最後修訂**：{{last_amended_date}}

本憲法只約束 SDD 流程中各 skill 的產出物內容與格式，不改變流程本身。

- `skills/<產出 skill>/<產出物>.md` 約束該 skill 的一份產出物；檔案不存在代表該產出物沿用 skill 內建規範。
- 任何寫入該產出物的 skill 都受同一份憲法檔約束，例如 clarify-over-specs 寫回 spec.md 時也遵循 `skills/specify/spec.md`。
- `shared/` 的共通條款不會自動生效，只有被產出物檔的「引用共通條款」列出時才約束該產出物。
- 覆寫內建 Rule 的條款必須在「覆寫對象」寫明被覆寫的 Rule。

## 目錄

| 產出物 | 憲法檔 | 條款 | 引用共通條款 |
| --- | --- | --- | --- |
<!-- 重複開始：每份已有憲法檔的產出物一列 -->
| {{product_path}} | [skills/{{producer_skill}}/{{product_file_name}}.md](skills/{{producer_skill}}/{{product_file_name}}.md) | {{clause_ids}} | {{referenced_shared_clause_ids}} |
<!-- 重複結束 -->

## 共通條款

| 條款 | 檔案 |
| --- | --- |
<!-- 重複開始：每條共通條款一列 -->
| {{shared_clause_id}} | [shared/{{shared_topic}}.md](shared/{{shared_topic}}.md) |
<!-- 重複結束 -->

## 修訂紀錄

| 版本 | 日期 | 異動條款 | 起因需求 |
| --- | --- | --- | --- |
<!-- 重複開始：每次修訂一列，依版本由舊到新 -->
| {{revision_version}} | {{revision_date}} | {{changed_clauses}} | {{triggering_need}} |
<!-- 重複結束 -->
