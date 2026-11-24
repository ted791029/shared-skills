# SOP 格式規範

## Rule 1 -- SOP 只規範 `## SOP` 區塊

**強度：MUST**

撰寫 SOP 時只建立 `## SOP` 區塊，不為目標 skill 新增範例、模板、格式說明或其他非 SOP 章節，除非使用者明確要求。

### Good Example

這個範例只輸出 SOP 區塊，責任單一。

```markdown
## SOP

### Phase 1 --- 判斷需求

1. READ 讀取使用者需求。
```

### Bad Example

這個範例在 SOP 之外新增使用者未要求的章節，SKILL.md 混入非 SOP 內容，增加 context 成本，並與 `rules/`、`templates/` 的職責重疊。

```markdown
## SOP

### Phase 1 --- 判斷需求

1. READ 讀取使用者需求。

## 範例輸出

## 常見問題
```

## Rule 2 -- Phase 編號必須連續遞增

**強度：MUST**

Phase 編號從 1 開始，依 Phase 出現順序連續遞增，不得跳號或重複。

### Good Example

這個範例的 Phase 編號從 1 開始連續遞增。

```markdown
### Phase 1 --- 判斷需求

### Phase 2 --- 撰寫內容
```

### Bad Example

這個範例的 Phase 編號從 1 跳到 3，agent 依編號引用 Phase 2 時找不到對應階段，也會誤以為中間有缺漏的 Phase。

```markdown
### Phase 1 --- 判斷需求

### Phase 3 --- 撰寫內容
```



## Rule 3 -- Phase 數量原則上控制在 3 至 5 個

**強度：SHOULD**

SOP 原則上使用 3 至 5 個 Phase；流程可以少於 3 個 Phase 完成時，不必為符合數量而新增無必要的 Phase。

### Good Example

這個範例用 3 個 Phase 涵蓋完整流程。

```markdown
### Phase 1 --- 判斷需求
### Phase 2 --- 撰寫內容
### Phase 3 --- 精簡檢查
```



### Bad Example

這個範例把流程拆成 6 個零碎 Phase，每個 Phase 只剩單一動作，Phase 失去分段意義，閱讀與維護成本增加。

```markdown
### Phase 1 --- 開啟檔案
### Phase 2 --- 讀取需求
### Phase 3 --- 思考
### Phase 4 --- 撰寫
### Phase 5 --- 再讀一次
### Phase 6 --- 存檔
```



## Rule 4 -- 過多 Phase 應考慮拆分 skill

**強度：SHOULD**

若 SOP 經過合併與壓縮後仍需要超過 5 個 Phase，應判斷是否包含不同使用者意圖、不同產出物或可重用流程；若是，應建議抽成另一個 skill，而不是繼續擴充同一個 SOP。

### Good Example

這個範例在壓縮後仍包含不同產出物，因此建議拆分 skill。

```markdown
原 SOP 壓縮後仍包含：

### Phase 1 --- 判斷需求
### Phase 2 --- 撰寫 SOP
### Phase 3 --- 撰寫 RuleFile
### Phase 4 --- 產生測試案例
### Phase 5 --- 執行測試
### Phase 6 --- 整理審查報告

建議拆分：

- `skill-form-sop`：負責撰寫與精簡 SOP。
- `skill-form-rule`：負責撰寫 RuleFile。
- `skill-test-case`：負責產生測試案例與整理測試結果。
```

### Bad Example

這個範例的 Phase 只是拆得太細、合併後不超過 5 個，卻未先合併就建議拆 skill，會把單一意圖的流程切散到多個 skill，增加呼叫與維護成本。

```markdown
原 SOP：

### Phase 1 --- 開啟檔案
### Phase 2 --- 讀取需求
### Phase 3 --- 思考需求
### Phase 4 --- 撰寫 SOP
### Phase 5 --- 檢查 SOP
### Phase 6 --- 刪除多餘內容

建議拆分：

- `skill-read-requirement`：負責開啟檔案、讀取與思考需求。
- `skill-write-sop`：負責撰寫、檢查與精簡 SOP。
```



## Rule 5 -- Phase 順序必須呈現自然流程

**強度：SHOULD**

Phase 順序依理解、設計、撰寫、驗證的自然流程排列，不把後段責任排在前段之前。

### Good Example

這個範例先理解需求再撰寫與檢查。

```markdown
### Phase 1 --- 判斷需求
### Phase 2 --- 撰寫內容
### Phase 3 --- 精簡檢查
```



### Bad Example

這個範例先撰寫再回頭理解需求，撰寫時缺少需求依據，產出常需要重寫。

```markdown
### Phase 1 --- 撰寫內容
### Phase 2 --- 判斷需求
```



## Rule 6 -- Step 動詞限定為標準動詞

**強度：MUST**

Step 開頭的動詞限定為 `READ`、`THINK`、`ASK`、`WRITE`、`DELEGATE`；動詞後的具體行為避免「處理」、「優化」、「完善」等不明確動詞。

### Good Example

這個範例使用標準動詞，行為具體。

```markdown
1. READ 讀取使用者需求與目標檔案。
2. WRITE 撰寫每條 Rule。
```



### Bad Example

這個範例使用清單外的 `CHECK`，agent 無法依動詞判斷 step 類型；「處理好」也沒有可判斷的完成條件。

```markdown
1. CHECK 檢查需求。
2. WRITE 把內容處理好。
```



## Rule 7 -- 每個 Step 只放一個動作

**強度：MUST**

每個 Step 只能包含一個標準動詞，並且只產生一份產出；`DELEGATE` 一次只委派一個 skill。以「並」、「然後」、「再」、「與」、頓號或多個子句連接的對象，若各自產生不同產出或改動不同檔案，即為多個動作，必須拆成不同 Step；這些對象若只是同一動作的輸入或參考檔，則不必拆分。不得以抽象名詞（如「部件」、「相關內容」）概括多個動作。

### Good Example

這個範例讓每個 Step 只產生一份產出：第 1 步的兩個對象都是讀取的輸入，維持一步；刪除檔案與刪除連結改動不同檔案，拆成兩步；兩個 skill 各自委派一步。

```markdown
1. READ 讀取使用者需求與目標 skill。
2. WRITE 刪除判定不存留的部件。
3. WRITE 刪除所有 skill 中指向已刪除部件的掛載連結。
4. DELEGATE 依 [skill-derive-script](../skill-derive-script/SKILL.md) 為指派的 Step 抽出腳本。
5. DELEGATE 依 [skill-derive-rule](../skill-derive-rule/SKILL.md) 為指派的 Step 展開規則。
```

### Bad Example

這個範例沒有使用「並」、「然後」、「再」，卻以「部件」概括兩個委派，一個 Step 產出腳本與規則兩份產出，agent 容易只委派第一個 skill，也無法逐步驗證各委派的結果。

```markdown
1. DELEGATE 依 [skill-derive-script](../skill-derive-script/SKILL.md) 與 [skill-derive-rule](../skill-derive-rule/SKILL.md) 衍生部件。
```

