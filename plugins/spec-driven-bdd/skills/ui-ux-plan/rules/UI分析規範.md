# UI 分析規範

## Rule 1 -- 每個介面必須涵蓋四種狀態

**強度：MUST**

每個介面必須寫出成功、載入、空狀態與錯誤四種狀態的呈現。某種狀態不會單獨出現時，必須寫出該情況下畫面會怎麼處理，不得留空或省略。

### Good Example

這個範例的燈箱不會單獨出現空狀態，仍寫出刪到沒有照片時的處理。

```markdown
| 空狀態 | 不單獨出現；刪到沒有照片時關閉燈箱並離開相簿頁 |
```

### Bad Example

這個範例省略空狀態，實作時刪光照片的燈箱沒有定義行為，可能停留在一個空白疊層。

```markdown
| 成功 | 顯示大圖與上一張／下一張控制 |
| 載入 | 大圖區域顯示載入中 |
| 錯誤 | 無法解碼時顯示提示 |
```

## Rule 2 -- 需要內層提供只寫資料與動作

**強度：MUST**

「需要內層提供」必須寫出操作需要的資料項目與動作，讓後端的 Planner 據此設計 API；不得寫出 API 路徑、HTTP 方法或欄位型別。操作完全在前端完成時寫「無」並說明原因。

### Good Example

這個範例只寫出需要的資料項目，API 設計留給後端。

```markdown
| 瀏覽相簿列表 | 開啟主頁，以卡片顯示名稱、照片數量與封面縮圖 | 相簿列表（識別、名稱、照片數、封面位址、目前順序） |
```

### Bad Example

這個範例寫出 API 路徑與回應欄位，前端分析越界替後端做了設計，後端的 Planner 被未經分析的路徑綁住。

```markdown
| 瀏覽相簿列表 | 開啟主頁顯示卡片 | `GET /api/albums` 回傳 `{ id, name, photoCount }` |
```

## Rule 3 -- 文案必須涵蓋所有可見文字與無障礙文字

**強度：MUST**

文案與無障礙表必須列出介面上每個可見文字、錯誤訊息、替代文字與螢幕閱讀器播報，語言與用語遵循 spec.md 的要求；含變數的文案以 `{變數名稱}` 標示。

### Good Example

這個範例列出替代文字與播報，變數以大括號標示。

```markdown
| 封面替代文字 | {相簿日期}，{照片數量} 張照片 |
| 放下播報 | {相簿名稱}已移到第 {新序} 本，共 {總數} 本 |
```

### Bad Example

這個範例只列出按鈕文字，缺少替代文字與播報，實作時各自決定文案，無障礙要求無法驗收。

```markdown
| 匯入按鈕 | 匯入照片 |
```

## Rule 4 -- 原型必須對應契約的操作與狀態

**強度：MUST**

原型必須為 ui-contract.md 的每個頁面各產出一個可直接以瀏覽器開啟的 HTML，實作契約中的每個操作，並能以 `?state=` 切換到每種非成功狀態；`states.html` 必須列出每個頁面每種狀態的連結。原型的文案必須與契約一致。介面標 MOD 的頁面，以先前 plan 中最新的同一頁原型為底修改，沒有改變的部分保持一致。

### Good Example

這個範例的狀態入口列出主頁的每種狀態，連結可直接切換。

```html
<li><a href="index.html?state=loading">載入<code>?state=loading</code></a></li>
<li><a href="index.html?state=empty">空狀態<code>?state=empty</code></a></li>
```

### Bad Example

這個範例的原型只呈現成功狀態，契約定義的空狀態與錯誤無法在原型中檢視，驗收時無法比對畫面。

```html
<li><a href="index.html">主頁</a></li>
```

## Rule 5 -- 原型的定位屬性必須與契約一致

**強度：MUST**

原型中每個介面與可操作元素的 `data-testid` 必須與 ui-contract.md 的定位屬性完全相同，讓驗收測試的定位器能先在原型上驗證。不得為原型另取一套定位名稱。

### Good Example

這個範例的相簿列表沿用契約定位 `[data-testid="home-album-list"]`。

```html
<ul class="album-grid" id="grid" data-testid="home-album-list" aria-label="相簿列表"></ul>
```

### Bad Example

這個範例在原型改用 `album-grid`，依契約撰寫的驗收步驟在原型上找不到元素，契約與原型無法互相對照。

```html
<ul class="album-grid" data-testid="album-grid"></ul>
```

## Rule 6 -- 原型的視覺依設計系統交由 ui-design

**強度：MUST**

