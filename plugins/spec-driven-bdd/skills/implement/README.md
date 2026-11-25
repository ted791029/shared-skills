# implement

與原版的主要差異：標 `[紅燈]`、`[綠燈]`、`[重構]` 的任務以任務的範疇（整份 feature 或端點資料夾）連同所屬 Phase 標頭的 NFR 約束、預計修改與必讀委派 bdd 的 red、green、refactor 執行，標 `[驗證]` 的任務委派 bdd 的 verify 執行所有端點的測試（整份 tasks.md 唯一一次，收尾引用其結果），並以 dsl-refine 產出的plan 的涵蓋表判定各故事的驗收標準。
