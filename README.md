# shared-skills

共用 skill 的 plugin repo。每個模組是一個 plugin，可以只安裝需要的；同一份 skill 同時提供給 Claude Code、Cursor 與 Codex。

## Plugin

| Plugin | 用途 | 需要另外安裝 |
| --- | --- | --- |
| `skill-workshop` | 建立與優化 skill 的工作流（9 個 skill） | `requirement-clarify` plugin、`uv` |
| `requirement-clarify` | 以選項題訪談使用者，釐清需求缺口（1 個 skill） | 無 |
| `spec-driven-bdd` | 以規格驅動（SDD）規劃、以 BDD 實作，從功能規格到通過測試的開發工作流（19 個 skill） | `requirement-clarify`、`skill-workshop`、`ui-studio` plugin、`uv` |
| `ui-studio` | 設計前端畫面，產出原型、設計系統、修改規格與素材，不修改專案程式碼（2 個 skill） | `uv`（實測時另需 Chromium，第一次使用時會詢問是否安裝） |

沒有 `clarify`（沒裝 `requirement-clarify`，同層也沒有 `clarify` 資料夾）時，下表呼叫 `clarify` 的 skill 會在該步驟停下來提示取得方式，其他 skill 不受影響。沒有 `ui-design`（沒裝 `ui-studio`，同層也沒有 `ui-design` 資料夾）時，`ui-direction` 與 `ui-ux-plan` 撰寫原型的步驟同樣會停下來。

### 跨 plugin 呼叫

`skill_graph.py` 只檢查連結，檢查不到這裡列的名稱呼叫。新增或移除時請更新此表。

| 呼叫者 | 被呼叫者 |
| --- | --- |
| `skill-workshop` 的 `artifact-to-skill-engineering` | `requirement-clarify` plugin 的 `clarify` |
| `spec-driven-bdd` 的 `specify` | `requirement-clarify` plugin 的 `clarify` |
| `spec-driven-bdd` 的 `clarify-over-specs` | `requirement-clarify` plugin 的 `clarify` |
| `spec-driven-bdd` 的 `spec-by-example` | `requirement-clarify` plugin 的 `clarify` |
| `spec-driven-bdd` 的 `technical-research` | `requirement-clarify` plugin 的 `clarify` |
| `spec-driven-bdd` 的 `system-analysis` | `requirement-clarify` plugin 的 `clarify` |
| `spec-driven-bdd` 的 `constitution` | `requirement-clarify` plugin 的 `clarify` |
| `spec-driven-bdd` 的 `planner-provisioning` | `skill-workshop` plugin 的 `artifact-to-skill-engineering` |
| `spec-driven-bdd` 的 `ui-direction` | `ui-studio` plugin 的 `ui-design` |
| `spec-driven-bdd` 的 `ui-ux-plan` | `ui-studio` plugin 的 `ui-design` |

被其他 plugin 呼叫的 skill 不可設定 `disable-model-invocation: true`，否則 Claude Code 會拒絕呼叫。

## 支援狀態

| Agent | 狀態 |
| --- | --- |
| Claude Code | 已從本機資料夾實測安裝與載入；從 git 安裝未實測 |
| Cursor | 未實測，設定檔依官方文件撰寫 |
| Codex | 未實測，設定檔依官方文件撰寫 |

## 安裝與更新

以下 `<repo>` 換成本 repo 的 git 網址，或 clone 到本機的資料夾路徑。

### Claude Code

```bash
claude plugin marketplace add <repo>
claude plugin install skill-workshop@shared-skills
claude plugin install requirement-clarify@shared-skills
claude plugin install spec-driven-bdd@shared-skills
claude plugin install ui-studio@shared-skills
```

更新後要重新啟動 Claude Code：

```bash
claude plugin marketplace update shared-skills
claude plugin update skill-workshop@shared-skills
claude plugin update requirement-clarify@shared-skills
claude plugin update spec-driven-bdd@shared-skills
claude plugin update ui-studio@shared-skills
```

呼叫範例：`/skill-workshop:skill-engineering`、`/requirement-clarify:clarify`、`/spec-driven-bdd:specify`、`/ui-studio:ui-design`

### Cursor（未實測）

- 團隊：在 Dashboard 的 Plugins & MCPs 進入 Team Marketplaces，以 Import from Repo 匯入本 repo。
- 個人：把要用的 `plugins/<plugin>` 複製到 `~/.cursor/plugins/local/<plugin>`，再執行 Developer: Reload Window。

### Codex（未實測）

```bash
codex plugin marketplace add <repo>
```

接著在 Codex 輸入 `/plugins` 安裝。更新時執行 `codex plugin marketplace upgrade`。

### 不支援 plugin 的 agent

把 `plugins/*/skills/` 底下的 skill 資料夾全部複製到該 agent 的 skill 目錄，並放在**同一層**：

```text
<skill 目錄>/
├── artifact-to-skill-engineering/
├── clarify/
├── skill-derive-rule/
└── ……
```

- 只有 `clarify`、4 個 `skill-form-*`、`bdd`、`truth-changes` 與 `constitution` 沒有連到同層的 skill；`ui-design` 與 `ui-assets` 互相連結，必須一起複製；其他 skill 單獨複製時連結會失效。`bdd` 等工作流中的 skill 仍需要上游 skill 的產出。
- `clarify` 要用本 repo 這份。設定了 `disable-model-invocation: true` 的版本在 Claude Code 無法被其他 skill 呼叫。
- 不要同時安裝 plugin 又放複製版；複製版不會跟著更新，更新時要重新複製。

## 維護規則

- 只改本 repo 的 `plugins/<plugin>/skills/`，不改各 agent 的安裝副本。
- 設定檔不寫 `version`，Claude Code 以 commit SHA 當版本。`claude plugin validate` 的 version 警告可以忽略。
- `script-執行規範.md` 在 `skill-engineering`、`skill-form-script` 與 `spec-driven-bdd` 的 15 個 skill 與 `ui-design` 各有一份，內容必須相同。
- `spec-driven-bdd` 新增 Planner（`<前綴>-plan`）時，放在本 repo 的 `plugins/spec-driven-bdd/skills/`，更新 plugin 後才能使用。
- 同一個 plugin 內的 skill 用相對連結，不同 plugin 用名稱呼叫。
- 新增模組時，在 `plugins/` 建立 plugin 資料夾，並在 `.claude-plugin/`、`.cursor-plugin/`、`.agents/plugins/` 的 `marketplace.json` 各加一筆。
- 不要把其他 repo 的 marketplace 也取名 `shared-skills`；重複時 Claude Code 會用後加的蓋掉先加的，不會警告。

驗證：

```bash
claude plugin validate .
claude plugin validate plugins/skill-workshop
claude plugin validate plugins/requirement-clarify
claude plugin validate plugins/spec-driven-bdd
claude plugin validate plugins/ui-studio
uv run plugins/skill-workshop/skills/skill-engineering/scripts/skill_graph.py plugins/skill-workshop/skills --issues-only
uv run plugins/skill-workshop/skills/skill-engineering/scripts/skill_graph.py plugins/requirement-clarify/skills --issues-only
uv run plugins/skill-workshop/skills/skill-engineering/scripts/skill_graph.py plugins/spec-driven-bdd/skills --issues-only
uv run plugins/skill-workshop/skills/skill-engineering/scripts/skill_graph.py plugins/ui-studio/skills --issues-only
```
