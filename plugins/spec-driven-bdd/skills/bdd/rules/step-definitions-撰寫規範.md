# Step definitions 撰寫規範

## Rule 1 -- 只為範疇內 undefined 的句型撰寫，沿用前比對語意

**強度：MUST**

只能為範疇內 Example 用到、尚未定義（undefined）的 step 撰寫 step definition，expression 必須與 dsl.md 該句型逐字對應，不得預先為範疇外的 Example 撰寫。已存在且能比對的 step，沿用前必須比對它的實作（呼叫的入口、帶的欄位、保存的值與斷言）與 dsl.md 該句型的測試撰寫語意，非本次撰寫、先前為其他 feature 撰寫或屬於其他端點的 step 尤其不得略過比對：一致時必須直接重用，不得另寫一個相近的版本，只缺 dsl.md 要求的參數值時擴充既有 step；不一致時先依 Rule 15 判定是不是句型的測試寫法改了（是則由 red 改寫），不是時依 Rule 12 判定是擴充還是撞句：撞句不得沿用，也不得改寫它，必須歸為「feature 或 dsl.md 有問題（同一個句子在其他 feature 有不同的意思）」依停下回報規範停下，交由 dsl-refine 換句子。

共用起點預設值表的界線：同一份 Driver 預設值表同時涵蓋多個起點（dsl.md 的同一個句型列出多個起點）時，起點名稱屬範疇外的起點，其預設值可在同一次修改中補進共用預設值表（它是資料，不是行為，依 Rule 14 與 feature 的 `# 預設值：` 註解一致）；但起點的建立步驟（`系統處於` 對應分支如何呼叫入口建立狀態）只能為範疇內用到的起點撰寫，範疇外起點的分支留到輪到它的範疇。

### Good Example

這個範例先比對兩個能比對的既有 step，語意一致才重用與擴充，只為 undefined 的句型新寫 step。

```text
基準 undefined："甲" 送出新答案 "4567"、"甲" 的目前答案為 "4567"
既有：@step('"{玩家}" 猜 "{四碼}"')（backend/tests/api/steps/modules/對戰/猜測.py）→ POST /api/rooms/{roomId}/guesses 帶 guess、保存回應
  backend/dsl.md 同句型：POST /api/rooms/{roomId}/guesses 帶 guess、保存回應 → 一致 → 直接重用
既有：@step('系統處於 "{state}"')（shared/系統狀態.py）→ 依預設值註解建立起點，只接受既有 feature 的起點
  backend/dsl.md 同句型：依預設值註解建立起點 → 一致，只缺「房主輪到且尚未改答案」→ 擴充
新寫：送出新答案、目前答案為
```

### Good Example

這個範例的預設值表同時有兩個起點，範疇只用到「房主輪到且尚未改答案」；表裡補進另一個起點的預設值資料，建立步驟只寫範疇內的起點。

