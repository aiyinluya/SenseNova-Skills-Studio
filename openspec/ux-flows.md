# UX 流程规格（按 Tab）

> 状态机约定见 [async-jobs.md](./async-jobs.md)。文案见 [ui-copy.md](./ui-copy.md)。图像流水线见 [prompt-pipeline-unified.md](./prompt-pipeline-unified.md)、扩写 UI 见 [ui-collapsible-prompt.md](./ui-collapsible-prompt.md)。

## 全局

```
idle ──[主操作]──► loading (≤200ms 显示 Toast + Tab 状态)
loading ──► success (自动填充结果组件)
loading ──► error   (红色状态行，可选保留 job_id)
```

**顶部 Toast**（`gr.Markdown`）：每次主操作更新一行；与配置横幅（绿/黄/红）分离。

---

## ⚙️ 设置

| 步骤 | idle | loading | success | error |
|------|------|---------|---------|-------|
| 保存 .env | 编辑中 | 「保存中…」 | 「✅ 已保存」+ 热加载 | 校验错误列表 |
| 测试 API | — | 「测试中…」 | 延迟 ms + 前 5 个模型 id | 连接失败一行红字 |
| 图像/PPT 诊断 | — | 「诊断已提交…」+ Timer 轮询 | 结果写入「操作结果」全文 | 失败摘要 |

**不展示**：仅「任务 ID: xxx」而无结果链接。

---

## 🖼️ 图像（各子 Tab 同构）

| 子 Tab | 触发 | 结果组件 |
|--------|------|----------|
| 文生图 | 生成 | Gallery + 状态 + **折叠**扩写 Prompt |
| 信息图 | 生成信息图 | Gallery + 状态 + 折叠扩写 Prompt |
| 系列批量 | 批量生成 | Gallery（多图）+ 状态 + 折叠扩写（含共享风格块） |
| 风格模仿 | 模仿 | Gallery + 状态 + 折叠扩写 Prompt |
| 简历图 | 生成海报 | Gallery + 状态 + 折叠扩写 Prompt |

**共用参数**：`扩写模式`（auto / force / disable，默认 auto）。详见 [prompt-pipeline-unified.md](./prompt-pipeline-unified.md)。

流程：

1. 点击 → 立即 `⏳ 已提交，正在生成…`
2. `submit` 后台 job → `job_id` 写入 `gr.State`
3. `gr.Timer(1.5s)` 激活 → 轮询至 `done`/`failed`
4. **success**：Gallery ← 已解析的绝对图片路径（`gr.update`）；状态 `✅ 完成`；无图时有路径列表回退
5. **error**：Gallery 不变；状态 `❌ …`

### 统一流水线阶段（写入 job.log，轮询显示）

| 模块 | 典型阶段序列 |
|------|----------------|
| 文生图 / 信息图 | 评估中 → 分析内容 / 分析版式 → 扩写 Prompt → 生成图像 |
| 系列批量 | 拆解系列场景 → 系列风格统一 → 扩写 Prompt（逐张）→ 生成图像 |
| 风格模仿 | 解析参考图 → 改写 Prompt → 生成图像 |
| 简历图 | 简历排版扩写 → 生成图像 |

- `disable`：仅「生成图像」
- `auto` 且评估通过：跳过分析/扩写，直接「生成图像」
- 完成后：`expanded_prompt` 填入 **Accordion 内**只读框；`jobs.json` 含 `expanded_prompt`、`expanded_prompt_path`、`pipeline_stages`

产物目录：`outputs/studio/<module>/<timestamp>/`（含 `expanded-prompt.txt` 等）。

### 信息图（sn-infographic 完整版）

额外参数：`最大生成轮次`（默认 1）、可选风格说明；版式/风格从 skill references 选取。

### 文生图 vs 信息图

| | 文生图 | 信息图 |
|---|--------|--------|
| 入口 | 画面描述 | 内容与数据 |
| 默认 | 描述直出图 | 完整扩写流水线 |
| 可选扩写 | Checkbox，单次 optimize | 内置 auto/force/disable |

---

## 📊 PPT

| 操作 | 反馈 | 结果 |
|------|------|------|
| 创建 Deck | `gr.Progress` 或即时 | `deck_dir` 文本框 + 输出区摘要 |
| 运行阶段 | 「运行中…」+ Progress | `ppt_out` 显示 stdout 摘要（截断） |
| 打开文件夹 | 即时 | Toast「已打开」 |

---

## 📈 数据分析

| 操作 | loading | success |
|------|---------|---------|
| Excel 探查 | Progress +「探查中…」 | Markdown 摘要自动刷新 |
| Caption | 「识别中…」 | Textbox 填入 caption 文本 |

---

## 🔬 深度研究

| 操作 | 结果 |
|------|------|
| 创建目录 | `report_dir` + 进度 Markdown 自动刷新 |
| 刷新进度 | 更新进度 Markdown |
| MD→HTML | 输出 HTML 路径（可点击式纯文本） |

---

## 🔍 搜索

1. 点击 → 立即清空表 + 状态「搜索中…」
2. 同步调用 skill 脚本（可 `show_progress="full"`）
3. success → Dataframe 填充；状态 `✅ N 条`
4. error → 空表 + 红色 `❌ …`

---

## 📋 任务历史

- **自动刷新** Checkbox 默认 ON → `gr.Timer(3s)` 刷新表格
- 展示 **最近 10 条**（含 job_id 短码）
- 「加载选中任务结果」→ 本 Tab 内预览区（图集 / 路径列表 / 日志摘要）
- 「打开文件夹」保留

---

## 🔄 更新

- Git 状态：刷新即时
- pull：Progress + 结果文本框
