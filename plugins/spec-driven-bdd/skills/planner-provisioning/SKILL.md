---
name: planner-provisioning
description: system-analysis 產出 plan.md 後、執行分析 Wave 前，要確認每個端點委派的 Planner skill 是否存在並補建缺少的 Planner，或呼叫 /planner-provisioning 時使用此 skill。plan.md 的規劃與 Wave 的執行交由 system-analysis，plan 的狀態檢查交由 plan-package，建立 Planner 交由 artifact-to-skill-engineering，優化已存在的 Planner 交由 skill-engineering。
---

## SOP

### Phase 1 --- 讀取輸入

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 確認目標是進行中的 plan，被拒絕時停止。
2. READ 讀取這個 plan 的 plan.md，以及與本 skill 資料夾同層的各 skill 的 name 與 description。

### Phase 2 --- 配對 Planner

1. THINK 依 [Planner 配對規範](rules/Planner配對規範.md) 與 [planner-matching.md](templates/planner-matching.md) 與 [planner-matching.example.md](templates/planner-matching.example.md) 從 plan.md 每個 Wave 的端點依介面 ID 前綴盤點所需 Planner，並依名稱與職責與既有 skill 配對出已有、疑似已有、不符或缺少。
2. ASK 請使用者確認配對表。

### Phase 3 --- 撰寫委派簡報

1. THINK 依 [委派簡報撰寫規範](rules/委派簡報撰寫規範.md) 與 [planner-brief.md](templates/planner-brief.md) 與 [planner-brief.example.md](templates/planner-brief.example.md) 為每個缺少及使用者決定另建的 Planner 撰寫委派簡報。
2. ASK 請使用者確認委派簡報。

### Phase 4 --- 建立 Planner

1. ASK 本 skill 位於 plugin 的安裝目錄時，請使用者提供該 plugin 原始 repo 的路徑。
2. DELEGATE 使用 artifact-to-skill-engineering skill（可由 skill-workshop plugin 提供，或為與本 skill 資料夾同層的 `artifact-to-skill-engineering` 資料夾）以每份確認後的委派簡報中的所有 Artifact 敘述、流程需求與存放位置建立 Planner skill，兩者都沒有時不得自行代替，停止並請使用者安裝 skill-workshop plugin，agent 不支援 plugin 時改為把 `artifact-to-skill-engineering` 資料夾複製到同層。
3. ASK Planner 建立在 plugin 的原始 repo 時，請使用者更新 plugin 並停止，更新後才能執行分析 Wave。