```js
// 預設值來源：specs/truth/features/frontend/改答案.feature 第 12 行 `# 預設值：…`、dsl.md 句型 系統處於 "{state}"
const DEFAULTS = {
  '房主輪到且尚未改答案': { hostAnswer: '0123', changeAnswerLeft: 1 },
  '房主已用完改答案': { hostAnswer: '0123', changeAnswerLeft: 0 }, // 範疇外起點：只補資料
};
async function setup(state) {
  if (state === '房主輪到且尚未改答案') return createRoomTurn(DEFAULTS[state]); // 範疇內起點才寫建立步驟
  throw new Error(`尚未撰寫的起點：${state}`);
}
```

### Bad Example

這個範例為範疇外的起點也寫了建立步驟，範疇外 Example 的紅燈第一次就通過，失去它之後的紅燈驗證機會。

```js
if (state === '房主已用完改答案') { await useChangeAnswer(room); return room; } // 範疇外，不該在這次撰寫
```

### Bad Example

這個範例看到既有 step 能比對就直接沿用，沒有比對測試撰寫語意；dsl.md 要求猜測前先保存連猜剩餘次數，既有 step 沒有保存，「連猜剩餘次數不變」的斷言沒有比對基準，也沒有依 Rule 12 判定是擴充既有 step 還是交給 dsl-refine 換句子。

```text
backend/dsl.md："{玩家}" 猜 "{四碼}" → 先 GET /api/rooms/current 保存 burst_left，再 POST guesses、保存回應
既有：@step('"{玩家}" 猜 "{四碼}"')（modules/對戰/猜測.py）→ 只 POST guesses、保存回應
處理：能比對 → 直接重用
```

## Rule 2 -- 參數使用領域名稱與型別

**強度：MUST**

參數名稱必須使用 dsl.md 句型參數的領域名稱，不得使用 `string`、`int`、`arg0` 等工具產生的名稱；dsl.md「參數對照」列出的固定選項領域值，例如結果、原因、玩家，必須定義自訂參數型別，在 transformer 中轉成對照表的技術值。

### Good Example

這個範例把結果改用自訂參數型別，step 本體直接拿到領域代碼。

```js
defineParameterType({
  name: 'result',
  regexp: /"(成功|點數不足|超過上限)"/,
  transformer: (label) => ({ 成功: 'OK', 點數不足: 'INSUFFICIENT_POINTS', 超過上限: 'OVER_LIMIT' })[label],
});
Then('兌換結果應該是 {result}', function (expectedCode) {
  assert.equal(this.lastResult.code, expectedCode);
});
```

### Bad Example

這個範例原樣保留 snippet 的參數名，並在 step 本體內轉換中文結果，同樣的轉換表會在每個用到結果的 step 重複出現。

```js
Then('兌換結果應該是 {string}', function (string) {
  const code = string === '成功' ? 'OK' : string === '點數不足' ? 'INSUFFICIENT_POINTS' : 'OVER_LIMIT';
  assert.equal(this.lastResult.code, code);
});
```

## Rule 3 -- Step 只解析、呼叫、斷言

**強度：MUST**

Step 本體只能做三件事：把參數交給 Driver、把結果存進 World、對 Driver 查詢回來的值做斷言。不得出現 locator、URL、SQL、HTTP 呼叫或業務計算；這些細節放在 Driver 或 adapter。

### Good Example

這個範例的 step 只呼叫 Driver，技術細節都在 Driver 內。

```js
When('{string} 兌換 {string}', async function (member, item) {
  this.lastResult = await this.rewards.redeem(member, item, 1);
});
```

### Bad Example

這個範例在 step 內直接呼叫 HTTP，API 路徑一改就要修改所有相關 step，同一份 Gherkin 也無法改用 in-memory 執行。

```js
When('{string} 兌換 {string}', async function (member, item) {
  const res = await fetch(`${baseUrl}/api/members/${member}/redemptions`, {
    method: 'POST', body: JSON.stringify({ item, quantity: 1 }),
  });
  this.lastResult = await res.json();
});
```

## Rule 4 -- Driver 只轉接產品程式

**強度：MUST**

Driver 必須呼叫 dsl.md 測試撰寫語意指定的產品入口（API、UI 或資料表），不得在 Driver 內自行實作業務規則。產品入口還不存在時，Driver 仍照 dsl.md 呼叫該入口，讓失敗呈現為入口不存在，不得在 Driver 內補上替代實作。

### Good Example

這個範例的 Driver 只轉接產品的 `RedemptionService`。

```js
class InMemoryRewardsDriver {
  constructor() { this.service = new RedemptionService(new InMemoryMemberRepo()); }
  async redeem(member, item, quantity) { return this.service.redeem(member, item, quantity); }
}
```

### Bad Example

這個範例在 Driver 內自行計算扣點，測試驗證的是 Driver 自己的邏輯，產品程式完全沒寫，情境也會通過。

```js
class InMemoryRewardsDriver {
  async redeem(member, item, quantity) {
    const cost = this.items[item].cost * quantity;
    if (this.points[member] < cost) return { code: 'INSUFFICIENT_POINTS' };
    this.points[member] -= cost;
    return { code: 'OK' };
  }
}
```

## Rule 5 -- 業務失敗由 When 存成結果

**強度：MUST**

驗證「操作應該失敗」的情境時，Driver 必須把業務失敗轉成結果物件回傳，When 把結果存進 World，Then 再斷言。When 不得讓業務失敗以例外拋出；程式錯誤等非預期例外仍然照常拋出。

### Good Example

這個範例的 When 存下失敗結果，Then 能執行並斷言失敗原因。

```js
When('{string} 兌換 {string}', async function (member, item) {
  this.lastResult = await this.rewards.redeem(member, item, 1); // { code: 'INSUFFICIENT_POINTS' }
});
```

### Bad Example

這個範例讓業務失敗以例外拋出，When 直接失敗，Then 永遠不會執行，「點數不足」的情境無法變成綠燈。

```js
When('{string} 兌換 {string}', async function (member, item) {
  await this.rewards.redeemOrThrow(member, item, 1); // 點數不足時 throw
});
```

## Rule 6 -- 狀態只存在每個情境的 World

**強度：MUST**

情境內步驟之間的狀態只能存在 World（cucumber-js、cucumber-ruby）或 scenario scope 的注入物件（Cucumber-JVM 的 PicoContainer、Spring `@ScenarioScope`），不得使用 global 或 static 變數。cucumber-js 的 step 與 hook 必須使用 `function`，不得使用箭頭函式。

### Good Example

這個範例以 `function` 撰寫 step，透過 `this` 存取每個情境自己的 World。

```js
Given('會員 {string} 有 {int} 點', async function (member, points) {
  await this.rewards.createMember(member, { points });
});
```

### Bad Example

這個範例使用箭頭函式，`this` 不是 World，`this.rewards` 為 undefined，step 一執行就拋出 TypeError。

```js
Given('會員 {string} 有 {int} 點', async (member, points) => {
  await this.rewards.createMember(member, { points });
});
```

## Rule 7 -- 依測試設定的 step 目錄與 dsl.md Step 檔對照放檔且不互相呼叫

**強度：MUST**

每個句型的 step definition 必須放在「測試設定為本端點載入的 step 目錄（依範疇與執行規範判定）」加上「dsl.md Step 檔對照為該句型登記的相對路徑」組成的位置；不得依 Given／When／Then、feature 或情境另行分檔，不得因為既有目錄的分法不同而改放他處，也不得放進其他端點的測試設定載入的 step 目錄。Step 之間不得互相呼叫；需要共用的邏輯抽成一般函式或放進 Driver。已存在且能比對的句型依 Rule 1 處理，不搬移它的檔案；本規則只約束新寫的 step。

### Good Example

這個範例以各端點測試設定載入的 step 目錄加上 dsl.md 登記的相對路徑放檔，backend 與 database 的同名 Step 檔各自落在自己的 step 目錄，改答案能力的 When 與 Then 放進同一個登記的檔案。

```text
backend：behave_runner.py suite=api → step 目錄 backend/tests/api/steps
  dsl.md Step 檔對照：技能｜改答案｜modules/技能/改答案.py｜{玩家} 送出新答案 {四碼}、{玩家} 的目前答案為 {四碼}
  撰寫：backend/tests/api/steps/modules/技能/改答案.py → 送出新答案、目前答案為
