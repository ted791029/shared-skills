# 樣板骨架規範

## Rule 1 -- 骨架檔名必須使用固定格式

**強度：MUST**

骨架路徑固定為 `templates/<樣板名稱>.<副檔名>`。樣板名稱使用描述產出物的短語，英文使用 kebab-case，也可使用中文；副檔名必須是產出檔案的實際格式。檔名不得加上 `template`、`skeleton` 等描述檔案角色的字樣。

### Good Example

這個範例以產出物命名，副檔名即產出格式。

```text
templates/sop.md
templates/需求規格書.md
```

### Bad Example

這個範例的名稱無法看出產出物、加上角色字樣，且副檔名不是產出格式，AI 無法從檔名判斷要產出什麼，編輯器與渲染工具也無法辨識內容格式。

```text
templates/template1.txt
templates/sop-skeleton.md
templates/sop.txt
```

## Rule 2 -- 填位符號必須使用 `{{snake_case}}`

**強度：MUST**

所有填位符號格式固定為 `{{snake_case}}`：雙大括號內使用小寫英文與底線，不加空白。同一骨架不得混用 `<name>`、`[name]`、`${name}` 等其他格式。

### Good Example

這個範例統一使用 `{{snake_case}}`。

```markdown
### Phase {{phase_number}} --- {{phase_name}}

{{step_number}}. {{action_verb}} {{step_behavior}}
```

### Bad Example

這個範例混用多種格式，AI 無法確定哪些文字要替換，且 `<phase_name>` 會被 Markdown 當成 HTML 標籤而在渲染時消失。

```markdown
### Phase [phase_number] --- <phase_name>

${step_number}. {{ Action Verb }} {{step_behavior}}
```

## Rule 3 -- 填位符號名稱必須表達填入內容

**強度：MUST**

填位符號名稱必須讓 AI 不看範例也能判斷要填入什麼，使用描述內容的名詞短語。不得使用 `x`、`value1`、`content` 等無法區分用途的名稱。

### Good Example

這個範例的名稱直接說明要填入的內容。

```markdown
## 驗收條件

- {{acceptance_criterion}}

## 風險

- {{risk_description}}
```

### Bad Example

這個範例的名稱無法區分各欄位要填什麼，AI 必須依賴範例猜測，容易填錯欄位。

```markdown
## 驗收條件

- {{item1}}

## 風險

- {{content}}
```

## Rule 4 -- 固定內容必須直接寫死

**強度：MUST**

每次產出都相同的內容（如語法關鍵字、章節標題、固定欄位名）必須直接寫在骨架中，不得挖成填位符號。只有會隨情境改變的內容才使用填位符號。

### Good Example

這個範例保留固定的 `## SOP` 標題、`Phase` 字樣與 `---` 分隔符，只對 Phase 編號與名稱填位。

```markdown
## SOP

### Phase {{phase_number}} --- {{phase_name}}
```

### Bad Example

這個範例把固定的標題與分隔符也挖成填位符號，AI 可能填入不一致的標題或分隔符。

```markdown
## {{section_title}}

### {{phase_label}} {{phase_number}} {{separator}} {{phase_name}}
```

## Rule 5 -- 重複區塊必須以註解標示

**強度：MUST**

可重複出現的區塊在骨架中只保留一份，並在區塊前後使用產出格式本身的註解語法標示重複範圍與重複依據，例如 Markdown 用 `<!-- -->`、Python 用 `#`。產出格式不支援註解時（如 JSON），不加標示，改由範例呈現多個實例。

### Good Example

這個範例在 Markdown 骨架用 `<!-- -->` 註解標示重複範圍與依據；JSON 不支援註解，因此只保留一份元素、不加標示。

```markdown
### Phase {{phase_number}} --- {{phase_name}}

<!-- 重複開始：每個 Step 一行 -->
{{step_number}}. {{action_verb}} {{step_behavior}}
<!-- 重複結束 -->
```

```json
{
  "endpoints": [
    { "method": "{{http_method}}", "path": "{{endpoint_path}}" }
  ]
}
```

### Bad Example

這個範例複製多份相同區塊，AI 無法判斷應產出幾份。

```markdown
### Phase {{phase_number}} --- {{phase_name}}

1. {{action_verb_1}} {{step_behavior_1}}
2. {{action_verb_2}} {{step_behavior_2}}
3. {{action_verb_3}} {{step_behavior_3}}
```
