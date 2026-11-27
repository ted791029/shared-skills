# 授權與出處

本 skill 改寫自 [pbakaus/impeccable](https://github.com/pbakaus/impeccable)（Copyright 2025 Paul Bakaus），依 Apache License 2.0 使用，授權全文見同目錄的 [LICENSE](LICENSE)。

- 取用版本：impeccable 4.11.1（commit `2fc5e1459efbbf06d92c7306517c286bf12490cf`，2026-11-26）
- 本 skill 不是 impeccable 的官方版本，也未經原作者認可。

## 修改說明

- `rules/` 下的設計規範改寫自 impeccable `skill/reference/` 的參考文件，已翻譯為中文、濃縮改寫為「規則 + 正確範例 + 錯誤範例」的格式；`rules/動態規範.md` 改寫自 `skill/reference/animate.md`。
- 本 skill 只產出設計產物（原型、修改規格、PRODUCT.md、DESIGN.md、tokens、檢查報告），不修改專案程式碼；impeccable 直接修改程式碼的流程改為產出修改規格。
- 移除 impeccable 執行檔、偵測器、hook、subagent、即時預覽與設計稿生圖等工具依賴。截圖、渲染後檢查與動態影格擷取改以重新撰寫的 `scripts/畫面擷取.py`（Playwright）實作，由執行本 skill 的 agent 自己檢視截圖。
- `SKILL.md` 的流程、`templates/` 的樣板與 `scripts/` 下的腳本為重新撰寫。
- 未取用 impeccable 的 critique、new-work-comp、visualize、component-review、region-map、live 等文件。
- `rules/視覺方向規範.md` 的七個候選、擲骰與使用者選定方向的概念改寫自 impeccable 的 `skill/reference/new-work-world.md`；impeccable 以編譯後的 `concept-seed` 與 `serve-question` 指令及線上風格目錄實作擲骰與選擇頁，本 skill 未取用這些程式與目錄，`scripts/方向擲骰.py`、`scripts/方向選擇頁.py`、`templates/方向候選.json` 與 `templates/方向選擇頁.html` 為重新撰寫，挑戰者只從本次推導的候選中抽出。

## 第三方內容

- `rules/原生平台規範.md` 的部分內容間接源自 impeccable 所引用的 [ehmo/platform-design-skills](https://github.com/ehmo/platform-design-skills)（MIT License，作者 ehmo）。
- `data/typography.csv` 與 `data/styles.csv` 取自 [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill)（commit `a0d04109f4193a04ec6959549cd735d95ecaa90a`，未修改內容），依 MIT License 使用，授權全文見 [data/LICENSE-ui-ux-pro-max](data/LICENSE-ui-ux-pro-max)。
- `scripts/畫面擷取.py` 執行時以 PEP 723 依賴取得 [Playwright](https://github.com/microsoft/playwright-python)（Apache License 2.0）與 [axe-playwright-python](https://github.com/pamelafox/axe-playwright-python)（內含 axe-core，MPL 2.0）；兩者不隨本 skill 散布。