這次範圍有新增的頁面或畫面有變動的修改頁面時，原型必須委派 ui-design skill（可由 ui-studio plugin 提供，或為與本 skill 資料夾同層的 `ui-design` 資料夾）撰寫，以 `specs/truth/ui/DESIGN.md` 為視覺依據，並把 `specs/truth/ui/tokens.css` 的內容原樣放進原型的 `<style>`，優先完整呈現契約的操作、狀態與文案；不得由本 skill 自行決定配色、字體與元件樣式；只為既有元素補上定位時不算畫面有變動，直接補上 `data-testid`，不委派也不需要 DESIGN.md。`specs/truth/ui/DESIGN.md` 或 `tokens.css` 不存在時不得撰寫原型，這次的結果是「不能改」，回報交給 ui-direction 建立設計方向或轉出 tokens。

### Good Example

這個範例依 DESIGN.md 委派撰寫原型，DESIGN.md 不存在的另一個 plan 則停止並交給 ui-direction。

```text
plan 005：specs/truth/ui/DESIGN.md 存在 → 委派 ui-design，以 DESIGN.md 的品牌藍、表格與按鈕元件撰寫 export.html，契約的四種狀態都能以 ?state= 切換。
plan 006：specs/truth/ui/DESIGN.md 不存在 → 不撰寫原型，結果不能改，交給 ui-direction 建立設計方向。
```

### Bad Example

這個範例在沒有 DESIGN.md 時自行挑選配色寫出原型，實作照原型做出的畫面沒有經過設計方向的決定，下一個功能的頁面也找不到可以沿用的視覺系統。

```text
plan 006：specs/truth/ui/DESIGN.md 不存在 → 先用灰階配色與系統字體寫出 signup.html，之後再補設計。
```

## Rule 7 -- 修改與移除的介面只寫這次的改變

**強度：MUST**

介面的操作、狀態或文案因本 plan 標 `@開發發現` 的 AC 而新增或改變時，在該列的說明寫出 AC 編號（例如「依 AC-09」），PM 否決或改寫這個 AC 時 ui-ux-plan 才會成為待補跑。介面列的異動為 ADD 時完整寫出該介面。異動為 MOD 時只寫這次新增與改變的操作、狀態與文案；沒有改變的部分不重抄，在「操作」與「文案與無障礙」表各以一列「沿用」寫出它們見哪個 plan 的 `ui/ui-contract.md` 的哪個介面，「狀態」表保留四列，沒有改變的狀態寫「沿用，見 <plan> 的 <介面>」，被移除的文案與定位在「文案與無障礙」表以一列「移除」列出。異動為 DEL 時該節只保留標題，寫一行說明使用者改由哪裡完成原本的操作，並列出被移除的定位。異動為「無」的介面不寫入契約。以下 Example 皆對照此介面列與既有的描述：

```text
介面列：| UI-02 | 相簿平鋪預覽介面（點擊縮圖下載原圖） | 前端 | MOD | FR-022 |
既有的描述：specs/plans/001-photo-album-organizer/ui/ui-contract.md 的 UI-03，點擊縮圖開啟燈箱
```

### Good Example

這個範例只寫改變後的操作、狀態與文案，沒有改變的部分以「沿用」指向 001 的 UI-03，狀態表保留四列，被移除的定位以「移除」列出。

```markdown
| 操作 | 互動 | 需要內層提供 |
|---|---|---|
| 下載原圖 | 點擊縮圖後下載該照片的原圖，縮圖上顯示「下載中…」 | 照片的原圖 |
| 沿用 | 捲動載入、刪除照片，見 001 的 UI-03 | — |
```

```markdown
| 狀態 | 呈現 |
|---|---|
| 成功 | 沿用，見 001 的 UI-03 |
| 載入 | 點擊的縮圖上顯示「下載中…」，其餘縮圖照常可捲動與刪除 |
| 空狀態 | 沿用，見 001 的 UI-03 |
| 錯誤 | 沿用，見 001 的 UI-03 |
```

```markdown
| 項目 | 文案 |
|---|---|
| 下載中的提示 | 「下載中…」 |
| 移除 | 開啟燈箱的定位 `[data-testid="open-lightbox"]` |
| 沿用 | 空狀態、載入與刪除的文案，見 001 的 UI-03 |
```

### Bad Example

這個範例把 001 的 UI-03 整節重抄一次再改掉一列，兩份契約描述同一個畫面，讀者看不出這次改了什麼；被移除的定位也沒有交代，實作時不知道要刪除哪個元素。

