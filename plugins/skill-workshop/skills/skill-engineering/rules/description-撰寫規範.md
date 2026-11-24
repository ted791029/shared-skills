# description 撰寫規範

## Rule 1 -- description 必須寫出觸發情境

**強度：MUST**

description 必須以使用者的需求或情境寫出何時使用此 skill（如「……時使用此 skill」），不得只描述 skill 的功能或內部流程。

### Good Example

這個範例以使用者會遇到的情境開頭，agent 能從使用者需求直接對應到此 skill。

```yaml
description: 撰寫、新增或修改任何 skill 的 `rules/` 底下時，必須使用此 skill；即使同時在使用其他 skill 也適用。
```

### Bad Example

這個範例只描述 skill 的內容，沒有寫出何時使用，agent 無法從使用者需求對應到此 skill，該觸發時不會觸發。

```yaml
description: 包含 RuleFile 格式規範與執行強度規範的 RuleFile 撰寫工具。
```

## Rule 2 -- description 必須寫出與相近 skill 的分界

**強度：MUST**

有觸發情境相近的既有 skill 時，description 必須寫出本 skill 不涵蓋的情境與負責該情境的 skill。

### Good Example

這個範例寫出 `## SOP` 區塊不在範圍內，並指出由 skill-form-sop 負責。

```yaml
description: 撰寫或修改 SKILL.md frontmatter 的 name 與 description 時使用此 skill；`## SOP` 區塊的撰寫交由 skill-form-sop。
```

### Bad Example

這個範例只寫「撰寫 SKILL.md 時」，與 skill-form-sop 的觸發情境重疊卻沒寫分界，兩個 skill 會同時被觸發並各自修改 SKILL.md。

```yaml
description: 撰寫或修改 SKILL.md 時使用此 skill。
```

## Rule 3 -- name 必須與資料夾名稱一致

**強度：MUST**

name 必須使用小寫英文與連字號，且與 skill 資料夾名稱完全相同。以下 Example 皆對照此資料夾：

```text
.claude/skills/skill-form-rule/SKILL.md
```

### Good Example

這個範例的 name 與資料夾名稱完全相同，且只使用小寫英文與連字號。

```yaml
name: skill-form-rule
```

### Bad Example

這個範例的 name 使用大寫駝峰，與資料夾名稱不一致，使用者以名稱呼叫或其他 skill 以名稱委派時對不上。

```yaml
name: SkillFormRule
```

## Rule 4 -- description 只寫觸發情境與分界

**強度：MUST**

description 只寫 agent 不讀 SOP 就能決定要不要呼叫此 skill 所需的資訊：觸發情境（使用者的需求、呼叫的入口、會委派它的 skill）與分界。分界每項寫一句「<情境>交由 <skill>」，不帶判定條件，也不寫中途轉交的對象。不得寫 SOP 的步驟、判定條件、例外處理、腳本與產出檔的行為；這些由 SOP、rules、scripts 承載，修改 skill 的行為時只改它們，不在 description 追加說明。以下 Example 皆對照此 skill：

```text
bdd：依範疇執行紅燈、綠燈、重構、重跑與全端點驗證；feature 與 dsl.md 由 dsl-refine 產出，逐任務執行由 implement 負責
```

### Good Example

這個範例只寫何時使用與四項分界，agent 從使用者的需求或委派就能判斷要不要呼叫。

```yaml
description: 使用者已有 dsl-refine 產出的端點 feature 與 dsl.md，要對指定範疇執行 BDD 的紅燈、綠燈或重構其中一個階段，或句型只改說明、要確認既有 step 不用改並重新執行範疇，或要執行所有端點的測試確認有沒有回歸，或呼叫 /bdd red、/bdd green、/bdd refactor、/bdd rerun、/bdd verify，或 implement 委派這些任務時使用此 skill。feature、dsl.md 與用語表的產生與修正交由 dsl-refine，介面文檔的錯誤與規格沒寫的行為交由 dev-finding，依 tasks.md 逐任務執行交由 implement，任務的拆解交由 task。
```

### Bad Example

這個範例在觸發情境之後寫進各階段的做法、結果檔的沿用條件與帶條件的轉交，description 長到兩千字，呼叫時機被流程淹沒；行為改變時還要同時改 description 與 rules，兩處容易不一致。

```yaml
description: 使用者已有 dsl-refine 產出的端點 feature 與 dsl.md，要依指定範疇以 BDD 執行紅燈、綠燈或重構時使用此 skill。red 依 dsl.md 撰寫 step definitions 與 Driver，第一次就通過時破壞產品程式並加標記保留到同範疇的 green；四個階段的基準沿用 `.verify-result.json` 的上次結果，範疇的結果來自最後一次執行且之後沒有改檔時直接沿用；dsl.md 與介面文檔矛盾時先判斷錯在哪一邊，錯在介面文檔時經 dev-finding 交給該文檔的 Planner、不交 dsl-refine。
```
