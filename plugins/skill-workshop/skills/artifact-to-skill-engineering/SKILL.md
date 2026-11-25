---
name: artifact-to-skill-engineering
description: 使用者想以一份或多份 Artifact 範例為目標建立新 skill 時使用此 skill，範例可為檔案、貼上內容，或僅以敘述說明 Artifact 要記載的資訊。先與使用者客製化所有範例並抽出樣板，再委派 skill-engineering 建立 skill；以預期產出出發的建立或優化既有 skill 交由 skill-engineering，只撰寫樣板交由 skill-form-template。
---

## SOP

### Phase 1 --- 取得範例

1. READ 讀取使用者或呼叫者提供的每個 Artifact（範例或敘述）、流程需求、目標 skill 名稱與存放位置。
2. ASK 目標 skill 名稱或存放位置不明時詢問使用者。
3. THINK 為只有敘述的 Artifact 選定可參考的最佳實踐產出格式。
4. DELEGATE 依 [skill-form-template](../skill-form-template/SKILL.md) 為每個 Artifact 各寫入一份範例至目標 skill 的 `templates/<樣板名稱>.example.<副檔名>`，各 Artifact 的 `<樣板名稱>` 不得重複。

### Phase 2 --- 客製化範例

1. DELEGATE 使用 clarify skill（可由 requirement-clarify plugin 提供，或為與本 skill 資料夾同層的 `clarify` 資料夾）釐清使用者對每份範例的客製化需求，兩者都沒有時不得自行代替，停止並請使用者安裝 requirement-clarify plugin，agent 不支援 plugin 時改為把 `clarify` 資料夾複製到同層。
2. DELEGATE 依 [skill-form-template](../skill-form-template/SKILL.md) 依釐清結果修改每份對應的範例。
3. ASK 請使用者一次確認所有範例是否滿意，有不滿意的範例時針對這些範例回到 Step 1。

### Phase 3 --- 建立 skill

1. DELEGATE 依 [skill-form-template](../skill-form-template/SKILL.md) 為每份範例各抽出一份同名骨架至 `templates/<樣板名稱>.<副檔名>`。
2. DELEGATE 依 [skill-engineering](../skill-engineering/SKILL.md) 以所有骨架與範例、呼叫者提供的流程需求、skill-form-template 回報的流程需求為預期建立目標 skill。
