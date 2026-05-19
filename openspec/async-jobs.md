# 异步任务与轮询契约（async-jobs）

> 实现：`sn_studio/core/jobs.py`、`sn_studio/ui/components/job_status.py`  
> 图像流水线字段见 [prompt-pipeline-unified.md](./prompt-pipeline-unified.md)

## 任务状态

| status | 含义 | UI |
|--------|------|-----|
| `pending` | 已入队 | ⏳ 排队中… |
| `running` | 执行中 | ⏳ 处理中… ({kind}) |
| `done` | 成功 | ✅ 完成 + 填充输出组件 |
| `failed` | 失败 | ❌ + log 摘要 |

终端态：`done` | `failed`

## 持久化

- 路径：`outputs/.studio_jobs/jobs.json`
- 单条字段：`id`, `kind`, `status`, `created_at`, `finished_at`, `params`, `result`, `log`, `output_paths`
- 图像流水线 `result` 扩展（`done` 时）：`expanded_prompt`, `expanded_prompt_path`, `pipeline_stages`（list）、`prompts_expand_skipped`, `prompts_expand_mode`, `work_dir`
- 保留最近 200 条；UI 列表默认展示 **10** 条

## 轮询

| 参数 | 值 |
|------|-----|
| 间隔 | **1.5s**（图像/诊断）；任务列表 **3s** |
| 机制 | `gr.Timer` + `tick`；提交后 `gr.Timer(active=True)` |
| 停止 | 终端态 → `gr.Timer(active=False)`；**无 job_id 的 Tab 回调返回 `gr.skip()`，不得关闭共享 Timer** |

## `wait_for_job(job_id, timeout=600, poll_interval=1.0)`

- 阻塞等待至终端态或超时
- 返回 `Job` 或 `None`（不存在）
- 超时抛出 `TimeoutError`（仅供脚本/测试，UI 用 Timer）

## Progress UI 契约

| 场景 | 方式 |
|------|------|
| 后台 job（图像、doctor） | Timer 轮询 + Tab 状态 Textbox |
| 同步短操作（Excel、搜索、PPT 阶段） | `gr.Progress()` 或 `show_progress="full"` |
| 全局 | 顶部 Toast 在 click 首帧更新 |

## 输出映射（done）

| kind 前缀 | 组件 |
|-----------|------|
| `image_*` | `gr.Gallery` ← `resolve` 后的绝对路径；`poll_pipeline_tick` 更新 Accordion 内扩写 Prompt |
| `doctor_*` | `gr.Textbox` ← `log` |
| 其他 | `gr.Textbox` / 路径列表 |

## 失败时

- 不清空用户已填写的输入
- Gallery 保持上一张成功图（可选）或空
- 任务历史仍可查；Toast 不强制用户跳转
