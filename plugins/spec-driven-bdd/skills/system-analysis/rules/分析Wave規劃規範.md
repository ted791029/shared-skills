# 分析 Wave 規劃規範

## Rule 1 -- Wave 必須由外而內排序

**強度：MUST**

最接近使用者的端點必須排在 Wave 1，越內層的端點排在越後面的 Wave。內層端點的介面由外層端點的需要與介面盤點分配給它的需求推導，因此外層端點是內層端點的前置依賴。

### Good Example

這個範例從使用者直接操作的前端開始，依序往內到後端與資料保存。

```markdown
**Wave 1 — 前端（UI-01～UI-04）**
**Wave 2 — 後端（API-01～API-03）**
**Wave 3 — 資料庫端（DB-01～DB-02）、檔案系統端（FS-01～FS-02）**
```

### Bad Example

這個範例先分析資料庫，資料表欄位在畫面需求確定前就被定下，前端分析時只能遷就既有欄位，容易出現畫面需要卻沒有的資料。

```markdown
**Wave 1 — 資料庫端（DB-01～DB-02）**
**Wave 2 — 後端（API-01～API-03）**
**Wave 3 — 前端（UI-01～UI-04）**
```

## Rule 2 -- 端點必須排在所有前置端點之後

**強度：MUST**

每個端點的 Wave 編號必須大於所有使用它的端點的 Wave 編號；彼此沒有使用關係且前置端點都已分析的端點，必須放在同一個 Wave。Wave 之間不得有循環依賴。以下 Example 皆對照此使用關係：

```text
使用者 → 前端 → 後端 → 資料庫端
               後端 → 檔案系統端
```

### Good Example

這個範例讓資料庫端與檔案系統端都排在後端之後，且因彼此沒有使用關係而放在同一個 Wave。

```markdown
**Wave 2 — 後端（API-01～API-03）**
**Wave 3 — 資料庫端（DB-01～DB-02）、檔案系統端（FS-01～FS-02）**
```

### Bad Example

這個範例把彼此無關的資料庫端與檔案系統端拆成兩個 Wave，檔案系統端要多等一輪，整體分析時間無故拉長。

```markdown
**Wave 3 — 資料庫端（DB-01～DB-02）**
**Wave 4 — 檔案系統端（FS-01～FS-02）**
```

## Rule 3 -- 委派以端點為單位

**強度：MUST**

每個 Wave 必須為其中每個端點各開一個 sub-agent，並以端點名稱寫出各 sub-agent 分析的端點；同一個 Wave 的 sub-agent 並行。不得以單一介面為單位開 sub-agent，也不得讓一個 sub-agent 負責多個端點。委派不得寫出介面文檔的檔名或格式，產出由負責該端點的 Planner 決定。

### Good Example

這個範例的 Wave 3 有兩個端點，開兩個 sub-agent，只寫出各自分析的端點。

```markdown
- 委派：開 2 個 sub-agent，分別分析資料庫端、檔案系統端。
```

### Bad Example

這個範例在委派寫出介面文檔檔名，plan.md 替 Planner 決定了產出，Planner 若採用其他格式（如 DBML），plan.md 與 Planner 會對同一份產物各有一套定義而互相矛盾。

```markdown
- 委派：開 2 個 sub-agent，委派子 skill 撰寫 `data-model.md`、`contracts/storage-contract.md`。
```

## Rule 4 -- 分析重點只寫要回答的問題

**強度：MUST**

分析重點必須寫出該 Wave 的 sub-agent 要回答哪些問題，包含必須涵蓋的面向與要向內層傳遞的需要；不得寫出分析結果，如具體欄位、API 路徑或畫面配置。

### Good Example

這個範例只列出後端要分析的面向，沒有替 sub-agent 決定 API 的設計。

```markdown
- 分析重點：滿足 Wave 1 各畫面需要的端點、請求與回應格式、分頁與錯誤回應，以及每個端點需要讀寫哪些資料與檔案。
```

### Bad Example

這個範例直接寫出 API 路徑與欄位，plan.md 越界做了系統分析，sub-agent 會被未經分析的設計綁住。

```markdown
- 分析重點：`GET /api/albums?page=1` 回傳 `{ id, name, coverUrl, photoCount }`，`PUT /api/albums/order` 接收相簿 ID 陣列。
```

## Rule 5 -- 相依只列前置 Wave 端點的產出

**強度：MUST**

相依必須寫成「Wave N <端點>的產出」，只列出使用到的前置 Wave 端點，多項以「、」分隔；Wave 1 沒有前置 Wave，寫「無」。不得寫出介面文檔檔名，不得列入每個 Wave 都讀取的共用輸入，也不得寫相依理由。

### Good Example

這個範例只列出前置 Wave 的端點，實際文檔由負責該端點的 Planner 決定。

```markdown
- 相依：Wave 2 後端的產出
```

### Bad Example

這個範例寫出文檔檔名並混入共用輸入，檔名與 Planner 的實際產出可能不一致，共用輸入也讓 Wave 之間交接了什麼變得不清楚。

```markdown
- 相依：Wave 2 的 `contracts/openapi.yaml`、`spec.md`、`techstack.md`
```
