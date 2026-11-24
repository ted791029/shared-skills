# Rule 執行強度規範

## Rule 1 -- 強度等級只能使用允許清單

**強度：MUST**

強度標示中的等級只能使用 `MUST`、`SHOULD` 或 `MAY`，不得使用其他字詞或自訂等級。

### Good Example

這個範例的強度等級屬於允許清單。

```markdown
## Rule 1 -- Rule 必須聚焦單一規範

**強度：MUST**

每條 Rule 只能描述一個明確要求。
```

### Bad Example

這個範例使用未定義的強度等級「高」，agent 無法對應到 MUST、SHOULD、MAY 的處理方式，也無法判斷違反時是否必須修正。

```markdown
## Rule 1 -- Rule 必須聚焦單一規範

**強度：高**

每條 Rule 只能描述一個明確要求。
```

## Rule 2 -- MUST 表示必須遵守

**強度：MUST**

`MUST` 用於不可省略的規範。當 Rule 標示為 `MUST` 時，agent 發現違反情況應直接修正，除非使用者明確要求保留。

### Good Example

這個範例把結構性要求標為 `MUST`，表示所有 Rule 都必須遵守。

```markdown
## Rule 4 -- Example 必須成對出現

**強度：MUST**

每條 Rule 都必須包含 `### Good Example` 與 `### Bad Example`。
```

### Bad Example

這個範例把必要結構標為可選，會讓 agent 誤以為可以省略。

```markdown
## Rule 4 -- Example 必須成對出現

**強度：MAY**

每條 Rule 都必須包含 `### Good Example` 與 `### Bad Example`。
```

## Rule 3 -- SHOULD 表示預設遵守

**強度：MUST**

`SHOULD` 用於建議遵守但允許例外的規範。只有當使用者需求、上下文限制或更高強度 Rule 衝突時，agent 才可偏離。

### Good Example

這個範例把精簡要求標為 `SHOULD`，並給出明確的預設行為，agent 只有在使用者要求保留背景等例外情況下才偏離。

```markdown
## Rule 5 -- RuleFile 必須保持精簡

**強度：SHOULD**

RuleFile 應刪除不影響執行的背景說明。
```

### Bad Example

這個範例沒有預設行為，只寫「看情況調整」，agent 任何時候都能偏離，`SHOULD` 實際上變成 `MAY`。

```markdown
## Rule 5 -- RuleFile 必須保持精簡

**強度：SHOULD**

RuleFile 可以看情況調整。
```

## Rule 4 -- MAY 表示可選建議

**強度：MUST**

`MAY` 用於補充性建議。agent 可以在有助於一致性、可讀性或使用者目標時採用，但不得把 `MAY` 規則當成必要條件。

### Good Example

這個範例把非必要的輔助格式標為 `MAY`，避免過度約束。

```markdown
## Rule 6 -- 複雜規則可補充判斷標準

**強度：MAY**

複雜規則可使用 Markdown table 補充判斷標準。
```

### Bad Example

這個範例用 `MAY` 描述必要要求，agent 會把固定的標題格式當成可選而略過，Rule 之後無法依編號引用。

```markdown
## Rule 2 -- Rule 標題必須使用固定格式

**強度：MAY**

Rule 標題格式固定為 `## Rule N -- <規範名稱>`。
```
