# 开源发布 checklist（自有 GitHub 仓库）

## 1. 本地目录怎么放（不用大改）

**Git 仓库根目录 = 内层** `SenseNova-Skills/SenseNova-Skills/`（含 `pyproject.toml`、`sn_studio/`、`skills/`）。

```text
D:\github\SenseNova-Skills\          ← 仅本地父文件夹，不要在这里 git init
└── SenseNova-Skills\                ← REPO_ROOT，所有 git / pip / python -m sn_studio 在这里
    ├── skills/                      ← 官方技能包（同源）
    ├── sn_studio/                   ← 你开发的 Studio
    ├── openspec/
    ├── docs/
    ├── scripts/
    ├── pyproject.toml
    └── .env                         ← 本地 only，不提交
```

不必把 `sn_studio` 挪到仓库外；当前结构已与 Python 包、`skills/` 调用路径一致。

若嫌双层目录名绕，可把整个内层**移动**为例如 `D:\github\SenseNova-Skills-Studio\`，只要移动后仍保留 `skills/` 与 `sn_studio/` 同级即可。

---

## 2. GitHub 上创建「自己的仓库」

1. 登录 GitHub → **New repository**  
2. 名称示例：`SenseNova-Skills-Studio` 或 `SenseNova-Skills`  
3. **Public**，**不要**勾选自动生成 README（避免冲突）  
4. 创建后记下：`https://github.com/<你的用户名>/<仓库名>.git`

README 顶部应保留指向官方的说明，本仓库已提供 [UPSTREAM.md](../../UPSTREAM.md)。

---

## 3. 配置远程（保留官方为 upstream）

在 **REPO_ROOT** 执行：

```powershell
cd D:\github\SenseNova-Skills\SenseNova-Skills

# 原官方地址改名为 upstream
git remote rename origin upstream

# 你的新仓库
git remote add origin https://github.com/<你的用户名>/<仓库名>.git

git remote -v
# origin    -> 你的仓库
# upstream  -> OpenSenseNova/SenseNova-Skills
```

---

## 4. 提交哪些、不提交哪些

### ✅ 应该提交

| 路径 | 说明 |
|------|------|
| `sn_studio/` | Studio 全部代码 |
| `openspec/` | 产品/架构规格 |
| `scripts/` | `install_studio.ps1`、`smoke_studio.py` |
| `tests/` | 根目录集成测试 |
| `sn_studio/tests/` | 单元测试 |
| `docs/studio/`、`docs/promo/` | 文档与推广（含已生成 PNG） |
| `pyproject.toml`、`requirements-studio.txt` | 包定义 |
| `.env.example` | 配置模板（无真实 Key） |
| `README_CN_STUDIO.md`、`CONTRIBUTING.md`、`UPSTREAM.md` | 说明与上游声明 |
| `README.md`、`README_CN.md` | 含 Studio 入口的改动 |
| `.gitignore` | 忽略规则 |
| `outputs/.gitkeep`、`outputs/README.md` | 说明产物目录，不含个人文件 |
| `skills/...` 中**你改过的文件** | 如 configs、doctor、tests（与 Studio 联调相关） |

### ❌ 不要提交

| 路径 | 原因 |
|------|------|
| `.env` | 含 API Key |
| `outputs/studio/**`、PNG、jobs.json | 个人生成物 |
| `ppt_decks/`、`research/` | 本地任务 |
| `*.egg-info/`、`.venv/` | 构建/环境 |
| `sn_skills_studio.egg-info/` | pip install -e 生成 |

提交前执行：`git status`，确认列表里没有 `.env` 和 `outputs/studio`。

---

## 5. 推荐提交命令（一次性）

```powershell
cd D:\github\SenseNova-Skills\SenseNova-Skills

git add .gitignore .env.example UPSTREAM.md CONTRIBUTING.md
git add README.md README_CN.md README_CN_STUDIO.md
git add pyproject.toml requirements-studio.txt
git add sn_studio/ openspec/ scripts/ tests/
git add docs/studio/ docs/promo/
git add outputs/.gitkeep outputs/README.md

git add skills/sn-image-base/scripts/sn_image_base/configs.py
git add skills/sn-image-base/scripts/sn_image_base/utils/httpx_client.py
git add skills/sn-image-base/scripts/tests/
git add skills/sn-image-doctor/scripts/check_environment.py

git status
# 再检查：不应出现 .env、outputs/studio、*.egg-info

git commit -m "feat(studio): add SenseNova Skills Studio local control panel

- Gradio UI (sn_studio) for image/PPT/excel/research/search
- openspec, docs, install scripts
- upstream: OpenSenseNova/SenseNova-Skills
- fix empty optional API key fallback for image generation"

git branch -M main
git push -u origin main
```

---

## 6. 推送后 GitHub 仓库设置

- **About**：Description 写「基于 OpenSenseNova/SenseNova-Skills，提供 sn_studio 本地控制面板」  
- **Website**：`https://platform.sensenova.cn/console/keys`  
- **Topics**：`sensenova`, `agent-skills`, `gradio`, `image-generation`  
- 在 README 置顶或 About 中再次链接官方仓库  

---

## 7. 与官方的关系说明（给用户看的三句话）

建议在 README 最上方或 Studio 章节写清：

1. 本仓库 fork/扩展自 [OpenSenseNova/SenseNova-Skills](https://github.com/OpenSenseNova/SenseNova-Skills)。  
2. **新增** `sn_studio` 本地 Web 控制台；`skills/` 与官方技能兼容。  
3. API Key 在 [商汤控制台](https://platform.sensenova.cn/console/keys) 申请，本地 `.env` 配置。

详见 [UPSTREAM.md](../../UPSTREAM.md)。
