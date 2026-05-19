# SenseNova Skills：为商汤日日新 U1 打造的办公技能包

> 围绕 **`sensenova-u1-fast`（SenseNova U1）** 与配套 **sn-\*** 技能；在 Agent 或 **SenseNova Skills Studio** 中本地调用（[申请 API Key](https://platform.sensenova.cn/console/keys)）。  
> **仓库**：[OpenSenseNova/SenseNova-Skills](https://github.com/OpenSenseNova/SenseNova-Skills) · MIT 协议

---

过去两年，大模型能力的竞争焦点从「能不能答对一题」转向「能不能把一件事做完」。在真实办公场景里，用户很少只需要一段流畅的文字——他们需要：
**SenseNova U1** 是商汤日日新体系里的**文生图模型**，在开放平台上的常用模型 ID 为 **`sensenova-u1-fast`**（快速版，适合批量出图与 Studio 交互场景）。通过 [SenseNova 开放平台](https://platform.sensenova.cn) 的 API（`https://token.sensenova.cn/v1`）即可调用，与对话、识图共用同一套 **`SN_API_KEY`**（在 [控制台 · Keys](https://platform.sensenova.cn/console/keys) 创建）。
- 一份**能发给老板**的 PPT，版式统一、配图合理、页与页之间叙事连贯；
- 一张**能进汇报材料**的 Excel 分析表，大文件不 OOM、结论有图表支撑；
- 一篇**能经得起追问**的行业报告，来源可追溯、数字冲突要先 reconcile 再落稿；
- 一张**能直接传播**的信息图，不是「随便画一张」，而是布局、风格、文字可读性都过关。

这些任务有一个共同特征：**步骤长、约束多、中间产物必须落盘**。只靠通用 Chat 或单次 API 调用，智能体很容易在第三步「即兴发挥」：用 `pd.read_excel()` 硬读十万行、搜三条网页就写尽调、PPT 每页风格漂移。问题不在模型不够聪明，而在于**缺少可复用的执行契约**。

## 一、SenseNova U1：生图模型与它能做什么

**SenseNova U1** 是商汤日日新体系里的**文生图模型**，在开放平台上的常用模型 ID 为 **`sensenova-u1-fast`**（快速版，适合批量出图与 Studio 交互场景）。通过 [SenseNova 开放平台](https://platform.sensenova.cn) 的 API（`https://token.sensenova.cn/v1`）即可调用，与对话、识图共用同一套 **`SN_API_KEY`**（在 [控制台 · Keys](https://platform.sensenova.cn/console/keys) 创建）。

**U1 适合产出什么？**

| 场景 | 说明 |
|------|------|
| 营销 / 运营物料 | 海报、横幅、社交媒体配图，支持常见宽高比 |
| 信息图 | 结构化版面 + 图中中文文案（需配合扩写与版式 skill） |
| PPT 创意页 | 每页一整张 16:9 视觉稿（创意模式） |
| 系列图 | 同一风格下的多张分镜（系列批量） |
| 简历视觉稿、风格模仿图 | 固定版式或参考图风格 |

单次调用 U1 API 只能得到「一张按 Prompt 生成的图」。真实办公里还需要：**Prompt 扩写、版式选型、多轮试稿、VLM 质检、文件落盘**——这些由本仓库的 **sn-\*** 技能包在 U1 之上补齐；扩写、规划、识图等环节则使用 **`sensenova-6.7-flash-lite`（SenseNova 6.7）**，与 U1 分工明确：

| 环节 | 默认模型 | 作用 |
|------|----------|------|
| **出图** | `sensenova-u1-fast` | 最终像素交付 |
| **扩写 / 规划 / 成稿** | `sensenova-6.7-flash-lite` | Prompt、大纲、研究报告文字 |
| **识图 / 质检** | `sensenova-6.7-flash-lite` | 图表理解、信息图与 PPT 分页评审 |

---

## 二、SenseNova Skills：U1 的配套技能包，以及怎么用

### 2.1 这是什么

**[SenseNova-Skills](https://github.com/OpenSenseNova/SenseNova-Skills)** 是一组开源 **Agent Skills**（遵循 [agentskills.io](https://agentskills.io/) 规范）：每个技能一个目录 + `SKILL.md`，写清**何时用、怎么用、产物放哪**。它们通过底层 [`sn-image-base`](../../skills/sn-image-base/SKILL.md) 调用商汤 API——**生图走 U1，其余走 6.7**——把模型能力变成可重复执行的工序，而不是聊天里随口一说。

### 2.2 技能清单（按场景）

**图像与可视化（围绕 U1）**

| 技能 | 作用 |
|------|------|
| `sn-image-base` | 底层封装：文生图、识图、文本优化（供其它图像 skill 调用） |
| `sn-image-doctor` | 检查依赖、Key、模型是否可用 |
| `sn-infographic` | 专业信息图：评估 Prompt → 选布局/风格 → 多轮 U1 生成 → VLM 选优 |
| `sn-image-imitate` | 按参考图风格生成新图 |
| `sn-image-resume` | 简历文字 → 简历视觉图 |

**演示文稿（页内素材大量用 U1）**

| 技能 | 作用 |
|------|------|
| `sn-ppt-entry` | 统一入口：收集需求，生成 `task_pack.json` |
| `sn-ppt-standard` | 标准模式：HTML 分页 + VLM 评审 → 导出 PPTX |
| `sn-ppt-creative` | 创意模式：每页一张 U1 全图 PNG |
| `sn-ppt-doctor` | PPT 流水线环境检查 |

**数据分析**

| 技能 | 作用 |
|------|------|
| `sn-da-excel-workflow` | 多 Sheet Excel 清洗、统计、导出（编排器） |
| `sn-da-large-file-analysis` | 十万行级大表流式处理 |
| `sn-da-image-caption` | 从图表截图提取数据 |

**深度研究 + 搜索 + 报告**

| 技能 | 作用 |
|------|------|
| `sn-deep-research` | 总控：规划 → 分维度取证 → 综合 → 成稿 |
| `sn-research-planning` / `sn-dimension-research` / `sn-research-synthesis` / `sn-research-report` | 研究各阶段 |
| `sn-search-academic` / `sn-search-code` / `sn-search-social-cn` / `sn-search-social-en` | 学术、开发者、中英文社交搜索 |
| `sn-report-format-discovery` / `sn-md-to-html-report` | 报告结构发现、MD 转离线 HTML |
| `sn-update` | 在 Agent 环境中更新 sn-\* 包 |

一条完整业务链示例见仓库 `examples/memory-price-end2end-analysis`：Excel 分析 → 深度研究 → PPT 汇报，由多个入口 skill 通过磁盘上的文件交接完成。

### 2.3 怎么使用这些技能

**第一步：拿到 API Key**

在 **[platform.sensenova.cn/console/keys](https://platform.sensenova.cn/console/keys)** 注册并创建 Key，写入仓库根目录 `.env`：

```env
SN_BASE_URL=https://token.sensenova.cn/v1
SN_API_KEY=sk-你的密钥
```

**方式 A — 在智能体里用（适合长流程、可改 skill）**

1. 将 `skills/` 下各目录安装到 Agent 的 skills 路径（如 OpenClaw：`~/.openclaw/skills/`，Cursor：`.cursor/skills/`）。  
2. 重启 Agent，在对话中用自然语言触发，例如：「用 sn-image-doctor 检查环境」「按 sn-infographic 做一张行业信息图」「启动 sn-deep-research 写尽调」。  
3. Agent 会按 `SKILL.md` 调用脚本、读写 `outputs/` 等目录中的产物。

详细安装见 [`INSTALL_CN.md`](../../INSTALL_CN.md)。也可让 Agent 自行克隆仓库：*「请安装 https://github.com/OpenSenseNova/SenseNova-Skills」*。

**方式 B — 不想自己配 Agent？**

[小浣熊](https://office.xiaohuanxiong.com/home) 已集成同源 **U1 + 6.7** 能力与 Cowork-Skill，云端开箱即用。本文重点介绍的开源路径，则适合要**本地保管 Key、改 skill、接 Cursor/OpenClaw** 的团队。

---

**下一节**介绍我们为此开发的 **SenseNova Skills Studio**（`sn_studio`）：在不装 Agent 的情况下，用浏览器完成配 Key、点按钮跑 skill、查看 U1 出图与 Excel/PPT 产物——同一套 sn-\*，多一种**图形化**用法。

---

## 三、SenseNova Skills Studio：Skills 的本地适配工具

### 3.1 它解决什么问题

第二节里的技能包，默认要在 Cursor / OpenClaw 等 Agent 里通过对话触发。**Studio** 面向「想用 U1 和 sn-\*，但不想先搭 Agent」的用户，定位很直接：

> **不改动 `skills/` 里的 SKILL 逻辑，只在上层提供 Gradio 控制面板，把既有脚本变成可配置、可触发、可浏览产物的本地 Web 应用。**

换句话说：技能包定义**工序与验收标准**；Studio 定义**人机界面与任务调度**——二者共用同一套商汤日日新 API 与 `.env` 配置。

### 3.2 使用前：注册 Key，即可本地使用

使用 Studio **不需要**先搭 Agent 运行时。只需：

1. 打开 **[SenseNova 开放平台 · API Keys](https://platform.sensenova.cn/console/keys)** 注册并创建密钥（亦可了解 [Token 套餐](https://platform.sensenova.cn/token-plan)）。  
2. 克隆本仓库，在内层 `REPO_ROOT`（含 `pyproject.toml`）复制 `.env.example` 为 `.env`，填入：

   ```env
   SN_BASE_URL=https://token.sensenova.cn/v1
   SN_API_KEY=sk-你的密钥
   ```

3. 安装并启动 Studio（Windows 可用一键脚本）：

   ```powershell
   cd D:\github\SenseNova-Skills\SenseNova-Skills
   powershell -ExecutionPolicy Bypass -File .\scripts\install_studio.ps1
   python -m sn_studio
   ```

4. 浏览器打开 **http://127.0.0.1:7860** → **设置** Tab 保存并 **测试 API** → 即可在图像、PPT、数据分析等 Tab 调用全部已适配能力。

密钥仅保存在本机 `.env`，界面脱敏显示；推理与生图请求直连 `token.sensenova.cn`，不经过第三方中转。

![SenseNova 控制台 API Keys](screenshot-sensenova-keys.png)

![Studio 设置页：保存 Key 与 API 测试通过](screenshot-studio-settings.png)

### 3.3 Studio 是什么：本地 Web 控制台，不是又一个聊天框

SenseNova Skills Studio 运行在你本机（默认 `http://127.0.0.1:7860`），基于 **Gradio 5** 搭建。它不做「万能对话」，而是把第二节列出的 sn-\* 能力拆成**固定的 Tab + 表单 + 按钮**：

- 该填什么的框都写好标签（Prompt、宽高比、扩写模式、Excel 路径……）  
- 该跑多久的任务交给后台子进程，界面用阶段条告诉你「正在扩写 / 正在用 U1 出图」  
- 该落盘的结果进 `outputs/`，Gallery 里能预览，**本会话历史**里能一键回看  

因此它特别适合：运营、设计、分析同事**不想学 Agent 话术**，但希望**稳定复用**同一套 U1 信息图、系列图、Excel 探查能力的人；也适合开发者**先在本机把 Key 和流水线跑通**，再接到 Cursor 里做长流程编排。

![Studio 主界面：顶栏与各 Tab](screenshot-studio-home.png)

### 3.4 七个 Tab：分别能帮你做什么

| Tab | 你会用到的情况 | 背后调用的能力 |
|-----|----------------|----------------|
| **设置** | 第一次安装、换 Key、确认 U1/6.7 是否可达、跑环境诊断 | `.env` 管理、`sn-image-doctor` / `sn-ppt-doctor` |
| **图像** | 出单张图、信息图、系列图、模仿参考图、简历视觉稿 | U1 + 图像流水线（见 §3.5） |
| **PPT** | 从 brief 建 deck、按阶段生成 HTML/素材、调试某一页 | `sn-ppt-entry`、`sn-ppt-standard` / `sn-ppt-creative` |
| **数据分析** | 上传 Excel 先看有多少 Sheet、多少行，再决定要不要上完整分析 skill | `sn-da-excel-workflow` 探查能力 |
| **深度研究** | 建 `research/` 目录、写 `request.md`、把报告转成 HTML 预览 | `sn-deep-research` 工件约定 |
| **搜索** | 快速查论文、GitHub、知乎/B 站等，结果以表格呈现 | `sn-search-*` 系列 |
| **更新** | 从 Git 拉取最新 sn-\* 技能包 | 仓库 `git pull` |

复杂任务（例如深度研究**全自动**多轮取证、PPT **一口气**生成二十多页）仍建议在 Cursor / OpenClaw 里加载完整 `SKILL.md`；Studio 的定位是**把高频、可点击的能力做到顺手**，而不是替代整个 Agent。

### 3.5 图像 Tab：最值得先体验的一块

图像 Tab 内再分五个子页，共用**左右分栏**布局：左侧输入与参数，右侧预览与会话历史——和常见生图产品一致，降低学习成本。

| 子页 | 你怎么用 | U1 何时介入 |
|------|----------|-------------|
| **文生图** | 写一句中文描述 → 选比例 → 生成 | 扩写完成后调用 U1 |
| **信息图** | 贴业务摘要或要点 → 自动选型版式风格 → 多轮出图并质检 | 多轮 U1 + 6.7 VLM 选优 |
| **系列批量** | **一句话主题** + 选择张数（3–8）→ 自动拆镜、统一风格、批量出图 | 全系列共享 seed，逐张 U1 |
| **风格模仿** | 上传参考图 + 新内容说明 | 识图后 U1 按风格重画 |
| **简历图** | 粘贴简历正文 | 结构化扩写后 U1 出视觉稿 |

生成过程中，右侧**阶段条**会依次提示（例如：分析内容 → 扩写 Prompt → 生成图像）；完成后可在 **「扩写后的 Prompt」** 折叠区查看实际发给 U1 的文案，便于复盘和二次修改。产物除显示在 Gallery 外，还会写入 `outputs/studio/<模块>/<时间戳>/`，本机可用 **「打开输出文件夹」** 直接定位文件。

![文生图：左右分栏 + 完成态预览](screenshot-studio-image-generate.png)

![系列批量：多图预览与会话历史](screenshot-studio-image-series.png)

![信息图：成品预览](screenshot-studio-infographic.png)

### 3.6 其它 Tab 怎么用（简例）

- **PPT**：填写角色、受众、页数，上传 pdf/docx/md 附件 → 生成 `task_pack.json` → 按阶段执行 `run_stage`（例如只跑大纲或只跑某一页素材），在浏览器里看 HTML 预览，产物在 `ppt_decks/`。  
- **数据分析**：指定 xlsx 路径 → 一键探查 Sheet 名与行数；大表会提示是否走 Parquet/流式策略，避免一上来内存爆掉。  
- **深度研究**：创建课题目录、编辑 `request.md`；完整多维度调研仍在 Agent 里跑，Studio 负责**建架子、转 HTML 方便阅读**。  
- **搜索**：选学术 / 代码 / 社交源，输入关键词 → 表格展示脚本返回的标题、链接、摘要，适合写报告前的快速摸底。

![PPT Tab：deck 与阶段运行](screenshot-studio-ppt.png)

![数据分析 Tab：Excel 探查结果](screenshot-studio-excel.png)

![搜索 Tab：学术检索结果表](screenshot-studio-search.png)

### 3.7 和 Agent 一起用时，Studio 扮演什么角色

同一仓库、同一 `.env`、同一套 sn-\*：

| 场景 | 建议用 Studio | 建议用 Cursor / OpenClaw |
|------|---------------|---------------------------|
| 配 Key、测 API、出第一张 U1 图 | ✅ | 可选 |
| 调试信息图 / 系列图参数 | ✅ | 可选 |
| Excel 行数探查、单次搜索 | ✅ | ✅ |
| 行业尽调全流程、PPT 全页循环 | 建目录、单步调试 | ✅ 主编排 |
| 修改 `SKILL.md`、提 PR | — | ✅ |

Studio 是**技能适配层上的图形壳**；Agent 是**对话编排层**。二者互补，不是二选一。

![Cursor 中触发 sn-* 技能（可选对比图）](screenshot-cursor-agent.png)

---

## 四、Studio 如何集成 Skills（技术说明）

### 4.1 集成架构：UI 不侵入 Skill 仓库

Studio 采用**薄适配层**，保证技能包可独立演进、Studio 可单独升级：

```text
浏览器 (Gradio 5)
    ↓
sn_studio/ui          ← Tab、表单、Gallery、任务轮询
    ↓
sn_studio/services/*  ← 参数组装、调用 prompt 流水线
    ↓
sn_studio/core/runner ← 子进程执行 skills/*/scripts 下既有入口
    ↓
skills/<sn-*>/        ← SKILL.md 约定的脚本与产物（不修改）
    ↓
商汤日日新 API        ← U1 生图 / 6.7 推理·VLM（SN_API_KEY）
```

任务状态与输出路径写入 `outputs/.studio_jobs/jobs.json` 与 `outputs/studio/<模块>/`，便于会话内回看与重启后恢复历史（图像系列等目录规范见 `openspec/image-series-one-shot.md`）。

### 4.2 图像流水线契约

五个图像子页共用 `openspec/prompt-pipeline-unified.md` 定义的 **评估 → 扩写 → 生图** 阶段；信息图叠加 `sn-infographic` 的版式/风格选型，系列批量在扩写前增加 **6.7 拆镜** 与 **共享风格块 + 统一 seed**。界面上的阶段条与 `expanded-prompt.txt` 与 skill 脚本写入内容一致，便于对照调试。

### 4.3 产物目录约定

| 路径 | 内容 |
|------|------|
| `outputs/studio/generate/`、`infographic/`、`series/<时间戳>/` 等 | 图像模块输出 |
| `outputs/.studio_jobs/jobs.json` | 任务状态（供本会话历史恢复） |
| `ppt_decks/` | PPT `task_pack` 与分阶段产物 |
| `research/<课题>/` | 深度研究工件 |

---

## 五、展望：Skills 适配层的下一步

1. **更深的一体化预览** — 研究 / PPT / 系列图在 Studio 内直接预览 HTML、manifest 与多图网格，减少跳转资源管理器。  
2. **可选「拆解预览」** — 系列批量、信息图在提交前展示 LLM 拆解的 N 条分镜，可编辑再生成。  
3. **模板市场** — 将 `sn-infographic` 案例画廊、行业报告 `report_shape` 沉淀为 Studio 可选模板。  
4. **团队配置** — 只读分享 `.env` 之外的「工序预设」（扩写模式、默认宽高比、品牌负向词）。  
5. **与 Agent 运行时互认任务** — `jobs.json` 与 Agent 侧工件目录双向索引，Studio 点开即可续跑 Agent 未完成的任务。

无论 Agent 生态如何演进，**Skills 作为「可交付工序」的抽象**不会过时；Studio 的角色，是把这套抽象持续翻译成**普通人也能点得动的本地工具**——而商汤日日新 API 始终是底下那块确定的算力底座。

---

## 六、结语

SenseNova Skills 用 **sn-\*** 技能包把商汤日日新模型浇铸成可审计的办公工序；**SenseNova Skills Studio** 则是这套工序面向本机的 **Skills 适配工具**——注册 [API Key](https://platform.sensenova.cn/console/keys)，写入 `.env`，启动 `python -m sn_studio`，即可在浏览器里调用图像、PPT、Excel、研究与搜索能力，无需先学会在 IDE 里 `@skill`。

若你已在用 Cursor 或 OpenClaw，Studio 是最佳的**配环境、试 API、看产物**伴侣；若你只想先把一张 U1 图、一张信息图或一份 Excel 探查跑通，Studio  alone 就足够。技能包开源可改，适配工具持续迭代——欢迎 Star、Issue 与 PR。

---

## 附录 A：实机截图清单

正文 §3 已预留 `![说明](文件名.png)` 占位，将截图放入 `docs/promo/` 同名文件即可显示。

| 文件名 | 建议内容 |
|--------|----------|
| `screenshot-sensenova-keys.png` | [控制台 Keys](https://platform.sensenova.cn/console/keys)（密钥打码） |
| `screenshot-studio-settings.png` | 设置页 API 测试通过 |
| `screenshot-studio-home.png` | Studio 全部 Tab |
| `screenshot-studio-image-generate.png` | 文生图完成态 |
| `screenshot-studio-image-series.png` | 系列批量多图 |
| `screenshot-studio-infographic.png` | 信息图成品 |
| `screenshot-studio-ppt.png` | PPT 单阶段 |
| `screenshot-studio-excel.png` | Excel 探查 |
| `screenshot-studio-search.png` | 学术搜索表格 |
| `screenshot-cursor-agent.png` | （可选）Cursor 触发 skill |

## 附录 B：核心 sn-\* 技能索引（24 个顶层 SKILL）

| 技能名 | 一句话 |
|--------|--------|
| `sn-image-base` | 调用 SenseNova API：U1 文生图 / 6.7 VLM·LLM（Tier 0） |
| `sn-image-doctor` | 图像环境诊断 |
| `sn-infographic` | 专业信息图（布局×风格×多轮质检） |
| `sn-image-imitate` | 参考图风格模仿 |
| `sn-image-resume` | 简历视觉稿 |
| `sn-ppt-entry` | PPT 统一入口与 task_pack |
| `sn-ppt-doctor` | PPT 环境诊断 |
| `sn-ppt-standard` | HTML 分页 + VLM + PPTX |
| `sn-ppt-creative` | 每页整图创意模式 |
| `sn-da-excel-workflow` | Excel 全流程编排 |
| `sn-da-large-file-analysis` | 十万行级流式分析 |
| `sn-da-image-caption` | 图表/截图数据提取 |
| `sn-deep-research` | 深度研究总控 |
| `sn-research-planning` | 产出 plan.json |
| `sn-dimension-research` | 单维度取证 |
| `sn-research-synthesis` | 综合判断 synthesis.md |
| `sn-research-report` | 终稿 report.md |
| `sn-report-format-discovery` | 报告形态发现 |
| `sn-md-to-html-report` | Markdown → 离线 HTML |
| `sn-search-academic` | 学术搜索聚合 |
| `sn-search-code` | 开发者搜索聚合 |
| `sn-search-social-cn` | 中文社交搜索 |
| `sn-search-social-en` | 英文社交搜索 |
| `sn-update` | 技能包更新 |

---

*文档版本：2026-05-18 · 以 Studio 技能适配工具为主线*
