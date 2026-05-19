# SenseNova Skills Studio

**[English](README.md)** · 上游技能包 **[README_CN.md](README_CN.md)**

SenseNova Skills Studio（`sn_studio`）是 **sn-\* 技能包的本地图形适配工具**：在浏览器中配置商汤日日新 API、点击运行既有 skill 脚本、预览 U1 出图与 Excel/PPT 等产物，**无需**先安装 OpenClaw / Cursor。

| 项目 | 说明 |
|------|------|
| **模型** | 生图默认 **SenseNova U1**（`sensenova-u1-fast`）；扩写 / 识图默认 **SenseNova 6.7**（`sensenova-6.7-flash-lite`） |
| **API** | [开放平台](https://platform.sensenova.cn) · [创建 Key](https://platform.sensenova.cn/console/keys) |
| **协议** | 与主仓库相同（MIT） |

---

## 快速开始

### 1. 获取 API Key

1. 打开 [platform.sensenova.cn/console/keys](https://platform.sensenova.cn/console/keys) 注册并创建密钥。  
2. 在**仓库根目录**（含 `pyproject.toml` 的目录）复制配置：

   ```powershell
   copy .env.example .env
   # 编辑 .env，填入 SN_API_KEY=sk-...
   ```

### 2. 安装

> **目录说明**：若克隆后出现双层 `SenseNova-Skills/SenseNova-Skills/`，所有命令均在**内层**执行（下文称 `REPO_ROOT`）。

**一键安装（Windows，推荐）**

```powershell
cd REPO_ROOT
powershell -ExecutionPolicy Bypass -File .\scripts\install_studio.ps1
```

**手动安装**

```powershell
cd REPO_ROOT
python -m pip install --upgrade pip
python -m pip install -r .\skills\sn-image-base\requirements.txt
python -m pip install -r .\requirements-studio.txt -e .
```

自检：

```powershell
python -c "from sn_studio.ui.app import build_app; build_app(); print('OK')"
```

### 3. 启动

```powershell
python -m sn_studio
```

浏览器访问 **http://127.0.0.1:7860** → **设置** Tab 保存并 **测试 API** → 在 **图像** 等 Tab 使用能力。

可选参数：`python -m sn_studio --port 7861 --theme light`

---

## 功能概览

| Tab | 能力 | 对应技能 |
|-----|------|----------|
| **设置** | Key 配置（脱敏）、API 测试、环境诊断 | `sn-image-doctor` / `sn-ppt-doctor` |
| **图像** | 文生图、信息图、系列批量、风格模仿、简历图 | `sn-image-base`、`sn-infographic` 等 |
| **PPT** | 创建 deck、单阶段 `run_stage`、预览产物 | `sn-ppt-entry`、`sn-ppt-standard` / `creative` |
| **数据分析** | Excel Sheet/行数探查、图表 Caption | `sn-da-excel-workflow`、`sn-da-image-caption` |
| **深度研究** | 创建 `research/`、`request.md`、MD→HTML | `sn-deep-research` 工件约定 |
| **搜索** | 学术 / 代码 / 中英文社交 | `sn-search-*` |
| **更新** | `git pull` 同步技能包 | — |

**图像 Tab** 采用左右分栏：左侧输入与参数，右侧阶段条、结果预览、本会话历史；详见 [`openspec/image-studio-layout-lr.md`](openspec/image-studio-layout-lr.md)。

**系列批量**：一句话主题 + 张数 3–8，自动拆镜并统一风格，产物在 `outputs/studio/series/<时间戳>/`。

---

## 项目结构

```text
sn_studio/
├── core/           # 配置、路径、任务队列、子进程 runner
├── services/       # 图像 / PPT / 数据 / 研究 / 搜索
├── ui/             # Gradio 应用与组件
└── tests/          # 单元测试

openspec/           # 产品与架构规格
scripts/            # 安装与冒烟脚本
docs/studio/        # 文档索引
docs/promo/         # 推广文章
```

完整说明见 [`docs/studio/README.md`](docs/studio/README.md)。

---

## 本地产物目录

运行后写入 **`outputs/`**（已 Git 忽略，勿提交个人生成内容）：

| 路径 | 内容 |
|------|------|
| `outputs/studio/` | 图像、探表等 |
| `outputs/.studio_jobs/jobs.json` | 任务状态与会话历史 |
| `ppt_decks/` | PPT 任务包 |
| `research/` | 深度研究目录 |

说明见 [`outputs/README.md`](outputs/README.md)。

---

## 与 Agent 的关系

| 场景 | Studio | Cursor / OpenClaw |
|------|--------|-------------------|
| 配 Key、测 API、出图、探表 | ✅ | 可选 |
| 深度研究全流程、PPT 全页自动循环 | 建目录、单步调试 | ✅ 主编排 |
| 修改 `SKILL.md` | — | ✅ |

Studio **不修改** `skills/` 内脚本，仅通过 `core/runner.py` 子进程调用。

---

## 开发

```powershell
# 单元测试
python -m unittest discover -s sn_studio/tests -v

# 冒烟（需已配置 .env）
python scripts/smoke_studio.py
```

规格与 ADR：[`openspec/`](openspec/)。

---

## 故障排除

| 现象 | 处理 |
|------|------|
| 找不到 `skills\sn-image-base\requirements.txt` | 确认 `cd` 到含 `pyproject.toml` 的 `REPO_ROOT` |
| `HfFolder` ImportError | 重装 `requirements-studio.txt`（需 Gradio ≥ 5.12） |
| 图像环境检查失败、已配 Key 仍报错 | 删除 `.env` 中空的 `SN_IMAGE_GEN_API_KEY=` 等行；设置页保存一次 |
| 生图失败 | 设置 → 图像环境诊断；确认 [Keys](https://platform.sensenova.cn/console/keys) 有效 |
| 搜索失败 | `pip install -r skills/sn-search-academic/requirements.txt`（其它搜索 skill 同理） |
| 预览空白 | 看 `outputs/studio/` 是否已有 PNG；点本会话历史缩略图重载 |

---

## 相关链接

- 推广介绍：[docs/promo/sensenova-skills-promo.md](docs/promo/sensenova-skills-promo.md)
- 贡献说明：[CONTRIBUTING.md](CONTRIBUTING.md)
- **上游官方仓库**：[OpenSenseNova/SenseNova-Skills](https://github.com/OpenSenseNova/SenseNova-Skills)（详见 [UPSTREAM.md](UPSTREAM.md)）
