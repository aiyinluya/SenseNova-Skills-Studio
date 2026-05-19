# 架构决策记录（ADR）

## ADR-001：UI 框架选用 Gradio

**状态**：已接受  

**背景**：需 Windows 下一键启动、文件上传、图片预览、表格结果；团队希望快速覆盖 8 个 Tab。  

**决策**：Gradio 4.x，入口 `python -m sn_studio`。  

**备选**：Streamlit（状态管理繁琐）、NiceGUI（学习曲线）、FastAPI+React（交付周期长）。  

**后果**：定制布局弱于 React；但满足 v1「尽可能完整暴露能力」。

---

## ADR-002：不内嵌 Agent 循环

**状态**：已接受  

**背景**：`sn-deep-research`、`sn-ppt-standard` 依赖多轮 LLM 工具调用，SKILL 面向 Cursor Agent。  

**决策**：Studio 提供 **输入工件 + 单脚本阶段 + 目录浏览**；完整编排仍用 Agent。  

**后果**：PPT/研究 Tab 标注「分步/Agent 模式」；降低维护成本且不 fork SKILL 逻辑。

---

## ADR-003：统一 Runner 层封装子进程

**状态**：已接受  

**决策**：`core/runner.py` 提供 `run_script`、`run_agent_runner`、`run_json_script`；超时、cwd、env 注入集中处理。  

**后果**：新增技能只需在 `services` 注册命令模板。

---

## ADR-004：任务持久化与并发上限

**状态**：已接受  

**决策**：`outputs/.studio_jobs/jobs.json`；`ThreadPoolExecutor(max_workers=2)`。  

**理由**：图像生成与 PPT stage 均耗时且占 API 配额。  

---

## ADR-005：仓库根发现策略

**状态**：已接受  

**决策**：自包位置向上查找 `skills/sn-image-base`；支持 `SN_SKILLS_ROOT`。  

**理由**：兼容 `SenseNova-Skills/SenseNova-Skills/` 嵌套布局与 Cursor 工作区根。

---

## ADR-006：Excel 工作流

**状态**：已接受（务实）  

**决策**：v1 实现 **数据探查**（sheet/行/列统计）+ 导出 JSON/Markdown；不打包 40+ capability 子 skill 按钮。  

**理由**：子 skill 无统一 CLI；探查满足「选文件 + 触发分析」验收，完整分析仍走 Agent + `sn-da-excel-workflow` SKILL。

---

## ADR-007：输出目录约定

**状态**：已接受  

| 类型 | 路径 |
|------|------|
| 通用输出 | `outputs/studio/<job_id>/` |
| PPT deck | `ppt_decks/`（与 sn-ppt-entry 一致） |
| 研究 | `research/` |
| 任务元数据 | `outputs/.studio_jobs/` |

---

## ADR-008：密钥安全

**状态**：已接受  

- UI 显示 API Key 时用 `mask_secret()`  
- 日志写入 jobs 时剔除 `SN_API_KEY` 等字段  
- `.env.example` 保持空密钥模板

---

## ADR-009：图像 Tab 采用左右分栏布局

**状态**：已接受（已实现，2026-05-18）  

**背景**：当前 Gradio 图像子 Tab 为垂直堆叠，宽屏下预览区下推，与 A1111 / 可灵 / Firefly 等主流生图 UI 不一致；用户迭代 Prompt 时需频繁滚动。  

**决策**：在 **🖼️ 图像** 五个子 Tab 内引入 **左栏控制（~40%）+ 右栏预览（~60%）** 的 `ImageWorkspace` 壳；`<960px` 降级为上下堆叠。不更换 UI 框架（延续 ADR-001）。  

**备选**：保持垂直 + sticky 预览（Gradio 支持弱）；独立 React 前端（交付周期长）。  

**后果**：新增 `sn_studio/ui/components/image_workspace.py`；`app.py` 图像区重构；Help 收敛为 Accordion。右栏不展示独立「状态日志 / 流水线阶段」文本区，阶段信息收敛到 `stage_indicator`；扩写 Prompt 限高滚动；任务历史支持选中/双击加载。  

**规格**：[image-studio-layout-lr.md](./image-studio-layout-lr.md)
