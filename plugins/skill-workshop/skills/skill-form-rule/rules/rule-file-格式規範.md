# RuleFile 格式規範

## Rule 1 -- Rule 必須聚焦單一規範

**強度：MUST**

每條 Rule 只能描述一個明確要求，讓 agent 可以直接判斷該規範是否被遵守。描述中的多項要求若各有不同目的、可以單獨被違反，就必須拆成不同 Rule；同一格式的組成細節屬於同一要求。

### Good Example

這個範例只規範範例結構對應骨架，違反與否只有一個判斷點。

```markdown
## Rule 2 -- 範例結構必須與骨架一一對應

**強度：MUST**

範例必須保留骨架的所有區塊、順序與固定內容，只把填位符號替換為實際內容。
```

### Bad Example

這個範例把結構對應與重複展開兩個不同目的的要求寫在同一條，結構正確但只展開一個實例時，agent 無法判斷這條 Rule 算不算被遵守。

```markdown
## Rule 2 -- 範例結構必須與骨架一一對應

**強度：MUST**

範例必須保留骨架的所有區塊、順序與固定內容，且重複區塊至少展開兩個實例。
```

## Rule 2 -- Rule 編號連續且名稱為短語

**強度：MUST**

Rule 標題中的 `N` 使用連續數字，依 Rule 出現順序從 1 遞增；規範名稱使用短語，不寫完整句子。

### Good Example

這個範例的編號從 1 連續遞增，規範名稱都是短語。

```markdown
## Rule 1 -- Rule 必須聚焦單一規範

## Rule 2 -- 規範描述必須可判斷
```

### Bad Example

這個範例的編號跳過 2，第二條名稱寫成完整句子，agent 依編號引用時找不到 Rule 2，冗長名稱也難以快速辨識規範重點。

```markdown
## Rule 1 -- Rule 必須聚焦單一規範

## Rule 3 -- 每條 Rule 的描述都必須寫得讓 agent 能判斷內容是否符合規範。
```

## Rule 3 -- 規範描述必須可判斷

**強度：MUST**

Rule 描述必須說明具體要求、限制或避免事項。描述應讓 agent 能判斷內容是否符合規範，不寫抽象口號、背景長文或無法驗證的形容詞。

### Good Example

這個範例用具體長度與句型限制定義 Rule 名稱，agent 可以直接判斷是否遵守。

```markdown
Rule 名稱必須使用 12 個字以內的短語，不使用問句或完整句子。
```

### Bad Example

這個範例只表達方向，沒有提供可檢查的要求，agent 無法判斷名稱是否符合規範。

```markdown
Rule 名稱要清楚自然，讓人一看就覺得好理解。
```

## Rule 4 -- Example 說明句必須寫出判斷依據

**強度：MUST**

Good Example 的說明句必須寫出符合了 Rule 的哪項要求；Bad Example 的說明句必須寫出違反了什麼，以及違反造成的後果。不得只描述範例內容或與 Good 的差異。

### Good Example

這個範例的 Good 說明句寫出符合的要求，Bad 說明句寫出違反的要求與造成的後果。

```markdown
### Good Example

這個範例保留骨架的所有段落，只替換填位符號。

### Bad Example

這個範例新增骨架沒有的「備註」段，AI 會學到可以自行增加段落，產出開始偏離骨架。
```

### Bad Example

這個範例的 Bad 說明句只描述差異，沒有說明為什麼不好，agent 無法判斷這個差異是否重要。

```markdown
### Good Example

這個範例保留骨架的所有段落，只替換填位符號。

### Bad Example

這個範例新增骨架沒有的「備註」段。
```

## Rule 5 -- Example 必須呈現真實情境的內容

**強度：MUST**

Example 的 code block 必須呈現示範對象在真實 RuleFile 中會出現的形態。示範完整 Rule 時要包含該 Rule 的必填欄位（如 `## Rule N -- <規範名稱>` 標題）；只示範單一欄位時可只呈現該欄位，但不得把一條 Rule 畫成省略必填欄位、真實情況不會出現的殘缺內容。

### Good Example

這個範例要示範一條帶強度的 Rule，呈現真實會出現的完整形態。

```markdown
## Rule 1 -- Rule 必須聚焦單一規範

**強度：MUST**

每條 Rule 只能描述一個明確要求。
```

### Bad Example

這個範例要示範一條 Rule，卻省略真實情況必有的 `## Rule N -- ...` 標題，agent 會誤以為 Rule 可以沒有標題。

```markdown
**強度：MUST**

每條 Rule 只能描述一個明確要求。
```

## Rule 6 -- Example 必須能獨立判讀

**強度：MUST**

Rule 規範的是兩者之間的關係時（如範例對骨架），必須在描述最後附上比對基準，Example 一律對照該基準。比對基準是同一個 skill 的 `rules/baselines/` 底下的基準檔時，描述以相對連結指明基準檔，並在描述最後只附上 Example 用到的條目，不附整份基準。除基準檔外，不得以跨檔案路徑或其他 Rule 編號引用比對基準。

### Good Example

這個範例的第一條 Rule 在描述最後附上骨架；第二條的比對基準是基準檔，以連結指明並只附上 Example 用到的一個條目。讀者不需離開該條 Rule 就能比對 Example。

````markdown
## Rule 2 -- 範例結構必須與骨架一一對應

**強度：MUST**

範例必須保留骨架的所有區塊、順序與固定內容。以下 Example 皆對照此骨架：

