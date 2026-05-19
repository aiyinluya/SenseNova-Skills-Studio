# 扩写 Prompt 可折叠展示（ui-collapsible-prompt）

> 实现：`sn_studio/ui/components/prompt_preview.py`  
> 关联：[prompt-pipeline-unified.md](./prompt-pipeline-unified.md) · [ux-flows.md](./ux-flows.md)

## 需求

扩写后的 Prompt 可能数百至上千字，默认 **收起**，避免挤压 Gallery；用户可展开复制或核对中文文案。

## 组件

`build_prompt_preview_block()` 返回：

| 组件 | Gradio 类型 | 说明 |
|------|-------------|------|
| 外层 | `gr.Accordion("扩写后的 Prompt", open=False)` | 默认折叠 |
| 内文 | `gr.Textbox` lines=10, interactive=False | 任务完成后填入 |
| 阶段 | `gr.Textbox` label="流水线阶段" lines=2 | 可选，展示 `pipeline_stages` 摘要 |

## 轮询契约

- 共享 `poll_pipeline_tick(job_id, expanded_tb)`：与 `poll_infographic_tick` 相同逻辑，适用于所有 `image_*` job。
- 提交时清空 expanded textbox；`running` 时若有部分 `expanded_prompt` 可增量更新（通常为空直到 done）。
- `done`：`gr.update(value=result.expanded_prompt)` + Accordion 仍可手动展开。

## 各 Tab

| Tab | Accordion | 扩写模式下拉 |
|-----|-----------|--------------|
| 文生图 | ✅ | ✅ auto/force/disable |
| 信息图 | ✅ | ✅（已有） |
| 系列批量 | ✅ | ✅ |
| 风格模仿 | ✅ | ✅（改写阶段受模式约束） |
| 简历图 | ✅ | ✅ |

移除文生图旧「使用文本优化扩写」Checkbox，由统一 **扩写模式** 下拉替代。

## 无障碍与复制

- Textbox 只读但可选中复制（Gradio 默认）。
- 状态行仍显示当前阶段（「扩写 Prompt…」），与 Accordion 内容互补。
