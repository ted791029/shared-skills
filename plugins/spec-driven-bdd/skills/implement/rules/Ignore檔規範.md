# Ignore 檔規範

## Rule 1 -- 依現有檔案與 techstack.md 偵測需要的 ignore 檔

**強度：MUST**

依下表偵測需要的 ignore 檔，偵測依據包含專案中已存在的檔案，以及 techstack.md 與 plan.md 選用的技術；實作尚未開始時專案多半是空的，必須以 techstack.md 與 plan.md 為主要依據。不得建立表中條件都不成立的 ignore 檔。

| 條件 | ignore 檔 |
|---|---|
| `git rev-parse --git-dir` 成功 | `.gitignore` |
| 存在 `Dockerfile*`，或 plan.md／techstack.md 選用 Docker | `.dockerignore` |
| 存在 `.eslintrc*` | `.eslintignore` |
| 存在或將建立 `eslint.config.*` | 不建 ignore 檔，改為確認 config 的 `ignores` 涵蓋必要 pattern |
| 存在 `.prettierrc*`，或 techstack.md 選用 Prettier | `.prettierignore` |
| `package.json` 未設 `"private": true` 且要發佈到 npm | `.npmignore` |
| 存在 `*.tf` | `.terraformignore` |
| 存在 Helm chart | `.helmignore` |

### Good Example

這個範例依專案現況與 techstack.md 逐條比對，條件都不成立，因此不建立任何 ignore 檔。

```text
git rev-parse --git-dir → fatal: not a git repository → 不建 .gitignore（既有 backend/.gitignore、frontend/.gitignore 不動）
沒有 Dockerfile*，plan.md／techstack.md 未選用 Docker（docker-compose.yml 只啟動測試用 MySQL）→ 不建 .dockerignore
techstack.md › 開發工具 選用 oxlint，沒有 .eslintrc*、eslint.config.*、.prettierrc* → 不建 .eslintignore、.prettierignore
frontend/package.json "private": true → 不建 .npmignore
```

### Bad Example

這個範例沒有逐條比對，依前端專案的習慣建立 `.gitignore` 與 `.prettierignore`；專案不是 git repo、也沒有選用 Prettier，兩個檔案都不會被任何工具讀取，完成報告卻列為已建立，讓人以為建置產物已被排除。

```text
前端專案通常有 Git 與 Prettier → 建立 .gitignore、frontend/.prettierignore
```

## Rule 2 -- 由任務建立的 ignore 檔交給該任務

**強度：MUST**

tasks.md 中有任務建立或修改某個 ignore 檔或 `eslint.config.*` 時，此階段不得先建立它。執行該任務時，先寫入任務指定的內容，再補上 Rule 4 對照表中缺少的 pattern；任務指定的 pattern 不得刪除或改寫。

### Good Example

這個範例的 T003 指定在 `frontend/.gitignore` 加入測試產物，此階段跳過，執行 T003 時先寫入任務內容再補缺少的 pattern。

```text
Phase 2：frontend/.gitignore 由 T003 修改 → 跳過
T003：追加 test-results/、.features-gen/（任務指定），補上 build/、.env*、.DS_Store、Thumbs.db
```

### Bad Example

這個範例在此階段先把 Node.js 與 Universal pattern 全集寫入 `frontend/.gitignore`，執行 T003 時又整份重寫成任務指定的內容，先前補的 pattern 被覆蓋，`.env*` 不再被忽略。

```text
Phase 2：frontend/.gitignore 追加 Node.js 與 Universal pattern 全集
T003：重寫 frontend/.gitignore（node_modules、dist、reports、test-results/、.features-gen/）→ 覆寫
```

## Rule 3 -- 既有 ignore 檔只追加缺少的 pattern

**強度：MUST**

ignore 檔已存在時，只能在檔尾追加 Rule 4 對照表中缺少的關鍵 pattern，不得刪除、改寫或重新排序既有的行。ignore 檔不存在時，以對照表中適用技術的完整 pattern 建立。

### Good Example

這個範例只在既有 `backend/.gitignore` 檔尾追加 Python 與 Universal 中缺少的 pattern，既有行的順序不變。

