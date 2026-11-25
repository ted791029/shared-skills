---
name: dev-finding
description: 工作流中 /specify 之後的任何 skill 在開發過程發現規格、truth 或程式沒寫清楚、互相不一致或有缺陷，要留下紀錄，或使用者要在技術修正 plan 記下要修的技術問題，或要在拆任務前與交付前請使用者確認開發中發現的 AC，或呼叫 /dev-finding 時使用此 skill。問題的修正由出錯資料的擁有者負責，需求缺口的訪談交由 clarify，PM 提出的驗收案例交由 spec-by-example，需求的改寫交由 clarify-over-specs，truth 異動的紀錄與查詢交由 truth-changes，plan 的開立、記錄與交付交由 plan-package。
---

## SOP

### Phase 1 --- 確認呼叫

1. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 與本 skill 名稱，確認目標是進行中的 plan 並取得 plan 的種類，被拒絕時停止。
2. READ 讀取呼叫者指定的入口、發現的現象、依據與發現的 skill，以及目標 plan 既有的 spec.md、`features/acceptance/`、`技術項.md` 與依據引用的檔案。
3. ASK 未指定入口時列出 record、review 兩個入口並停止。

### Phase 2 --- 記錄發現（record）

1. THINK 依 [發現分類規範](rules/發現分類規範.md) 判定每個發現屬於違反已核准的需求、PM 看得到的行為，或看不到的技術問題。
2. ASK 依 [串接規範](../plan-package/rules/串接規範.md) 在技術修正 plan 中每個發現都判定為 PM 看得到的行為時，以「不能改」回覆擋住它們的規則與需以有需求的 plan 處理，不記錄並停止。
3. THINK 依 [修正擁有者規範](rules/修正擁有者規範.md) 判定每個發現應修正的擁有者、要修正的內容與交辦方式。
4. WRITE 依 [開發發現 AC 規範](rules/開發發現AC規範.md) 與 [Gherkin 撰寫規範](../spec-by-example/rules/Gherkin撰寫規範.md) 與 [功能.feature](../spec-by-example/templates/功能.feature) 在需求 plan 中發現屬於 PM 看得到的行為時，於 `features/acceptance/` 新增標上 `@開發發現` 的 AC。
5. WRITE 依 [技術項.md](templates/技術項.md) 與 [技術項.example.md](templates/技術項.example.md) 在發現屬於看不到的技術問題，或屬於直接修而應修正的擁有者不是呼叫者時，於 plan 的 `技術項.md`（不存在時依樣板建立）加一行並寫上應修正的擁有者。
6. DELEGATE 依 [check_findings.py](scripts/check_findings.py) 與 [腳本執行規範](rules/script-執行規範.md) 在新增 AC 或技術項後檢查它們的寫法與修正的擁有者。
7. WRITE 修正檢查發現的問題。
8. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 在新增了 AC 或技術項時以 record 記錄這次的結果是「改了」。
9. WRITE 回覆呼叫者每個發現的分類結果、新增的 AC 編號、技術項或被違反的需求編號、應修正的擁有者、要修正的內容與交辦方式，技術修正 plan 中不能處理的發現另寫擋住它的規則與需以有需求的 plan 處理。

### Phase 3 --- 列出並確認（review）

1. DELEGATE 依 [check_findings.py](scripts/check_findings.py) 與 [腳本執行規範](rules/script-執行規範.md) 列出這個 plan 所有標 `@開發發現` 的 AC 與它們的確認狀態。
2. WRITE 沒有標 `@開發發現` 的 AC 時回報沒有開發發現並結束。
3. THINK 依 [開發發現 AC 規範](rules/開發發現AC規範.md) 比對每個 AC 與 PM 提出的 AC、spec.md 的 FR 與 NFR 找出矛盾之處，並依確認狀態判定這次要詢問的 AC。
4. ASK 有要詢問的 AC 時逐一列出它們的 Example 原文、發現的 skill、依據、確認狀態與矛盾之處，不再詢問的已確認 AC 只列編號，請使用者回覆這個 plan 不處理或要修改的 AC，並寫明沒有提到的 AC 視為保留、有矛盾的 AC 保留時會以它取代矛盾的一方。
5. WRITE 依使用者的回覆刪除或改寫指定的 AC。
6. DELEGATE 依 [check_findings.py](scripts/check_findings.py) 與 [腳本執行規範](rules/script-執行規範.md) 以 `--confirm` 記下這次詢問後保留或改寫的每個 AC 與它取代的對象。
7. DELEGATE 依 [clarify-over-specs](../clarify-over-specs/SKILL.md) 在保留並取代 FR 或 NFR 時，交辦依保留的 AC 改寫那條需求。
8. DELEGATE 依 [spec-by-example](../spec-by-example/SKILL.md) 在保留並取代 PM 提出的 AC 時，交辦依保留的 AC 改寫那條 AC。
9. DELEGATE 依 [truth_changes.py](../truth-changes/scripts/truth_changes.py) 與 [腳本執行規範](rules/script-執行規範.md) 列出被刪除或改寫的 AC 造成的 truth 異動列。
10. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 在刪除或改寫了 AC 時以 record 記錄這次的結果是「改了」。
11. DELEGATE 依 [plan-package](../plan-package/SKILL.md) 以 check 帶入目標 plan 取得待補跑。
12. WRITE 回報每個 AC 的處理結果、受影響的 truth 異動、保留並取代的交辦結果與待補跑。