database：behave_runner.py suite=database → step 目錄 backend/tests/database/steps
  dsl.md Step 檔對照：技能｜改答案｜modules/技能/改答案.py｜{玩家} 送出新答案 {四碼}、{玩家} 的答案與原答案如下：
  撰寫：backend/tests/database/steps/modules/技能/改答案.py → 送出新答案、答案與原答案如下
```

### Bad Example

這個範例因為既有目錄已有 `modules/對戰/` 就把 dsl.md 登記在 `modules/連猜三次/猜測與回合.py` 的句型改放 `modules/對戰/猜測.py`，dsl.md 與實際位置不一致，下一個依 dsl.md 找 step 的人找不到，dsl-refine 也不知道對照需要修正。

```text
step 目錄：backend/tests/api/steps（behave_runner.py suite=api）
dsl.md：{玩家} 連猜第 {次數} 次 {四碼} → modules/連猜三次/猜測與回合.py
撰寫：backend/tests/api/steps/modules/對戰/猜測.py
```

## Rule 8 -- Data Table 在入口轉成領域物件

**強度：MUST**

Data Table 必須在 step 入口一次轉成領域物件或物件陣列，例如 cucumber-js 的 `table.hashes()` 加上型別轉換，或 Cucumber-JVM 的 `@DataTableType`；不得把原始的 table 傳進 Driver，也不得在後續程式中以欄位索引存取。

### Good Example

這個範例在入口把每一列轉成型別正確的商品物件。

```js
Given('商品目錄如下:', async function (table) {
  for (const row of table.hashes()) {
    await this.rewards.addItem({ name: row['名稱'], cost: Number(row['所需點數']), stock: Number(row['庫存']) });
  }
});
```

### Bad Example

這個範例把原始 table 直接交給 Driver，並以欄位索引存取，表格欄位順序一調整，點數與庫存就會對調，而且仍是字串型別。

```js
Given('商品目錄如下:', async function (table) {
  await this.rewards.addItems(table.raw().slice(1)); // Driver 內用 row[1]、row[2]
});
```

## Rule 9 -- 模組之間不得互相匯入

**強度：MUST**

`modules/<模組>/` 的 step 檔只能匯入 `shared/`、支援程式與 Driver，不得匯入其他模組的 step 檔。需要其他模組的操作時，呼叫該模組的 Driver。Driver 依 step 的分法放在 Driver 根目錄下的 `shared/` 與 `modules/<模組>`。

### Good Example

這個範例的兌換 step 需要先查會員點數，呼叫會員模組的 Driver。

```js
// features/step_definitions/modules/兌換/兌換商品.js
const { memberDriver } = require('../../../../test/drivers/modules/會員');
```

### Bad Example

這個範例直接匯入會員模組的 step 檔，兩個模組的 step 綁在一起，搬動或刪除會員的 step 時兌換的 step 會跟著壞掉。

```js
// features/step_definitions/modules/兌換/兌換商品.js
const { givenMemberHasPoints } = require('../會員/點數');
```

## Rule 10 -- 動作與保存依測試撰寫語意

**強度：MUST**

Given 與 When 的 step 與 Driver 必須逐項做到 dsl.md 該句型「測試撰寫語意」的動作、等待與保存：呼叫的入口、帶的欄位、保存的值與保存給哪個斷言都要相同，不得省略保存項目，也不得改用 dsl.md 沒寫的入口。起點句只依「起點句上方的 `# 預設值：` 註解」建立起點。

