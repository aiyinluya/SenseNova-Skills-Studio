# SenseNova Skills Studio — 项目愿景

## 定位

**SenseNova Skills Studio** 是面向 Windows 桌面用户的本地控制面板，将 [SenseNova-Skills](https://github.com/OpenSenseNova/SenseNova-Skills) 仓库中 24+ 个 `sn-*` 技能以可点击、可配置的方式暴露出来，无需 OpenClaw / Cursor Agent 编排即可运行核心流程。

目标用户不依赖 IDE 内的 `.cursor/skills` 软链，而是通过浏览器访问本机 Gradio UI（默认 `http://127.0.0.1:7860`）完成图像生成、搜索、Excel 探查、PPT 任务包创建、深度研究目录初始化等操作。

## 人物画像

| 角色 | 需求 |
|------|------|
| **业务分析师** | 上传 Excel，查看 Sheet/行数，触发清洗/统计向导；导出到 `outputs/` |
| **内容运营** | 信息图、系列图、简历图；批量 prompt 队列 |
| **研究员** | 学术/代码/社交搜索；创建 `report_dir` 并跟踪 `plan.json` / `report.md` |
| **演示制作者** | PPT 参数向导、`task_pack.json`、调用 `run_stage.py` 单阶段 |
| **平台管理员** | 编辑 `.env`、API 连通性测试、技能路径检测、`sn-update` 指引 |

## 约束

- **不修改** 现有 `skills/` 内 SKILL 逻辑；Studio 仅通过子进程调用既有脚本（`sn_agent_runner.py`、`arxiv_search.py`、`run_stage.py` 等）。
- **Python 3.10+**，优先 Windows 路径（`pathlib`、UTF-8、`os.startfile` 打开文件夹）。
- **密钥** 仅存用户本机 `.env`，UI 与日志中脱敏显示。
- **长任务** 后台线程执行，UI 轮询任务状态；失败保留 stderr 片段供排查。
- **Agent 编排型** 流程（完整 deep-research 多轮搜索、PPT 全页循环）在 Studio 中提供「输入收集 + 单步脚本触发 + 产物目录浏览」，完整自主编排仍建议在 Cursor/OpenClaw 中使用对应 SKILL。

## 成功标准

1. 新用户 5 分钟内完成：配置 `.env` → API 测试 → 生成一张图 → 一次 ArXiv 搜索。
2. 所有顶层技能类别在 UI 中有对应入口（完整度优先于每个子 capability 的独立按钮）。
3. `outputs/.studio_jobs/` 可查看历史任务、打开输出目录。
