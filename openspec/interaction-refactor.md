# 交互重构总纲（Interaction Refactor）

> 关联文档：[ux-flows.md](./ux-flows.md) · [ui-copy.md](./ui-copy.md) · [async-jobs.md](./async-jobs.md) · [ui-ux.md](./ui-ux.md) · [prompt-pipeline-unified.md](./prompt-pipeline-unified.md) · [ui-collapsible-prompt.md](./ui-collapsible-prompt.md)

## 背景

用户反馈：点击操作后长时间无反馈、需手动去「任务历史」查看结果、参数缺少中文说明、界面充斥 Agent 术语与冗余 Markdown。本次为 **OpenSpec 驱动的完整交互重构**，非零散补丁。

## 目标

1. **可感知**：任意主操作在 200ms 内出现状态反馈（文案或 spinner）。
2. **可完成**：长任务结束后 **自动** 填充当前 Tab 的结果区（图、表、路径、日志），无需用户切换 Tab 自查。
3. **可理解**：非显然参数附带简短中文 `gr.Markdown` 说明（非弹窗问卷）。
4. **可恢复**：失败时红色状态行 + 保留任务 ID；成功不重复展示无关联的「已提交 task id」。

## 设计原则

| # | 原则 | 说明 |
|---|------|------|
| P1 | 反馈优先 | 先更新顶部 Toast / 本 Tab 状态行，再执行 I/O |
| P2 | 结果归位 | 成功产物出现在触发操作的同一 Tab |
| P3 | 少即是多 | 去掉重复 Markdown 墙、空占位、Agent 黑话 |
| P4 | 中文第一 | 控件 label、help、错误摘要均为简体中文 |
| P5 | 不破坏 Runner | 子进程仍走 `sn_agent_runner` / skill scripts，Studio 只改 UI 编排 |

## 成功指标（可验收）

| 指标 | 目标 |
|------|------|
| 首帧反馈延迟 | ≤ 200ms（状态文案或 `show_progress`） |
| 图像类后台任务 | 完成后 2s 内 Gallery 自动出现图片（轮询 ≤1.5s 间隔） |
| 搜索 | 完成后 Dataframe 自动填充；失败红色一行 |
| 设置 API 测试 | 显示延迟 ms + 模型名片段，非整页 JSON |
| 任务历史 | 默认自动刷新；最近 10 条；一键预览最近完成任务的输出 |
| 用户无需话术 | 全流程不出现「请自行到任务 Tab 查看」类文案（失败除外） |

## 范围

**In scope（Phase 1–2）**

- 全局 Toast、`JobPoller` + `gr.Timer`
- 图像五子 Tab、设置诊断、任务历史、搜索、PPT 阶段运行、Excel/Caption 同步进度
- `jobs.wait_for_job`、README 交互说明

**Out of scope（后续 Phase）**

- WebSocket 推送百分比
- 跨 Tab 自动跳转（Gradio 限制）
- 深度研究全自动多轮 Agent

## 技术约束

- Gradio **5.x**（`theme` 在 `gr.Blocks`，非 `launch`）
- `gr.Timer` 轮询 `jobs.json` 持久化状态
- 密钥不入库、日志 `sanitize_log`