```markdown
| 操作 | 互動 | 需要內層提供 |
|---|---|---|
| 捲動載入 | 捲到底部時載入下一批縮圖 | 相簿內照片的下一頁 |
| 刪除照片 | 點擊刪除並確認後移除縮圖 | 刪除照片 |
| 下載原圖 | 點擊縮圖後下載該照片的原圖 | 照片的原圖 |
```

## Rule 8 -- 測試擬定的定位必須補進 UI 契約

**強度：MUST**

testid 的家是 UI 契約。技術項或交辦指出 dsl-refine 為某個元素擬定了 UI 契約沒有的 testid 時，必須先讀該元素所在介面最近一次的描述再處理：描述中這個元素已有定位時（包括與擬定的 testid 相同）不新增，經 dev-finding 交給 dsl-refine 改用既有的定位；描述有這個元素但沒有定位時，在本 plan `ui/ui-contract.md` 該介面一節的「文案與無障礙」表，於該元素的一列寫出「（定位 `[data-testid="<testid>"]`）」，原型的同一元素加上相同的 `data-testid`；描述沒有這個元素時，這是規格沒寫的畫面元素，經 dev-finding 記錄，不得只補定位。該介面在本 plan 不是 ADD 或 MOD 時，依 Rule 9 回報。以下 Example 皆對照此技術項與介面：

```text
技術項：
- dsl.md 擬定了連猜確認視窗取消鈕的 testid `triple-guess-cancel`，UI 契約沒有（dsl-refine；`specs/truth/features/frontend/dsl.md:110`；修正：ui-ux-plan）
- dsl.md 擬定了連猜確認鈕的 testid `triple-guess-ok`，UI 契約沒有（dsl-refine；`specs/truth/features/frontend/dsl.md:112`；修正：ui-ux-plan）
- dsl.md 擬定了連猜確認視窗關閉鈕的 testid `triple-guess-close`，UI 契約沒有（dsl-refine；`specs/truth/features/frontend/dsl.md:114`；修正：ui-ux-plan）
本 plan 的介面列：| UI-02 | 對戰畫面技能介面（連猜確認視窗） | 前端 | MOD | FR-003 |
最近一次的描述（002 的 UI-01「文案與無障礙」）：
- 連猜取消鈕 | 取消（沒有定位）
- 連猜確認鈕 | 確認使用（定位 `[data-testid="triple-guess-confirm"]`）
- 沒有關閉鈕
```

### Good Example

這個範例依最近一次的描述分三種情況處理：只為沒有定位的取消鈕補上定位與原型的 testid，已有定位的確認鈕交給 dsl-refine 改用既有的，描述中不存在的關閉鈕交給 dev-finding 記錄。

```text
- triple-guess-cancel：描述有取消鈕、沒有定位 → UI-02 一節「文案與無障礙」寫「| 連猜取消鈕 | 取消（定位 `[data-testid="triple-guess-cancel"]`） |」，game.html 的取消鈕加上 data-testid="triple-guess-cancel"
- triple-guess-ok：確認鈕已有定位 triple-guess-confirm → 不新增，經 dev-finding 交給 dsl-refine 改用 triple-guess-confirm
- triple-guess-close：描述沒有關閉鈕 → 規格沒寫的畫面元素，經 dev-finding 記錄，不補定位
```

### Bad Example

這個範例把 testid 當成測試自己的事，只在回報中提到 dsl.md 已擬定；這些定位只存在於 dsl.md，下一個 plan 讀 UI 契約最近一次的描述時看不到它們，可能為同一個按鈕另取名稱，既有測試的定位跟著失效。

```text
UI-02：連猜取消鈕、確認鈕與關閉鈕的 testid 已由 dsl.md 擬定，契約不另外記載。
```

## Rule 9 -- plan.md 的上游問題只回報 system-analysis

**強度：MUST**

分析或判斷差異時發現 plan.md 的上游問題，必須只回報，不得修改 plan.md，也不得為受影響的介面撰寫或修改契約與原型：要新增、修改或移除的介面在介面盤點沒有 ADD、MOD、DEL 的列（包括標「無」的介面），或介面列的依據需求缺了驅動它的需求。技術項或交辦要改的介面在本 plan 已是 ADD 或 MOD 時，技術項就是依據，不算依據需求缺漏。不受影響的介面照常完成，這次的結果是「不能改」，回報要新增或修改的介面列（介面、異動，以及依據需求或「技術：」開頭的原因）交給 system-analysis。技術修正 plan 沒有 plan.md，不適用本條。以下 Example 皆對照此介面列與差異：

