# SOP 精簡規範

## Rule 1 -- SOP step 必須對應真實動作

**強度：MUST**

每個 SOP step 必須對應一個 agent 實際會執行的動作（如讀取、判斷、撰寫、詢問、委派），並產生可驗證的結果。不得寫佔位、宣告或沒有實際產出的 step。

### Good Example

這個範例每個 step 都對應 agent 會執行的動作，可直接驗證產出。

```markdown
1. WRITE 撰寫每個 Phase 的重點步驟。
2. THINK 確認 step 是否符合格式。
```

### Bad Example

這個範例的 step 是沒有產出的佔位描述，agent 無法執行也無法驗證。

```markdown
1. 準備開始撰寫 SOP。
2. 處理相關內容。
```

## Rule 2 -- 必須採最短可執行流程

**強度：MUST**

SOP 只包含完成任務所需的最少 step。逐一檢驗每個 step：在該 step 要處理的情境下（如條件式 step 的條件成立、檢查 step 遇到有錯的草稿）刪除它，任務仍能完成且產出不變，該 step 即為多餘，必須刪除。

### Good Example

這個範例的任務是撰寫 RuleFile；第 3 步在需求不明時刪除會無法釐清需求，其餘 step 刪除後都會缺少必要產出。

```markdown
1. READ 讀取使用者需求與目標 RuleFile。
2. THINK 判斷需要規範的項目。
3. ASK 需求不明時詢問使用者。
4. WRITE 撰寫每條 Rule。
```

### Bad Example

這個範例的第 2、4 步刪除後任務仍能完成、產出不變，屬於多餘 step，徒增執行步驟與 context 成本。

```markdown
1. READ 讀取使用者需求與目標 RuleFile。
2. THINK 再次確認使用者需求。
3. WRITE 撰寫每條 Rule。
4. WRITE 存檔。
```