```markdown
# {{feature_name}} 需求規格書

## 背景

{{background}}
```

## Rule 3 -- code 與 message 必須照錯誤代碼表

**強度：MUST**

`code` 必須是[錯誤代碼表](baselines/錯誤代碼表.md)中的一個條目，`message` 必須與該條目的訊息句型逐字相同，只把 `<佔位符>` 換成實際值。以下 Example 皆對照此條目：

| code | HTTP 狀態 | 訊息句型 |
|---|---|---|
| ORDER_CANCELLED | 409 | 訂單 <訂單編號> 已取消，無法再修改 |
````

### Bad Example

這個範例的第一條沒有附上骨架，只引用其他檔案的 Rule 編號，agent 無法比對範例是否真的與骨架一致；第二條只連結基準檔、沒有附上 Example 用到的條目，讀者必須另外打開基準檔才能判斷 Example 的訊息是否逐字相同。

````markdown
## Rule 2 -- 範例結構必須與骨架一一對應

**強度：MUST**

範例必須保留骨架的所有區塊、順序與固定內容。

### Good Example

這個範例對應骨架規範 Rule 5 的 SOP 骨架，結構完全一致。

```markdown
## SOP

### Phase 1 --- 判斷需求

1. READ 讀取使用者需求與目標 skill。
```

## Rule 3 -- code 與 message 必須照錯誤代碼表

**強度：MUST**

`code` 必須是[錯誤代碼表](baselines/錯誤代碼表.md)中的一個條目，`message` 必須與該條目的訊息句型逐字相同，只把 `<佔位符>` 換成實際值。

### Good Example

這個範例的 `message` 與 ORDER_CANCELLED 的訊息句型逐字相同。

```text
{ "code": "ORDER_CANCELLED", "message": "訂單 20261011-001 已取消，無法再修改" }
```
````

## Rule 7 -- Example 必須針對該條 Rule

**強度：MUST**

Good Example 必須示範該條 Rule 描述中的每項要求，不得使用與其他 Rule 共用、看不出本條重點的通用範例。Bad Example 只能違反該條 Rule，且不需外部資訊就能看出違反之處。

### Good Example

這個範例示範「Rule 必須標示執行強度」，Bad Example 只缺少強度標示，其餘欄位皆正確。

````markdown
### Bad Example

這個範例缺少強度標示，agent 無法判斷違反時是否必須修正。

```markdown
## Rule 1 -- Rule 必須聚焦單一規範

每條 Rule 只能描述一個明確要求。
```
````

### Bad Example

這個範例同樣示範「Rule 必須標示執行強度」，Bad Example 卻保留強度、改錯標題格式，違反的是別條 Rule，agent 學不到本條的違反樣貌。

````markdown
### Bad Example

這個範例的標題不符固定格式，agent 無法辨識這是一條 Rule。

```markdown
## 單一規範

**強度：MUST**

每條 Rule 只能描述一個明確要求。
```
````

## Rule 8 -- 其他 plugin 的 skill 以名稱提及

**強度：MUST**

RuleFile 的內文提到其他 plugin 的 skill 時，不得使用連結或 `/<plugin 名稱>:<skill 名稱>` 指令前綴，格式固定為 ``<skill 名稱> skill（可由 <plugin 名稱> plugin 提供，或為與本 skill 資料夾同層的 `<skill 名稱>` 資料夾）``，只是建議使用者改用該 skill 時，不加缺少該 skill 時的處理。各 plugin 分開安裝，相對路徑到不了其他 plugin；skill 也可能直接複製到不支援 plugin 的 agent，那裡沒有指令前綴。同一個 plugin 內的 skill 照常使用相對連結。以下 Example 中，`skill-engineering` 屬於 skill-workshop plugin，RuleFile 所屬的 skill 與 `plan-package` 屬於 spec-driven-bdd plugin。

### Good Example

這個範例的第 1 句以 skill 名稱提及其他 plugin 的 skill，括號寫出 plugin 與同層資料夾兩種來源，只是建議使用者改用，因此沒有缺少時的處理；第 2 句提到同一個 plugin 的 skill，照常使用相對連結。

```markdown
Planner 的產出不符其樣板時，必須停止並建議使用者以 skill-engineering skill（可由 skill-workshop plugin 提供，或為與本 skill 資料夾同層的 `skill-engineering` 資料夾）優化該 Planner。
回報前必須依 [plan-package](../../plan-package/SKILL.md) 確認目標是進行中的 plan。
```

### Bad Example

這個範例的第 1 句以相對路徑連到其他 plugin 的 skill，plugin 安裝後該路徑不存在；第 2 句使用指令前綴，skill 複製到不支援 plugin 的 agent 時沒有這個指令，使用者照做會找不到 skill；第 3 句只是建議卻加上安裝提示，agent 會誤以為缺少 skill-engineering 時必須停止流程。

```markdown
Planner 的產出不符其樣板時，必須停止並建議使用者以 [skill-engineering](../../../../skill-workshop/skills/skill-engineering/SKILL.md) 優化該 Planner。
Planner 的產出不符其樣板時，必須停止並建議使用者以 `/skill-workshop:skill-engineering` 優化該 Planner。
Planner 的產出不符其樣板時，必須停止並建議使用者以 skill-engineering skill（可由 skill-workshop plugin 提供，或為與本 skill 資料夾同層的 `skill-engineering` 資料夾）優化該 Planner，兩者都沒有時不得自行代替，停止並請使用者安裝 skill-workshop plugin。
```