```text
既有：reports/、.env、__pycache__/、.venv/、*.pyc
追加：venv/、dist/、*.egg-info/、.DS_Store、Thumbs.db、*.tmp、*.swp、.vscode/、.idea/
```

### Bad Example

這個範例用對照表整份取代既有的 `backend/.gitignore`，既有的 `.env` 被刪除，對照表的 Python 列又沒有 `.env`，含資料庫密碼的 `backend/.env` 從此不再被忽略。

```text
以 Python 與 Universal pattern 全集覆寫 backend/.gitignore
```

## Rule 4 -- pattern 依 techstack.md 選用的技術取自對照表

**強度：MUST**

pattern 只能取自下表中 techstack.md 選用的語言與工具，以及 Universal；不得加入未選用技術的 pattern。

| 技術 | pattern |
|---|---|
| Node.js／JavaScript／TypeScript | `node_modules/`、`dist/`、`build/`、`*.log`、`.env*` |
| Python | `__pycache__/`、`*.pyc`、`.venv/`、`venv/`、`dist/`、`*.egg-info/` |
| Java | `target/`、`*.class`、`*.jar`、`.gradle/`、`build/` |
| C#／.NET | `bin/`、`obj/`、`*.user`、`*.suo`、`packages/` |
| Go | `*.exe`、`*.test`、`vendor/`、`*.out` |
| Ruby | `.bundle/`、`log/`、`tmp/`、`*.gem`、`vendor/bundle/` |
| PHP | `vendor/`、`*.log`、`*.cache`、`*.env` |
| Rust | `target/`、`debug/`、`release/`、`*.rs.bk`、`*.rlib`、`*.prof*`、`.idea/`、`*.log`、`.env*` |
| Kotlin | `build/`、`out/`、`.gradle/`、`.idea/`、`*.class`、`*.jar`、`*.iml`、`*.log`、`.env*` |
| C++ | `build/`、`bin/`、`obj/`、`out/`、`*.o`、`*.so`、`*.a`、`*.exe`、`*.dll`、`.idea/`、`*.log`、`.env*` |
| C | `build/`、`bin/`、`obj/`、`out/`、`*.o`、`*.a`、`*.so`、`*.exe`、`*.dll`、`autom4te.cache/`、`config.status`、`config.log`、`.idea/`、`*.log`、`.env*` |
| Swift | `.build/`、`DerivedData/`、`*.swiftpm/`、`Packages/` |
| R | `.Rproj.user/`、`.Rhistory`、`.RData`、`.Ruserdata`、`*.Rproj`、`packrat/`、`renv/` |
| Universal | `.DS_Store`、`Thumbs.db`、`*.tmp`、`*.swp`、`.vscode/`、`.idea/` |
| Docker | `node_modules/`、`.git/`、`Dockerfile*`、`.dockerignore`、`*.log*`、`.env*`、`coverage/` |
| ESLint | `node_modules/`、`dist/`、`build/`、`coverage/`、`*.min.js` |
| Prettier | `node_modules/`、`dist/`、`build/`、`coverage/`、`package-lock.json`、`yarn.lock`、`pnpm-lock.yaml` |
| Terraform | `.terraform/`、`*.tfstate*`、`*.tfvars`、`.terraform.lock.hcl` |
| Kubernetes／k8s | `*.secret.yaml`、`secrets/`、`.kube/`、`kubeconfig*`、`*.key`、`*.crt` |

`.env*` 會連帶忽略 `.env.example`；專案需要提交 `.env.example` 時，必須同時加上 `!.env.example`。

### Good Example

這個範例的 techstack.md 選用 Python（backend）與 Node.js（frontend），`frontend/.gitignore` 只取 Node.js 與 Universal，並保留 `.env.example`。

```text
node_modules/
dist/
build/
*.log
.env*
!.env.example
.DS_Store
Thumbs.db
*.tmp
*.swp
.vscode/
.idea/
```

### Bad Example

這個範例把所有語言的 pattern 都加入 `frontend/.gitignore`，Go 的 `vendor/` 與 C 的 `bin/` 可能誤忽略日後真正需要提交的目錄，`.env*` 沒有搭配 `!.env.example`，前端的環境變數範本也無法提交。

```text
node_modules/
vendor/
bin/
target/
.env*
```
