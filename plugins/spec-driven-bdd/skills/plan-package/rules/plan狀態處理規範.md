# plan 狀態處理規範

## Rule 1 -- 被拒絕時不得繞過

**強度：MUST**

腳本拒絕開立或檢查時，只能回報並停止。不得手動建立 plan 資料夾、撰寫或修改 `.plan.json`、自行 commit 或還原 truth 的修改來讓檢查通過，呼叫的 skill 也不得繼續往下做。以下 Example 皆對照此結果：

```text
open 的結果：拒絕，已有進行中的 plan 004-ranking
```

### Good Example

這個範例回報後停止，沒有建立任何檔案。

```text
無法開立新的 plan：已有進行中的 plan 004-ranking。
下一步：先完成並交付它，或放棄它。
（停止，不撰寫 spec.md）
```

### Bad Example

這個範例手動建立資料夾繞過拒絕，兩個 plan 同時修改 truth，交付時無法分辨哪些異動屬於哪個 plan，基準也不是由腳本記錄的。

```text
已有進行中的 plan 004-ranking，改為手動建立 specs/plans/005-chat-emoji/ 與 .plan.json，繼續撰寫 spec.md。
```

## Rule 2 -- 回報必須完整轉述原因與下一步

**強度：MUST**

腳本給的每一項拒絕原因、它附帶的檔案清單與下一步都必須逐項轉述，不得只挑一項、省略清單或換成自己的建議；下一步有多個選擇時由使用者決定。以下 Example 皆對照此結果：

```text
open 的結果：拒絕
- 已有進行中的 plan 004-ranking；下一步：先交付或放棄
- truth 有 2 個未 commit 的修改（specs/truth/contracts/components/schemas/Error.yaml、specs/truth/data/房間.dbml）；下一步：請使用者決定 commit 或還原
```

### Good Example

這個範例兩項原因都轉述，檔案清單完整，選擇留給使用者。

```text
無法開立新的 plan，原因有兩項：
1. 已有進行中的 plan 004-ranking。請先交付或放棄它。
2. truth 有 2 個未 commit 的修改，不屬於任何 plan：
   - specs/truth/contracts/components/schemas/Error.yaml
   - specs/truth/data/房間.dbml
   請決定要 commit 還是還原這些修改。
```

### Bad Example

這個範例只轉述一項原因，使用者處理完進行中的 plan 後會再被拒絕一次，也不知道是哪些 truth 檔案有未 commit 的修改。

```text
無法開立新的 plan，請先處理進行中的 plan 004-ranking。
```

## Rule 3 -- 已交付的 plan 不得修改

**強度：MUST**

目標是已交付的 plan 時，不得修改它資料夾中的任何檔案，也不得把它的狀態改回進行中。需要修正時回報以新的 plan 處理。以下 Example 皆對照此情境：

```text
使用者：003-room-chat 的 spec.md 有個錯字，幫我改掉
check 的結果：拒絕，003-room-chat 已交付
```

### Good Example

這個範例回報唯讀與處理方式後停止，沒有修改已交付的檔案。

```text
003-room-chat 已交付，內容唯讀。要修正請以 /specify 開立新的 plan。
（停止）
```

### Bad Example

這個範例以只是錯字為由直接修改，已交付的 spec.md 與當時 commit 的內容不再一致，之後無法得知 PM 當時核准的是哪個版本。

```text
只是錯字，不影響內容，直接修改 specs/plans/003-room-chat/spec.md。
```

## Rule 4 -- 放棄只轉述還原步驟

**強度：MUST**

abandon 只把腳本輸出的還原步驟、將被捨棄的變更與提醒轉述給使用者，由使用者自行執行。不得執行其中任何指令，也不得刪除 plan 資料夾或修改 `.plan.json`。

### Good Example

這個範例只轉述步驟，沒有執行任何指令。

```text
要放棄 004-ranking，請自行執行以下步驟：
1. 還原 truth 中被修改與刪除的檔案：git restore --source=d35575b --staged --worktree -- "specs/truth"
2. 刪除 truth 中這次新增的檔案：先以 git clean -nd -- "specs/truth" 預覽，確認後執行 git clean -fd -- "specs/truth"
3. 刪除 plan 資料夾 "specs/plans/004-ranking"
我沒有修改任何檔案。
```

### Bad Example

這個範例直接執行還原與刪除，使用者還沒確認的修改被永久刪除，無法復原。

```text
已執行 git restore 與 git clean 還原 truth，並刪除 specs/plans/004-ranking，004-ranking 已放棄。
```

## Rule 5 -- check 必須帶入目標 plan 與擁有者

**強度：MUST**

check 必須以 `--plan` 帶入呼叫者的目標 plan 資料夾名稱（Planner 是呼叫參數指定的 plan.md 所在的資料夾），呼叫者是相依表中的擁有者、而且是要開始執行它的 SOP 時另以 `--owner` 帶入它的 skill 名稱（帶 `--owner` 會記下開始時間，之後要以 record 結束；只想查詢狀態時改用 `plan_trace.py status`）；不是擁有者的 skill（例如 implement、analyze、planner-provisioning）不帶 `--owner`。不得省略 `--plan` 而依賴唯一進行中的 plan，否則呼叫者指定的已交付 plan 會被換成另一個進行中的 plan。以下 Example 皆對照此呼叫：

```text
api-plan 由 system-analysis 委派，呼叫參數指定 specs/plans/004-ranking/plan.md
```

### Good Example

這個範例帶入 plan.md 所在的資料夾與 api-plan 的名稱，輸出會含 api-plan 自己的輸入差異。

```bash
uv run "D:/plugins/spec-driven-bdd/skills/plan-package/scripts/plan_state.py" check specs --plan 004-ranking --owner api-plan
```

### Bad Example

這個範例沒有帶 `--plan` 與 `--owner`，結果只確認了「有一個進行中的 plan」，api-plan 拿不到自己的輸入差異，無法依差異逐項判斷，只能重跑完整流程。

```bash
uv run "D:/plugins/spec-driven-bdd/skills/plan-package/scripts/plan_state.py" check specs
```