### Good Example

這個範例依測試撰寫語意先讀一次房間狀態再送出新答案，並保存三項值給後面的斷言。

```text
dsl.md：動作：先以該玩家身份 GET /api/rooms/current 讀一次，再 POST /api/rooms/{roomId}/skills/change-answer，帶 answer
        保存：這次的回應、動作前的 my_answer 與技能剩餘次數、新答案與被取代的答案
Driver：get_current(玩家) → 保存 my_answer、change_answer_left → post_change_answer(玩家, 四碼) → 保存回應、新舊答案
```

### Bad Example

這個範例只送出新答案，沒有先保存動作前的答案與剩餘次數，「系統拒絕這次改答案」的查證斷言沒有比對基準，只能斷言回應碼，拒絕後答案被偷改也不會失敗。

```text
Driver：post_change_answer(玩家, 四碼) → 保存回應
```

## Rule 11 -- Then 同時寫回應斷言與查證斷言

**強度：MUST**

Then 的 step 必須同時實作 dsl.md 該句型列出的回應斷言與每一項查證斷言；dsl.md 只列其中一種時只實作列出的那一種，不得自行補上或省略任何一項。

### Good Example

這個範例同時斷言回應的 `my_answer` 與再讀一次的結果。

```python
@then('"{玩家}" 的目前答案為 "{四碼}"')
def step_impl(context, 玩家, 四碼):
    assert context.last_response.status_code == 200
    assert context.last_response.json()["my_answer"] == 四碼
    reread = context.rooms.get_current(玩家)
    assert reread.json()["my_answer"] == 四碼
```

