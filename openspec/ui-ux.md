# UI / UX 规格

> **交互重构（2025-05）**：完整流程与轮询契约见专用文档：
> - [interaction-refactor.md](./interaction-refactor.md) — 目标与成功指标
> - [ux-flows.md](./ux-flows.md) — 各 Tab idle→loading→success 流程
> - [ui-copy.md](./ui-copy.md) — 中文 help 与语气
> - [async-jobs.md](./async-jobs.md) — 任务状态与 Timer 轮询
> - [image-studio-layout-lr.md](./image-studio-layout-lr.md) — **图像 Tab 左右分栏布局**（对标主流生图工具）

## 技术选型

**Gradio 5.x**（≥5.12，`theme` 在 `gr.Blocks`）— 单文件可启动、Windows 友好、内置文件上传与 Gallery、`gr.Timer` 轮询后台任务。

主题：`gr.themes.Base()` + 主色 `#0ea5e9`（SenseNova 蓝）；`gr.themes.Default()` 作浅色备选（启动参数 `--theme light`）。

## 屏幕地图

```
┌──────────────────────────────────────────────────────────┐
│  SenseNova Skills Studio                    [关于] [刷新] │
├──────────┬───────────────────────────────────────────────┤
│ 设置     │  .env 编辑器 | API 测试 | 技能列表 | Doctor   │
│ 图像     │  子 Tab 内 **左控制 | 右预览**（见 image-studio-layout-lr.md） │
│ PPT      │  向导 | 文档上传 | 单阶段运行 | 打开目录        │
│ 数据分析 │  Excel 探查 | 大文件提示 | 图片 Caption       │
│ 深度研究 │  新建课题 | 进度树 | MD→HTML                   │
│ 搜索     │  类别/提供商 | 查询 | 结果表                    │
│ 更新     │  git 状态 | 更新说明 | 运行 pull（可选）       │
└──────────┴───────────────────────────────────────────────┘
```

> **图像 Tab（当前实现）**：各子 Tab 内 **左控制 | 右预览**（`ImageWorkspace`）；右栏含阶段条、主 Gallery、本会话历史缩略条、扩写 Prompt（可滚动）。详见 [image-studio-layout-lr.md](./image-studio-layout-lr.md)。

## 导航原则

- 左侧 **Tab** 对应技能域，顺序与 FR 编号一致。
- 每个 Tab 顶部 **状态条**：API 是否已配置（绿/黄/红）。
- 长操作：点击后 **200ms 内** 显示「处理中…」；完成后 **同 Tab 自动展示结果**（见 async-jobs.md）。
- 危险操作（覆盖 `.env`）需勾选确认。

## 关键工作流

### 设置

1. 进入 Tab → 结构化字段（`SN_BASE_URL` 明文；`SN_API_KEY` 为密码框，**永不回显完整密钥**）  
2. 已保存密钥仅显示状态行，如 `已配置 (sk-…abcd)`；留空密码框表示不修改  
3. 保存 → 合并写盘 + 热加载；保存后清空密码框  
4. 「测试 API」/「刷新状态」→ 延迟与 HTTP 状态；日志与原始响应经 `sanitize_log` 脱敏  
5. 可选密钥与模型在折叠「可选配置」内；技能数量一行摘要（无重复 env 大块文本区）

### 文生图

1. 填写 prompt、选择比例  
2. 点击「生成」→ 立即状态「处理中…」+ 顶部 Toast  
3. 完成 → **同页 Gallery 自动预览**（Timer 轮询，无需打开任务 Tab）

### Excel

1. 上传 `.xlsx`  
2. 点击「探查」→ Markdown 摘要（sheet/行/列样例）  
3. 可选保存 JSON 到 outputs

### 搜索

1. 选「学术 → arXiv」  
2. 输入 query → 结果 Dataframe  
3. 失败显示 skill 脚本 stderr 摘要

## 无障碍与本地化

- 所有控件 `label` 使用简体中文  
- `info=` 提示关键 env 变量名（英文），便于对照 SKILL.md  
- 错误信息保留英文原文片段便于搜索 issue

## 未来扩展（非当前 Phase）

- WebSocket 推送任务进度百分比  
- 嵌入 SKILL.md 只读预览  
- 跨 Tab 一键「将任务结果载入图像页」
