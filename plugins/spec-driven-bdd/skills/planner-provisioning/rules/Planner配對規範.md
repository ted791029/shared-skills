# Planner 配對規範

## Rule 1 -- Planner 名稱依介面 ID 前綴對照

**強度：MUST**

每個 Wave 的每個端點，必須取該端點在 plan.md 介面盤點的介面 ID 前綴，依下表對照 Planner 名稱，不得依中文端點名稱對照。表中沒有的前綴，Planner 名稱為 `<前綴小寫>-plan`，並必須在配對表後請使用者確認此名稱。不得自訂表外的名稱。

| 介面 ID 前綴 | Planner 名稱 |
|---|---|
| `UI` | `ui-ux-plan` |
| `API` | `api-plan` |
| `DB` | `data-plan` |
| `FS` | `storage-plan` |

### Good Example

這個範例的端點名稱寫成「MySQL 資料庫」，仍依前綴 `DB` 對照為 `data-plan`；表外前綴 `HW` 命名為 `hw-plan` 並請使用者確認。

```markdown
| Wave | 端點 | 介面前綴 | Planner | 狀態 |
|---|---|---|---|---|
| 3 | MySQL 資料庫 | `DB` | `data-plan` | 已有 |
| 3 | 感測裝置 | `HW` | `hw-plan` | 缺少 |

`HW` 不在對照表，Planner 暫定命名為 `hw-plan`，請確認是否採用此名稱。
```

### Bad Example

這個範例依中文端點名稱命名為 `mysql-plan`，與既有的 `data-plan` 對不上，配對為缺少後會重建一個職責相同的 Planner。

```markdown
| Wave | 端點 | 介面前綴 | Planner | 狀態 |
|---|---|---|---|---|
| 3 | MySQL 資料庫 | `DB` | `mysql-plan` | 缺少 |
```

## Rule 2 -- 一種端點類型只對應一個 Planner

**強度：MUST**

不同前綴的端點必須各自對應一個 Planner，不得合併給同一個 Planner；一個端點的全部產出由同一個 Planner 負責。

### Good Example

這個範例的資料庫端與檔案系統端雖在同一個 Wave，仍各自對應一個 Planner。

```markdown
| Wave | 端點 | 介面前綴 | Planner | 狀態 |
|---|---|---|---|---|
| 3 | 資料庫端 | `DB` | `data-plan` | 缺少 |
| 3 | 檔案系統端 | `FS` | `storage-plan` | 缺少 |
```

### Bad Example

這個範例把檔案系統端併給 `data-plan`，一個 Planner 要產出兩個端點結構不同的文檔，樣板得同時涵蓋資料表與目錄結構，Planner 的職責變得模糊。

```markdown
| Wave | 端點 | 介面前綴 | Planner | 狀態 |
|---|---|---|---|---|
| 3 | 資料庫端 | `DB` | `data-plan` | 缺少 |
| 3 | 檔案系統端 | `FS` | `data-plan` | 缺少 |
```

## Rule 3 -- 狀態依名稱與職責判定

**強度：MUST**

每列狀態必須依下表判定，「負責端點」以 skill 的 description 寫明負責的端點類型為準，不比對產出檔名。與 planner-provisioning 同層只有資料夾、沒有 SKILL.md 的不算 skill。

| 狀態 | 判定 | 後續處理 |
|---|---|---|
| 已有 | 有同名 skill，且 description 的負責端點與該列相同 | 直接使用 |
| 疑似已有（`<skill 名稱>`） | 沒有同名 skill，但有其他 skill 的 description 負責同類型端點 | 請使用者決定沿用、改名或另建 |
| 不符 | 有同名 skill，但 description 負責其他類型的端點 | 建議使用者以 skill-engineering skill（可由 skill-workshop plugin 提供，或為與本 skill 資料夾同層的 `skill-engineering` 資料夾）優化，不撰寫委派簡報 |
| 缺少 | 沒有同名 skill，也沒有負責同類型端點的 skill | 撰寫委派簡報 |

### Good Example

這個範例的資料庫端沒有 `data-plan`，但 `db-plan` 的 description 寫明負責資料庫端，標為疑似已有並請使用者決定，不直接重建。

```markdown
| Wave | 端點 | 介面前綴 | Planner | 狀態 |
|---|---|---|---|---|
| 3 | 資料庫端 | `DB` | `data-plan` | 疑似已有（`db-plan`） |

`db-plan` 的 description 寫明負責資料庫端，請決定沿用 `db-plan`、改名為 `data-plan`，或另建 `data-plan`。
```

### Bad Example

這個範例只比對名稱，沒有檢查其他 skill 的職責，`db-plan` 已負責資料庫端仍標為缺少，會重建出兩個職責重複、產出格式各異的 Planner。

```markdown
| Wave | 端點 | 介面前綴 | Planner | 狀態 |
|---|---|---|---|---|
| 3 | 資料庫端 | `DB` | `data-plan` | 缺少 |
```

## Rule 4 -- 前置端點寫進 truth 的產出只讀這次的異動

**強度：MUST**

讀取前置端點的產出時，先從負責的 Planner 的 SKILL.md 找出撰寫產出的 Step 寫明的位置。位置在 plan 資料夾時讀取那些文檔；位置在 `specs/truth/` 時，讀取 plan 的 `truth-changes.md` 中該 Planner 的一節，再讀取每一列對象所在的檔案，已刪除的對象以該列的改動摘要為準。該節還沒有任何紀錄時，表示前置端點尚未執行，必須停止並回報；只有一列「無異動」時，前置端點這次沒有新的產出。不得因為 truth 的檔案存在就把整個資料夾當成這次的產出。以下 Example 皆對照此情境：

```text
data-plan 的相依：Wave 2 後端的產出；api-plan 的 SKILL.md 寫明增修 `specs/truth/contracts/`
truth-changes.md 的 api-plan 一節：
| ADD | `contracts/paths/標籤/api_photos_{photoId}_tags.yaml` | 整份檔案，2 個操作：新增與移除照片的標籤 | FR-021 |
| DEL | `contracts/paths/照片/api_photos_{photoId}_neighbors.yaml` | 刪除取得前後張的操作 | FR-022 |
```

### Good Example

這個範例只讀 api-plan 一節列出的對象：新增的讀檔案內容，刪除的依改動摘要得知操作已移除。

```text
讀取 specs/truth/contracts/paths/標籤/api_photos_{photoId}_tags.yaml → 兩個操作都需要寫入照片的標籤
DEL api_photos_{photoId}_neighbors.yaml → 檔案已不存在，依改動摘要得知取得前後張的操作已移除
```

### Bad Example

這個範例讀完整個 contracts 資料夾，分不出哪些是這次的異動；被刪除的操作已經沒有檔案，資料庫端不會知道只為它存在的索引可以移除。

```text
讀取 specs/truth/contracts/ 的全部檔案 → 依所有操作的 x-inner-needs 重新推導每一張資料表
```