### Bad Example

這個範例只寫回應斷言，省略 dsl.md 列出的「再讀確認」，產品程式只改回應不寫進資料庫時 Example 仍會通過。

```python
@then('"{玩家}" 的目前答案為 "{四碼}"')
def step_impl(context, 玩家, 四碼):
    assert context.last_response.json()["my_answer"] == 四碼
```

## Rule 12 -- 既有 step 不一致時判定擴充或撞句

**強度：MUST**

同一個句子已被其他 feature 使用、既有 step 的實作與 dsl.md 該句型的測試撰寫語意不一致，而這個句型不是依 Rule 15 由 red 改寫的情況時，依下列標準判定，不得憑印象：只缺 dsl.md 新增的起點或參數名稱（例如 `系統處於` 這次新增的起點名稱），或只缺 dsl.md 新要求的保存與斷言，補上後不改變既有名稱的行為時，屬「擴充既有 step」，在既有 step 新增分支處理新的名稱或補上缺少的保存與斷言，既有名稱的行為不得改變，不算撞句；必須改變既有名稱的行為才能讓範疇通過，而其他 feature 的 Example 仍依賴原本的行為時，才是撞句（同一個句子被用成兩種意思），歸為「feature 或 dsl.md 有問題」，依 Rule 1 與停下回報規範停下，交由 dsl-refine 換句子。擴充時新增的分支與補上的保存、斷言必須逐項依 dsl.md 該句型的 `# 預設值：` 註解與測試撰寫語意撰寫。

### Good Example

這個範例的 `系統處於` 句子已被既有 feature 使用，既有 step 只缺 dsl.md 這次新增的起點名稱，補上後不改變既有起點的行為，在既有 step 新增分支，既有的分支不動。

```text
既有：@step('系統處於 "{state}"')（shared/系統狀態.py）→ 既有 feature 的起點「房間已建立」「雙方已加入」
backend/dsl.md 同句型：這次新增的起點「房主輪到且尚未改答案」「加入者下一回合不能行動、輪到房主」（既有 step 只缺這兩個名稱，語意同為建立起點）
判定：擴充既有 step → 新增兩個分支，「房間已建立」「雙方已加入」行為不變
```

### Bad Example

這個範例既有的起點「雙方已加入」在 dsl.md 要求多帶技能次數，必須改變既有名稱的行為才能讓範疇通過，而其他 feature 的 Example 仍依賴原本的行為，卻當成擴充直接改既有分支，其他 feature 的 Example 全部被改壞；這是同一個句子被用成兩種意思的撞句，必須停下。

```text
既有：系統處於 "雙方已加入" → 既有 feature：建立房間、兩人加入
backend/dsl.md：系統處於 "雙方已加入" → 建立房間、兩人加入、再把雙方技能次數設為 1
處理：直接修改既有分支加上技能次數 → 既有 feature 的 42 個 Example 行為被改
```

## Rule 13 -- Driver 的等待與動作必須明確指定逾時

**強度：MUST**

Driver 中所有等待與動作（Playwright 的 `click`、`fill`、`waitFor`、`expect(...).toBeVisible()`、`waitForResponse`、`waitForURL`，以及 HTTP 請求）必須明確指定逾時（例如 8 秒），不得依賴測試設定的預設值：`playwright.config.js` 沒有設定 `actionTimeout`，缺元素時單一動作會等到整個測試的 `timeout`（300 秒），紅燈時每個 Example 都要等 5 分鐘。逾時的值寫成 Driver 內的具名常數。

### Good Example

這個範例的 Driver 對每個等待與動作都明確帶 8 秒逾時，缺元素的紅燈 8 秒內就失敗。

```js
const ACTION_TIMEOUT = 8_000;
async submitNewAnswer(answer) {
  await this.page.locator('#answer-input').fill(answer, { timeout: ACTION_TIMEOUT });
  await this.page.getByRole('button', { name: '改答案' }).click({ timeout: ACTION_TIMEOUT });
  await expect(this.page.locator('#my-answer')).toHaveText(answer, { timeout: ACTION_TIMEOUT });
}
```

