---
name: ui-design
description: 要設計新的前端畫面並產出靜態原型，或為既有畫面的收尾修細節、單項改善版面、字體、配色、文案、響應式、效能、錯誤與空狀態、首次使用流程或動態產出修改規格，或檢查畫面有沒有無障礙、效能、響應式等技術問題，或撰寫專案的 PRODUCT.md 與 DESIGN.md，或 ui-direction 委派決定設計方向與撰寫設計系統、ui-ux-plan 委派撰寫原型，或呼叫 /ui-design 時使用此 skill。專案程式碼的修改交由實作流程（例如 SDD 的 implement），素材的選定與取得交由 ui-assets，SDD 流程中的設計方向交由 ui-direction，前端介面文檔的規劃交由 ui-ux-plan，claude.ai Artifact 頁面的設計交由 artifact-design，圖表與資料視覺化交由 dataviz。
---

## SOP

### Phase 1 --- 判斷需求

1. READ 依 [呼叫參數規範](rules/呼叫參數規範.md) 讀取使用者需求或呼叫者指定的參數、PRODUCT.md、DESIGN.md、既有原型與目標畫面的程式碼。
2. THINK 依 [畫面類型規範](rules/畫面類型規範.md) 與 [呼叫參數規範](rules/呼叫參數規範.md) 判斷用法（做新畫面、收尾、技術檢查、單項改善）、畫面類型與這次執行的範圍。
3. ASK 依 [白話提問規範](rules/白話提問規範.md) 與 [呼叫參數規範](rules/呼叫參數規範.md) 在缺少產品背景或設計方向時以白話選項詢問使用者。
4. WRITE 依 [產品背景規範](rules/產品背景規範.md) 與 [呼叫參數規範](rules/呼叫參數規範.md) 與 [PRODUCT.md](templates/PRODUCT.md) 與 [PRODUCT.example.md](templates/PRODUCT.example.md) 在 PRODUCT.md 不存在時產出 PRODUCT.md，或在呼叫者帶入產品背景的差異時更新 PRODUCT.md，技術檢查時不執行。

### Phase 2 --- 決定設計方向

1. DELEGATE 依 [參考資料搜尋.py](scripts/參考資料搜尋.py) 與 [腳本執行規範](rules/script-執行規範.md) 與 [視覺方向規範](rules/視覺方向規範.md) 在建立或取代視覺方向，或單項改善字體而需要更換字型時，以英文關鍵字搜尋字體搭配與風格的候選。
2. THINK 依 [視覺方向規範](rules/視覺方向規範.md) 在做新畫面時決定視覺方向。
3. DELEGATE 依 [ui-assets](../ui-assets/SKILL.md) 與 [呼叫參數規範](rules/呼叫參數規範.md) 在做新畫面或範圍為決定設計方向，且 DESIGN.md 沒有素材節時選定圖示庫、插圖風格與照片來源，技術檢查時不執行。
4. WRITE 依 [設計系統規範](rules/設計系統規範.md) 與 [呼叫參數規範](rules/呼叫參數規範.md) 與 [DESIGN.md](templates/DESIGN.md) 與 [DESIGN.example.md](templates/DESIGN.example.md) 在做新畫面、DESIGN.md 不存在或呼叫者帶入設計系統的異動時產出或增修 DESIGN.md，技術檢查時不執行。
5. DELEGATE 依 [轉token.py](scripts/轉token.py) 與 [腳本執行規範](rules/script-執行規範.md) 與 [設計系統規範](rules/設計系統規範.md) 在產出或增修 DESIGN.md 後轉出 tokens.css 與 tokens.json。

### Phase 3 --- 撰寫設計產物

1. DELEGATE 依 [ui-assets](../ui-assets/SKILL.md) 與 [呼叫參數規範](rules/呼叫參數規範.md) 在畫面需要圖示、插圖或照片，或正式畫面以 emoji 代替圖示或缺圖時取得素材，技術檢查時不執行。
2. WRITE 依 [設計產物規範](rules/設計產物規範.md) 與 [品質底線規範](rules/品質底線規範.md) 與 [收尾規範](rules/收尾規範.md) 與 [版面規範](rules/版面規範.md) 與 [字體規範](rules/字體規範.md) 與 [配色規範](rules/配色規範.md) 與 [強化規範](rules/強化規範.md) 與 [收斂規範](rules/收斂規範.md) 與 [精簡規範](rules/精簡規範.md) 與 [驚喜規範](rules/驚喜規範.md) 與 [突破規範](rules/突破規範.md) 與 [文案規範](rules/文案規範.md) 與 [響應式規範](rules/響應式規範.md) 與 [效能規範](rules/效能規範.md) 與 [強韌規範](rules/強韌規範.md) 與 [首次使用規範](rules/首次使用規範.md) 與 [原生平台規範](rules/原生平台規範.md) 與 [動態規範](rules/動態規範.md) 中對應用法的規範，在做新畫面或目標是原型時撰寫或修改原型。
3. WRITE 依 [設計產物規範](rules/設計產物規範.md) 與 [修改規格.md](templates/修改規格.md) 與 [修改規格.example.md](templates/修改規格.example.md) 在收尾或單項改善既有畫面時撰寫修改規格與需要的局部示意。

### Phase 4 --- 實測與檢查

1. DELEGATE 依 [畫面擷取.py](scripts/畫面擷取.py) 與 [實測規範](rules/實測規範.md) 與 [腳本執行規範](rules/script-執行規範.md) 以 shot 擷取實測對象的截圖、溢出、超出畫面、渲染後對比與 axe-core 結果。
2. DELEGATE 依 [畫面擷取.py](scripts/畫面擷取.py) 與 [動態規範](rules/動態規範.md) 與 [腳本執行規範](rules/script-執行規範.md) 在這次新增或修改動態時，以 motion 擷取正常與減少動態兩組影格。
3. DELEGATE 依 [對比檢查.py](scripts/對比檢查.py) 與 [腳本執行規範](rules/script-執行規範.md) 計算圖示、元件邊框與疊在圖片上的文字的對比，以及未實測時所有文字的對比。
4. THINK 依 [品質底線規範](rules/品質底線規範.md) 與 [技術檢查規範](rules/技術檢查規範.md) 與 [設計評分規範](rules/設計評分規範.md) 與 [實測規範](rules/實測規範.md) 逐條檢查設計產物或正式畫面的程式碼、截圖與影格。
5. WRITE 依 [實測規範](rules/實測規範.md) 在原型或局部示意有 P0 或 P1 的問題時修正，並重新執行 Step 1 至 Step 4 一輪。
6. WRITE 依 [設計系統規範](rules/設計系統規範.md) 與 [呼叫參數規範](rules/呼叫參數規範.md) 在這次新增或變更 token（含動態）時寫回 DESIGN.md，範圍不允許改寫 DESIGN.md 時列入回報。
7. DELEGATE 依 [轉token.py](scripts/轉token.py) 與 [腳本執行規範](rules/script-執行規範.md) 在 Step 6 寫回 DESIGN.md 後重新轉出 tokens。
8. WRITE 依 [呼叫參數規範](rules/呼叫參數規範.md) 與 [檢查報告.md](templates/檢查報告.md) 與 [檢查報告.example.md](templates/檢查報告.example.md) 撰寫中文的檢查報告。
