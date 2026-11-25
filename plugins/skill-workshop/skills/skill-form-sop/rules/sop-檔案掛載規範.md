# SOP 檔案掛載規範

## Rule 1 -- 檔案只在使用的 step 點名

**強度：MUST**

掛載的檔案（如規則檔、參考文件、模板、腳本、其他 skill）連結只能出現在真正使用它的 step。同一份檔案預設只點名一次；只有驗證 step 需要對照原文，或 `DELEGATE` step 需要交給不共享 context 的 subagent 時，才可再次點名。不得單獨開一個只讀檔案的 step，也不得在用不到它的 step 提前列出連結。

### Good Example

這個範例在撰寫 step 點名檔案，並在需要對照原文的驗證 step 再次點名。

```markdown
### Phase 2 --- 撰寫 SOP

1. WRITE 依 [SOP 格式規範](rules/sop-格式規範.md) 撰寫重點步驟。

### Phase 3 --- 精簡檢查

1. THINK 依 [SOP 格式規範](rules/sop-格式規範.md) 確認每個 Step 符合規範。
```

### Bad Example

這個範例單獨開一個只讀檔案的 step，又在非驗證、非委派的 step 重複點名同一份檔案，多出沒有產出的 step，重複連結也讓 agent 誤以為每一步都要重新讀檔。

```markdown
### Phase 2 --- 撰寫 SOP

1. READ 讀取 [SOP 格式規範](rules/sop-格式規範.md)。
2. WRITE 依 [SOP 格式規範](rules/sop-格式規範.md) 撰寫重點步驟。
3. WRITE 依 [SOP 格式規範](rules/sop-格式規範.md) 調整 Phase 標題。
```

## Rule 2 -- 掛載連結必須使用固定格式

**強度：MUST**

Step 掛載檔案時，連結緊接在標準動詞之後，格式固定為 `<ACTION> 依 [<連結文字>](<相對路徑>) <具體行為>`。連結文字依 Rule 3 決定。路徑使用相對於 SKILL.md 的相對路徑；委派其他 plugin 的 skill 時改依 Rule 4。同一 Step 掛載多份檔案時以「與」連接。

### Good Example

這個範例的連結緊接動詞、使用相對路徑，多份檔案以「與」連接。

```markdown
1. WRITE 依 [RuleFile 格式規範](rules/rule-file-格式規範.md) 與 [Rule 執行強度規範](rules/rule-file-執行強度規範.md) 撰寫每條 Rule。
```

### Bad Example

這個範例把連結附在句尾且使用絕對路徑，agent 讀到動詞時還不知道要依據哪份檔案，skill 搬移位置後連結也會失效。

```markdown
1. WRITE 撰寫每條 Rule（參考 [RuleFile 格式規範](d:/skills/skill-form-rule/rules/rule-file-格式規範.md)）。
```

## Rule 3 -- 連結文字依檔案類型決定

**強度：MUST**

連結文字依掛載對象決定：`templates/` 底下的樣板檔（骨架與範例）一律使用檔名；其他 skill 使用 skill 名稱；其餘檔案使用其 H1 標題，沒有 H1 標題時使用檔名。樣板檔的 H1 可能是填位符號或範例內容，不得作為連結文字。以下 Example 皆對照這些掛載對象：

```text
rules/需求規格撰寫規範.md          H1：# 需求規格撰寫規範
rules/glossary.md                  無 H1
templates/需求規格書.md            H1：# {{feature_name}} 需求規格書
templates/需求規格書.example.md    H1：# 會員登入 需求規格書
../skill-review-spec/SKILL.md      skill 名稱：skill-review-spec
```

### Good Example

這個範例的 RuleFile 使用 H1 標題，沒有 H1 的檔案與樣板骨架、範例使用檔名，其他 skill 使用 skill 名稱。

```markdown
1. WRITE 依 [需求規格撰寫規範](rules/需求規格撰寫規範.md) 與 [glossary.md](rules/glossary.md) 與 [需求規格書.md](templates/需求規格書.md) 與 [需求規格書.example.md](templates/需求規格書.example.md) 產出需求規格書。
2. DELEGATE 依 [skill-review-spec](../skill-review-spec/SKILL.md) 審查需求規格書。
```

### Bad Example

這個範例把樣板骨架的 H1（含填位符號）與範例的 H1（範例內容）當成連結文字，範例換成別的情境後連結文字就與內容不符，`{{feature_name}}` 也會被誤認為待替換的填位符號。

```markdown
1. WRITE 依 [{{feature_name}} 需求規格書](templates/需求規格書.md) 與 [會員登入 需求規格書](templates/需求規格書.example.md) 產出需求規格書。
```

## Rule 4 -- 跨 plugin 的 skill 以名稱委派

**強度：MUST**

委派的 skill 位於其他 plugin 時，不得使用連結，格式固定為 ``DELEGATE 使用 <skill 名稱> skill（可由 <plugin 名稱> plugin 提供，或為與本 skill 資料夾同層的 `<skill 名稱>` 資料夾）<具體行為>，兩者都沒有時不得自行代替，停止並請使用者安裝 <plugin 名稱> plugin，agent 不支援 plugin 時改為把 `<skill 名稱>` 資料夾複製到同層。``。各 plugin 分開安裝，相對路徑到不了其他 plugin；skill 也可能不經 plugin、直接複製到不支援 plugin 的 agent，因此不得把被委派的 skill 限定為 plugin 版本。以下 Example 中，`clarify` 屬於 requirement-clarify plugin，呼叫者屬於 skill-workshop plugin。

### Good Example

這個範例以 skill 名稱委派，寫出 plugin 與同層資料夾兩種來源，並寫出兩者都沒有時的處理。

```markdown
1. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）釐清客製化需求，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。
```

### Bad Example

這個範例的第 1 句以相對路徑連到其他 plugin 的 skill，安裝後該路徑不存在，agent 讀不到 clarify 的 SOP；第 2 句把 clarify 限定為 plugin 版本，skill 複製到沒有 plugin 的環境時，agent 即使看到同層的 clarify 也會拒絕使用而停止。

```markdown
1. DELEGATE 依 [clarify](../clarify/SKILL.md) 釐清客製化需求。
2. DELEGATE 使用 requirement-clarify plugin 的 clarify skill 釐清客製化需求，無法使用時不得自行代替，停止並請使用者安裝 requirement-clarify。
```
