---
name: clarify
description: 需求或輸入存在缺漏、矛盾、模糊或尚未拍板的決策，要直接訪談使用者拍板、不由 AI 自行補完時，或呼叫 /clarify、其他 skill 需要釐清缺口時使用此 skill。主動掃描 spec.md 的覆蓋盲點交由 clarify-over-specs，把答案寫回產物交由呼叫者 skill。
---

## SOP

### Phase 1 --- 收斂提問

1. READ 讀取使用者輸入、呼叫者指示與既有產物，確認澄清主題、提問面向、各面向的題目標籤、每輪題數、題數上限、是否只問一輪與是否詳記問答紀錄。
2. THINK 依 [盤點高影響缺口與提問排序判準](rules/盤點高影響缺口與提問排序判準.md) 盤點輸入中的缺漏、矛盾、模糊與未拍板決策，選出本輪提問。

### Phase 2 --- 提問

1. WRITE 依 [Context與選項題撰寫判準](rules/Context與選項題撰寫判準.md) 與 [clarify-question-round.md](templates/clarify-question-round.md) 與 [clarify-question-round.example.md](templates/clarify-question-round.example.md) 在對話中輸出本輪問題後停止等待回答，呼叫者未指定題目標籤時省略題號後的「 ｜ 」與標籤。

### Phase 3 --- 收斂回答

1. READ 讀取使用者對本輪問題的回答。
2. ASK 依 [回答解讀判準](rules/回答解讀判準.md) 追問無法明確對應選項的回答。
3. WRITE 呼叫者要求詳記問答紀錄時，依 [clarify-log.md](templates/clarify-log.md) 與 [clarify-log.example.md](templates/clarify-log.example.md) 更新問答紀錄。
4. THINK 仍有高影響缺口、累計題數未達題數上限且呼叫者未指定只問一輪時回到 Phase 1；否則把已確認決策、使用者補充與剩餘風險交還呼叫者 skill。