```text
本 plan 的介面列：
| UI-01 | 結果畫面介面（總回合數） | 前端 | MOD | FR-005 |
| UI-02 | 對戰畫面技能介面（連猜確認視窗） | 前端 | 無 | FR-003 |
check 列出的差異：
- MOD plan:spec.md＞FR-005
- ADD plan:技術項.md＞dsl.md 擬定了連猜確認視窗取消鈕的 testid `triple-guess-cancel`，UI 契約沒有
```

### Good Example

這個範例照常完成 UI-01，UI-02 標「無」而不寫入契約，回報 system-analysis 把它改為 MOD，沒有記錄。

```text
FR-005 → 連帶異動：UI-01 依新的需求改寫，契約與原型完成並通過核對。
技術項 → 不能改：UI-02 在介面盤點標「無」，補上取消鈕的定位需要在本 plan 的 UI 契約寫入 UI-02。
交給：system-analysis 把 UI-02 改為 MOD，依據需求補上「技術：補上 dsl.md 擬定的定位 triple-guess-cancel」。
這次沒有記錄，ui-ux-plan 仍是待補跑。
```

### Bad Example

這個範例自己把 plan.md 的 UI-02 改為 MOD 再寫入契約；plan.md 的修改沒有經過 system-analysis 與 check_plan.py 的檢查，同一個 Wave 中回報同一列的其他 Planner 也會各自改寫它而互相覆蓋。

```text
已把 plan.md 的 UI-02 由「無」改為 MOD，並在 ui/ui-contract.md 新增 UI-02 一節補上 triple-guess-cancel；記錄改了。
```

## Rule 10 -- UI 契約必須讓涵蓋的 AC 成立

**強度：MUST**

涵蓋本端點介面列依據需求的 AC，每個操作步驟與看得到的斷言都必須能在 UI 契約描述的畫面上完成：AC 用到的操作、狀態、文案與標示要寫進該介面的操作、狀態與「文案與無障礙」，不得只依 FR 的文字設計出與 AC 相反或做不到 AC 的畫面。AC 與 spec.md 的需求或前置端點的產出矛盾時不自行選邊，經 dev-finding 記錄並交給回覆寫明的應修正的擁有者，這次的結果是「不能改」。以下 Example 皆對照此需求與 AC：

```text
FR-005：客人可以取消自己的預約
AC-02（# 涵蓋：US1、FR-005）："王小明" 按 "取消預約" → 看到 "預約已取消"，而且預約清單仍列出這筆預約並標為 "已取消"
```

### Good Example

這個範例依 AC-02 寫出取消後的提示、清單保留這筆預約與已取消的標示。

```markdown
| 操作 | 互動 | 需要內層提供 |
|---|---|---|
| 取消預約 | 按「取消預約」後顯示「預約已取消」；這筆預約留在清單中，狀態欄改為「已取消」並停用「取消預約」 | 取消預約（預約編號）；取消後的預約與它的狀態 |
```

### Bad Example

這個範例只依 FR-005 的「取消」設計成把預約從清單移除；AC-02 的「仍列出並標為已取消」在畫面上做不到，要等 dsl-refine 衍生 AC-02 時才發現，再經 dev-finding 交回 ui-ux-plan 多走一輪。

```markdown
| 操作 | 互動 | 需要內層提供 |
|---|---|---|
| 取消預約 | 按「取消預約」後顯示「預約已取消」，這筆預約從清單移除 | 取消預約（預約編號） |
```

## Rule 11 -- 原型只用本功能的內嵌假資料

**強度：MUST**

原型只能使用內嵌的假資料，不得呼叫後端或外部服務；假資料必須依本功能的業務內容設計。範例原型的視覺精細度、假資料產生方式與頁面配置屬於該功能的設計，不得照搬到其他功能。

### Good Example

這個範例為報名表單功能內嵌幾筆符合業務內容的報名資料，沒有呼叫任何服務。

```html
<script>
const registrations = [
  { name: "林雅婷", course: "週六兒童陶藝", status: "已報名" },
  { name: "陳柏翰", course: "平日成人拉坯", status: "候補第 2 位" }
];
</script>
```

### Bad Example

這個範例為報名表單功能照搬相簿範例的 SVG 風景圖產生器，並向後端要資料；原型離不開後端就無法單獨開啟，與本功能無關的視覺還佔去大量篇幅。

```html
<script>
function photoSrc(p) { /* 產生山景、海景 SVG …… */ }
fetch("/api/registrations").then((res) => res.json()).then(render);
</script>
```
