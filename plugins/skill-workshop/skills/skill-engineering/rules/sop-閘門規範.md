# SOP 閘門規範

## Rule 1 -- Step 必須由 next 取得並讀完部件

**強度：MUST**

建立執行紀錄後，每個 Step 開始前必須以 `next` 取得，讀完它印出的掛載部件全文才開始執行；`next` 列出掛載 skill 時，必須以 Skill 工具載入該 skill 並依其 SOP 執行。不得憑記憶或 SKILL.md 的 Step 文字直接執行。

### Good Example

這個範例先以 `next` 取得 Step，讀完印出的編排判斷規範全文才撰寫編排。

```text
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" next --log work/gate.json
## 下一個 Step：4.1（Phase：編排衍生）
THINK 依 [編排判斷規範](rules/編排判斷規範.md) 為每個 Step 決定 deriver 與執行順序。
---------- 掛載部件全文：rules/編排判斷規範.md
（全文）
→ 依 Rule 1～5 逐 Step 寫出 deriver 與理由
```

### Bad Example

這個範例沒有執行 `next`，依印象撰寫編排，漏掉編排判斷規範 Rule 4 要求的刪除清單，使用者在確認閘門看不到要刪除的部件。

```text
（直接看 SKILL.md 的 Phase 4 Step 1）
編排：Phase 1 Step 2 → skill-derive-rule
```

## Rule 2 -- 完成產出後才以 done 記錄

**強度：MUST**

`done` 只能在該 Step 的產出已實際完成後執行，`--evidence` 寫出產出位置或結論；不得先記錄再補做，也不得在多個 Step 之後一次補記。

### Good Example

這個範例在描述檔案修改完成後才記錄，證據指向實際產出。

```text
（Edit SKILL.md 的 description 成功）
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 3.2 --log work/gate.json --evidence "SKILL.md description 補上與 artifact-to-skill-engineering 的分界"
```

### Bad Example

這個範例在 Edit 失敗後仍先記錄完成，之後若忘了補做，狀態表會顯示已執行，使用者無法從紀錄發現描述其實沒改。

```text
（Edit SKILL.md 失敗：尚未讀取檔案）
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 3.2 --log work/gate.json --evidence "description 已更新"
```

## Rule 3 -- ASK 回覆必須照錄使用者原話

**強度：MUST**

ASK Step 必須單獨向使用者提出該 Step 的問題並停下等待，`--question` 寫出這次提出的問題，`--reply` 只能填使用者在這次提問之後的回覆原文，不得引用先前對其他問題的回覆，也不得增刪任何字。

### Good Example

這個範例在編排確認時重新提問，回覆欄照錄使用者對編排提案本身的回答。

```text
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 4.2 --log work/gate.json --question "是否同意編排提案與刪除清單？" --reply "同意，但不要刪 rules/重構取捨規範.md" --evidence "刪除清單移除重構取捨規範"
```

### Bad Example

這個範例沒有重新提問，把使用者對根因的回覆當成編排的同意，還在原話後加上註記，使用者從沒看過刪除清單，狀態表卻顯示已同意。

```text
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 4.2 --log work/gate.json --question "編排提案" --reply "照新根因改（視同同意編排）" --evidence "使用者已同意"
```

## Rule 4 -- 確認後修改必須退回重新確認

**強度：MUST**

使用者在 ASK Step 確認過的內容（預期、根因、編排提案或刪除清單），之後需要修改時，必須以 `back` 退回該 ASK 之前產出該內容的 Step，修改後重新經過該 ASK，不得直接修改後繼續。

### Good Example

這個範例在驗證時發現需擴充 tdd Phase 1 Step 3 的範圍，退回編排 Step 重新提案並取得確認。

```text
驗證發現：綠燈、重構失去讀相關程式碼的 Step，需擴充 tdd Phase 1 Step 3
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" back 4.1 --log work/gate.json
（修改編排提案後重新提問 4.2）
```

### Bad Example

這個範例在使用者同意編排後，於驗證階段自行擴大修改範圍，使用者同意的提案與實際修改不一致，卻不知道有額外變更。

```text
驗證發現：需擴充 tdd Phase 1 Step 3 → 直接修改 tdd/SKILL.md
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 5.2 --log work/gate.json --evidence "演練通過，順便補上 Step 3"
```

## Rule 5 -- 跳過 Step 必須取得使用者同意

**強度：MUST**

不論改動大小，都不得自行跳過或縮減 Step。認為某 Step 不需要時，必須先向使用者說明該 Step 與跳過理由，取得同意後以 `skip` 記錄提問與回覆原文。SOP 標明僅適用於另一模式的 Phase 由 `done --mode` 標為不適用，不需詢問。

### Good Example

這個範例在認為零基推導沒有必要時先詢問，取得同意才跳過。

```text
提問：本次只改一個 Bad Example，SOP 不變，是否同意跳過 Phase 3 Step 1 零基推導？
使用者：可以
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" skip 3.1 --log work/gate.json --reason "改動不涉及 SOP" --question "是否同意跳過 Phase 3 Step 1 零基推導？" --reply "可以"
```

### Bad Example

這個範例以改動很小為由自行略過整個 Phase，沒有經過使用者，零基推導本可發現的上游問題被遺漏。

```text
改動很小，Phase 3 不需要，直接進入 Phase 4。
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 3.1 --log work/gate.json --evidence "不需要"
```

## Rule 6 -- 腳本拒絕時必須補做

**強度：MUST**

`done`、`skip` 或 `report` 拒絕或以非零結束時，必須依錯誤訊息補做缺漏的產出、提問或 Step 後重新執行，不得改寫產出以騙過檢查、改用其他方式記錄，或在 `report` 仍列出待執行 Step 時回報完成。

### Good Example

這個範例在腳本拒絕缺章節的報告後，依樣板補齊章節再記錄。

```text
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 2.3 --log work/gate.json --file work/落差分析報告.md --evidence "完成"
拒絕：產出檔 work/落差分析報告.md 缺少樣板章節 ['## 已排除假設']，請依樣板補齊後重新記錄
（補寫「已排除假設」章節的實際內容）
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 2.3 --log work/gate.json --file work/落差分析報告.md --evidence "根因：SOP 層缺少閘門"
```

### Bad Example

這個範例只補上空的章節標題騙過檢查，報告缺少已排除假設的內容，使用者確認根因時無法判斷其他可能性是否被排除過。

```text
拒絕：產出檔 work/落差分析報告.md 缺少樣板章節 ['## 已排除假設']
（在檔尾加上一行「## 已排除假設」）
$ uv run "D:/plugins/skill-workshop/skills/skill-engineering/scripts/sop_gate.py" done 2.3 --log work/gate.json --file work/落差分析報告.md --evidence "完成"
```
