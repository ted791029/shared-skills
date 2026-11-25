---
name: analyze
description: 使用者已有任務清單（tasks.md），要在實作前檢查進行中的 plan 與 `specs/truth/` 中這次異動之間的一致性與覆蓋缺口、只要分析報告不要修改產物，或呼叫 /analyze 時使用此 skill。含 `.specify/` 的原版 spec-kit 專案交由 speckit-analyze，plan 的待補跑與交叉檢查交由 plan-package，掃描 spec.md 盲點並寫回交由 clarify-over-specs，產物的修正交由產出它的 skill。
---

## SOP

### Phase 1 --- 讀取輸入

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 確認目標是進行中的 plan，並取得待補跑與交叉檢查的結果，被拒絕時停止。
2. READ 讀取使用者指定的分析重點，以及同一對話中的前次分析報告。
3. DELEGATE 依 [collect_artifacts.py](scripts/collect_artifacts.py) 與 [腳本執行規範](rules/script-執行規範.md) 盤點這個 plan 與 `specs/truth/` 的必要產物、truth 用語表登記的端點資料夾、各端點的介面文檔、這次沒有案例的端點，以及 wave-report.md 的 Planner 狀態。
4. DELEGATE 依 [check_plan.py](../system-analysis/scripts/check_plan.py) 與 [腳本執行規範](rules/script-執行規範.md) 檢查 plan.md 的結構。
5. DELEGATE 依 [check_tasks.py](../task/scripts/check_tasks.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 collect_artifacts.py 輸出的 `own_doc_args` 作為 `--own-doc` 檢查 tasks.md 的結構。
6. READ 依 [憲法套用規範](../constitution/rules/憲法套用規範.md) 讀取每份產物與介面文檔適用的憲法條款。
7. ASK 依 [前置檢查規範](rules/前置檢查規範.md) 在必要產物、端點資料夾或介面文檔缺漏時列出缺漏，並請使用者先執行產出它的上游 skill。

### Phase 2 --- 建立追溯模型

1. DELEGATE 依 [build_trace.py](scripts/build_trace.py) 與 [腳本執行規範](rules/script-執行規範.md) 解析需求與受影響的既有功能、介面盤點、這次異動的介面文檔段落、涵蓋表、acceptance 涵蓋註解、這次新增與修改的 Rule、端點 feature 與 dsl.md，以及 tasks.md 的 Phase 標頭與任務，輸出追溯 JSON。
2. THINK 依 [需求盤點規範](rules/需求盤點規範.md) 判定每個 SC 是否需要建置，以及每個需求的落點類型。

### Phase 3 --- 偵測問題

1. THINK 依 [覆蓋判定規範](rules/覆蓋判定規範.md) 判定需求覆蓋、受影響的既有功能、介面文檔覆蓋與反向覆蓋的狀態。
2. THINK 依 [問題偵測判準](rules/問題偵測判準.md) 找出模糊、重複、規格不足、不一致與憲法違反的發現事項。
3. THINK 依 [嚴重度與編號規範](rules/嚴重度與編號規範.md) 為每個發現事項分級、編號，並與同一對話中的前次分析比對。

### Phase 4 --- 輸出報告

1. WRITE 依 [報告撰寫規範](rules/報告撰寫規範.md) 與 [report.md](templates/report.md) 與 [report.example.md](templates/report.example.md) 在對話中輸出分析報告。
2. ASK 詢問使用者是否要針對前 N 個發現事項提出具體修正建議，不修改任何產物。
