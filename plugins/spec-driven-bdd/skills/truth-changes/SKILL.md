---
name: truth-changes
description: truth owner skill（technical-research、api-plan、data-plan、dsl-refine 與其他產出寫進 `specs/truth/` 的 Planner）要在修改 truth 前盤點這次的新增、修改、刪除，或修改後把異動記進 plan 的 `truth-changes.md` 並核對，或下游 skill 要查上游改了哪些 truth，或呼叫 /truth-changes 時使用此 skill。決定改什麼與實際修改 truth 交由各 truth owner，開發中發現的問題交由 dev-finding，plan 的開立與交付交由 plan-package，AC 對 Rule 的涵蓋表交由 dsl-refine。
---

## SOP

### Phase 1 --- 確認呼叫

1. READ 讀取呼叫者指定的子命令、owner、呼叫者帶入的輸入差異，與目標 plan 的 `.plan.json`、spec.md、`技術項.md` 與 `truth-changes.md`。
2. ASK 未指定子命令時列出 inventory、record、query 三個入口並停止。
3. THINK 依子命令只執行 Phase 2、Phase 3 或 Phase 4 其中一個。

### Phase 2 --- 盤點異動（inventory）

1. DELEGATE 依 [truth_changes.py](scripts/truth_changes.py) 與 [腳本執行規範](rules/script-執行規範.md) 列出上游各 owner 已記錄的列與基準以來實際異動的 truth 檔案。
2. READ 讀取該 owner 路徑下的 truth 現況。
3. THINK 依 [異動盤點規範](rules/異動盤點規範.md) 判定該 owner 要新增、修改、刪除的 truth 內容與各自的原因。
4. WRITE 依 [盤點清單.md](templates/盤點清單.md) 與 [盤點清單.example.md](templates/盤點清單.example.md) 在對話中把盤點清單回覆給呼叫者，不寫入檔案。

### Phase 3 --- 記錄異動（record）

1. WRITE 依 [紀錄撰寫規範](rules/紀錄撰寫規範.md) 與 [truth-changes.md](templates/truth-changes.md) 與 [truth-changes.example.md](templates/truth-changes.example.md) 整張改寫 `truth-changes.md` 中該 owner 的表格。
2. DELEGATE 依 [truth_changes.py](scripts/truth_changes.py) 與 [腳本執行規範](rules/script-執行規範.md) 核對該 owner 的表格與基準以來的實際異動是否一致。
3. WRITE 修正核對列出的漏記與多記。

### Phase 4 --- 查詢異動（query）

1. DELEGATE 依 [truth_changes.py](scripts/truth_changes.py) 與 [腳本執行規範](rules/script-執行規範.md) 依呼叫者的條件輸出已記錄的列、實際異動的 truth 檔案、異動的 Rule 或指定 AC 的列。
