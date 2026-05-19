# 功能需求 — 按技能类别

## FR-0 全局

| ID | 需求 |
|----|------|
| FR-0.1 | 自动发现仓库根目录（含 `skills/` 与 `.env`） |
| FR-0.2 | 启动时加载 `.env` 到进程环境 |
| FR-0.3 | 任务队列：提交、运行中、完成、失败；持久化 JSON |
| FR-0.4 | 中文 UI 标签；可选深色 Gradio 主题 |

## FR-1 设置（sn-image-doctor / 全局配置）

| ID | 需求 |
|----|------|
| FR-1.1 | `.env` 可视化编辑与保存 |
| FR-1.2 | 校验必填项：`SN_BASE_URL`、`SN_API_KEY` |
| FR-1.3 | API 连通性测试（轻量 HTTP，不记录密钥） |
| FR-1.4 | 模型覆盖：`SN_IMAGE_GEN_MODEL` 等展示与编辑 |
| FR-1.5 | 技能目录扫描：列出 `skills/sn-*` |
| FR-1.6 | 运行 `sn-image-doctor` / `sn-ppt-doctor` 诊断脚本 |

## FR-2 图像（sn-image-base, infographic, imitate, resume）

| ID | 需求 |
|----|------|
| FR-2.1 | 文生图：prompt、宽高比、seed、保存路径 |
| FR-2.2 | 信息图：内容 → 文本优化 → 生图（简化流水线） |
| FR-2.3 | 系列批量：多行 prompt 队列顺序生图 |
| FR-2.4 | 风格模仿：参考图 + 新内容（VLM + 优化 + 生图） |
| FR-2.5 | 简历图：简历文本 → 优化 prompt → 生图 |
| FR-2.6 | 图像环境检查（doctor） |

## FR-3 PPT（entry, doctor, creative, standard）

| ID | 需求 |
|----|------|
| FR-3.1 | 向导：role / audience / scene / page_count / mode |
| FR-3.2 | 参考文档上传，写入 `ppt_decks/<topic>_<ts>/` |
| FR-3.3 | 生成 `task_pack.json` + `info_pack.json` |
| FR-3.4 | Standard：`run_stage.py preflight` 等单阶段触发 |
| FR-3.5 | PPT doctor 一键检查 |
| FR-3.6 | 打开 deck 目录 |

## FR-4 数据分析（sn-da-excel-workflow, large-file, image-caption）

| ID | 需求 |
|----|------|
| FR-4.1 | Excel 上传：Sheet 列表、行数、列预览 |
| FR-4.2 | ≥10k 行提示启用 Parquet/大文件模式说明 |
| FR-4.3 | 导出探查报告到 `outputs/studio-excel/` |
| FR-4.4 | 图片 Caption：调用 `caption.py` |
| FR-4.5 | 大文件：openpyxl read_only 行数统计（可选） |

## FR-5 深度研究（sn-deep-research 链）

| ID | 需求 |
|----|------|
| FR-5.1 | 从主题创建 `research/<topic>_<ts>/` |
| FR-5.2 | 写入 `request.md` 模板 |
| FR-5.3 | 展示 `plan.json` / `sub_reports/` / `synthesis.md` / `report.md` 存在状态 |
| FR-5.4 | `render_report.py`：MD → HTML |
| FR-5.5 | 说明：完整多维度研究需在 Agent 中继续 |

## FR-6 搜索（academic, code, social-cn, social-en）

| ID | 需求 |
|----|------|
| FR-6.1 | 统一搜索 UI：类别、提供商、关键词、条数 |
| FR-6.2 | 调用各 skill 下 `scripts/*_search.py`，解析 JSON |
| FR-6.3 | 结果表格展示 title / url / snippet |
| FR-6.4 | 可选 GitHub token 等环境变量提示 |

## FR-7 任务历史

| ID | 需求 |
|----|------|
| FR-7.1 | 列表：时间、类型、状态、输出路径 |
| FR-7.2 | 查看日志摘要 |
| FR-7.3 | 在资源管理器中打开输出目录（Windows） |

## FR-8 更新（sn-update）

| ID | 需求 |
|----|------|
| FR-8.1 | 显示上游仓库 URL 与本地 skills 路径 |
| FR-8.2 | `git pull` / 文档指引（不破坏用户 fork） |
| FR-8.3 | 列出可更新 `sn-*` 技能名 |

## 非功能需求

- NFR-1：单图生成超时默认 600s
- NFR-2：并发后台任务上限 2（避免 API 限流）
- NFR-3：依赖通过 `pyproject.toml` 可安装
- NFR-4：无 API Key 时降级为配置引导，不崩溃