### Bad Example

這個範例沒有指定逾時，`#answer-input` 尚未實作時 `fill` 等到測試的 300 秒逾時，一個紅燈 Example 就要 5 分鐘，整個端點資料夾的基準跑不完。

```js
async submitNewAnswer(answer) {
  await this.page.locator('#answer-input').fill(answer);
  await this.page.getByRole('button', { name: '改答案' }).click();
}
```

## Rule 14 -- 起點預設值只寫在 Driver 並標明來源

**強度：MUST**

step 讀不到 feature 的 `# 預設值：` 註解，預設值只能寫在 Driver，並在 Driver 的註解標明來源 feature 與 dsl.md 句型；寫入的值不得與 feature 的 `# 預設值：` 註解矛盾，發現不一致時以 feature 註解為準修正 Driver，不得改 feature 或 dsl.md。

### Good Example

這個範例把「房主輪到且尚未改答案」的預設值寫在 Driver，註解標明來源，值與 feature 註解一致。

```js
// 預設值來源：specs/truth/features/backend/改答案.feature 第 12 行 `# 預設值：房主答案 0123、加入者答案 4567、改答案剩餘 1`
// dsl.md 句型：系統處於 "{state}"
const DEFAULTS = { hostAnswer: '0123', guestAnswer: '4567', changeAnswerLeft: 1 };
```

### Bad Example

這個範例的 Driver 預設值沒有標明來源，剩餘次數寫成 2，與 feature 註解的 1 矛盾；「剩餘次數用完」的 Example 起點錯誤，失敗卻被誤判為產品程式問題。

```js
const DEFAULTS = { hostAnswer: '0123', guestAnswer: '4567', changeAnswerLeft: 2 };
```

## Rule 15 -- 句型的測試寫法改了時由 red 改寫既有 step

**強度：MUST**

既有 step 與 dsl.md 該句型的測試撰寫語意不一致，而進行中 plan 的 `truth-changes.md` 把這個句型記為 MOD（對象為 `features/<端點>/dsl.md ＞ 句型「<句型>」`、改動摘要以「改測試寫法：」開頭）時，dsl.md 現在的寫法就是這個句子在每份 feature 的意思，不算撞句：red 必須依 dsl.md 改寫既有的 step 與它呼叫的 Driver（逐項依 Rule 10、Rule 11），step 留在原本登記的 Step 檔，不得改動其他句型的 step，也不得為了相容舊寫法同時保留新舊兩個版本；改寫後依紅燈規範確認其他用到它的 Example。沒有這筆紀錄時不得改寫，依 Rule 12 判定擴充或撞句；green 與 refactor 一律不得改寫。

### Good Example

這個範例的提示句型在 truth-changes 記為改測試寫法，red 依 dsl.md 改寫共用的 step 與 Driver，其他句型的 step 不動。

```text
truth-changes.md › dsl-refine：MOD `features/frontend/dsl.md ＞ 句型「玩家 {玩家} 看到提示 {提示}」`｜改測試寫法：改讀 role=status 區塊的文字
既有：frontend/tests/e2e/steps/shared/提示.js 讀 passcode-error 等元素的文字
處理：改寫 shared/提示.js 與它呼叫的 Driver，改讀 role=status；依紅燈規範確認其他用到它的 Example
```

### Bad Example

這個範例在 truth-changes 沒有這個句型的紀錄時就改寫既有 step，其他 feature 依賴原本行為的 Example 被默默改了意思；這其實是撞句，應該停下交給 dsl-refine 換句子。

```text
truth-changes.md：沒有 `features/backend/dsl.md ＞ 句型「系統處於 {前置狀態}」` 的紀錄
既有：系統處於 "雙方已加入" → 建立房間、兩人加入
處理：依 backend/dsl.md 改寫成另把雙方技能次數設為 1 → 既有 feature 的 42 個 Example 起點被改
```
