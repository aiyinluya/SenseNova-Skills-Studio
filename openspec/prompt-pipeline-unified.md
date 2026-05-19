# 统一图像 Prompt 流水线（prompt-pipeline-unified）

> 关联：[chinese-text-on-image.md](./chinese-text-on-image.md) · [ui-collapsible-prompt.md](./ui-collapsible-prompt.md) · [interaction-refactor.md](./interaction-refactor.md) · [ux-flows.md](./ux-flows.md) · [async-jobs.md](./async-jobs.md)

## 目标

Studio **所有图像子模块**在调用 `sn-image-generate` 之前，必须经过结构化 Prompt 流水线，禁止将用户原始短句直接作为最终生图 prompt（`disable` 模式除外）。

标准五段式（与 `sn-infographic` 对齐）：

```
评估 → 内容分析 → 版式/风格选型 → Prompt 扩写 → 生图
```

实现入口：`sn_studio/services/prompt_pipeline.py` → `run_pipeline(...)`。

## 模块映射

| Studio Tab | `module_kind` | 流水线变体 | 说明 |
|------------|---------------|------------|------|
| 文生图 | `generate` | 标准五段（轻量分析，无 infographic 结构化模板） | 默认 `prompts_expand_mode=auto` |
| 信息图 | `infographic` | 完整 `sn-infographic`（含 layout/style 参考 MD） | 委托 `infographic_pipeline.run_infographic_pipeline` |
| 系列批量 | `series` | 一句话拆解 N 场景 → 共享风格块 + 每行短扩写 | `expand_series_prompts`；全系列共用 seed/负向 |
| 风格模仿 | `imitate` | **非**五段：识图 caption → 风格保持改写 → 生图 | 对齐 `sn-image-imitate` SKILL；改写阶段注入中文可读性附录 |
| 简历图 | `resume` | 简历版式 prompt（`prompts/resume.md`）→ 生图 | 对齐 `sn-image-resume` SKILL；扩写注入中文附录 |
| PPT creative T2I | `ppt_creative`（预留） | 由 `sn-ppt-creative` 阶段脚本负责；Studio 仅文档化 | Studio PPT Tab 当前不直接 T2I |

## 扩写模式 `prompts_expand_mode`

| 值 | 行为 |
|----|------|
| `auto`（默认） | 评估（`evaluation-standard.md` 或模块等价）→ 通过则跳过扩写，原文出图 |
| `force` | 始终执行分析 + 扩写 |
| `disable` | 跳过评估与分析，用户原文直接生图（调试/高级用户） |

## 产物与 jobs.json

每次走流水线（非 `disable` 跳过）写入：

| 字段 | 说明 |
|------|------|
| `expanded_prompt` | 最终生图字符串 |
| `expanded_prompt_path` | `outputs/studio/<module>/<ts>/expanded-prompt.txt` |
| `pipeline_stages` | `[{"id":"evaluate","label":"评估中"}, ...]` 时间序 |
| `prompts_expand_skipped` | bool |
| `prompts_expand_mode` | auto/force/disable |
| `work_dir` | 工件目录 |

UI 通过 `gr.Accordion` 展示扩写结果，见 [ui-collapsible-prompt.md](./ui-collapsible-prompt.md)。

## 进度回调

`on_progress(stage_label: str)` → 写入 `jobs.set_job_progress` → Tab 状态行显示。

各模块阶段标签（简体中文）：

| 阶段 id | 标签 |
|---------|------|
| evaluate | 评估中 |
| analyze | 分析内容 |
| layout | 分析版式 |
| expand | 扩写 Prompt |
| caption | 解析参考图 |
| rewrite | 改写 Prompt |
| resume_expand | 简历排版扩写 |
| series_plan | 拆解系列场景 |
| series_style | 系列风格统一 |
| generate | 生成图像 |

## 负向 Prompt 默认

文生图/系列在未填写负向时合并 `DEFAULT_NEGATIVE_PROMPT_CHINESE`（乱码、水印、过小字号等），见 [chinese-text-on-image.md](./chinese-text-on-image.md)。

## 与 Cursor Agent 的关系

完整多轮 VLM 评审（`max_rounds>1`）、布局一致性重试（imitate）仍在对应 SKILL 的 Worker Agent 中执行；Studio 实现 **首版单轮** 流水线 parity。
