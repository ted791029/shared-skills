# shared-skills

共用 skill 的 plugin repo。每個模組是一個 plugin，可以只安裝需要的；同一份 skill 同時提供給 Claude Code、Cursor 與 Codex。

## Plugin

| Plugin | 用途 | 需要另外安裝 |
| --- | --- | --- |
| `skill-workshop` | 建立與優化 skill 的工作流（9 個 skill） | `requirement-clarify` plugin、`uv` |
| `requirement-clarify` | 以選項題訪談使用者，釐清需求缺口（1 個 skill） | 無 |

沒裝 `requirement-clarify` 時，只有 `artifact-to-skill-engineering` 的客製化步驟會停下來提示安裝，其他 skill 不受影響。

### 跨 plugin 呼叫

`skill_graph.py` 只檢查連結，檢查不到這裡列的名稱呼叫。新增或移除時請更新此表。

| 呼叫者 | 被呼叫者 |
| --- | --- |
| `skill-workshop` 的 `artifact-to-skill-engineering` | `requirement-clarify` plugin 的 `clarify` |

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
```

更新後要重新啟動 Claude Code：

```bash
claude plugin marketplace update shared-skills
claude plugin update skill-workshop@shared-skills
claude plugin update requirement-clarify@shared-skills
```

呼叫範例：`/skill-workshop:skill-engineering`、`/requirement-clarify:clarify`

### Cursor（未實測）

- 團隊：在 Dashboard 的 Plugins & MCPs 進入 Team Marketplaces，以 Import from Repo 匯入本 repo。
- 個人：把要用的 `plugins/<plugin>` 複製到 `~/.cursor/plugins/local/<plugin>`，再執行 Developer: Reload Window。

### Codex（未實測）

```bash
codex plugin marketplace add <repo>
```

接著在 Codex 輸入 `/plugins` 安裝。更新時執行 `codex plugin marketplace upgrade`。

## 維護規則

- 只改本 repo 的 `plugins/<plugin>/skills/`，不改各 agent 的安裝副本。
- 設定檔不寫 `version`，Claude Code 以 commit SHA 當版本。`claude plugin validate` 的 version 警告可以忽略。
- `script-執行規範.md` 在 `skill-engineering` 與 `skill-form-script` 各有一份，內容必須相同。
- 同一個 plugin 內的 skill 用相對連結，不同 plugin 用名稱呼叫。
- 新增模組時，在 `plugins/` 建立 plugin 資料夾，並在 `.claude-plugin/`、`.cursor-plugin/`、`.agents/plugins/` 的 `marketplace.json` 各加一筆。
- 不要把其他 repo 的 marketplace 也取名 `shared-skills`；重複時 Claude Code 會用後加的蓋掉先加的，不會警告。

驗證：

```bash
claude plugin validate .
claude plugin validate plugins/skill-workshop
claude plugin validate plugins/requirement-clarify
uv run plugins/skill-workshop/skills/skill-engineering/scripts/skill_graph.py plugins/skill-workshop/skills --issues-only
uv run plugins/skill-workshop/skills/skill-engineering/scripts/skill_graph.py plugins/requirement-clarify/skills --issues-only
```
