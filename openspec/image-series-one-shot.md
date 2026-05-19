# 系列批量 · 一句话成系列（image-series-one-shot）

> 关联：[prompt-pipeline-unified.md](./prompt-pipeline-unified.md) · [image-studio-layout-lr.md](./image-studio-layout-lr.md) · [ux-flows.md](./ux-flows.md)

## 产品愿景

用户输入**一句话主题**，选择张数 **N（3–8）**，系统产出**风格统一**的 N 张图系列，无需手写多行分镜。

可选：**风格锚点**（短词或参考说明），与共享风格块叠加，进一步锁定配色/画风。

## 现状 vs 目标

| 维度 | 现状（改前） | 目标（MVP） |
|------|-------------|-------------|
| 输入 | 多行 Textbox，每行一张 | 单行「系列主题」+ 张数 Dropdown |
| 分镜 | 用户自备 N 行 | LLM `expand_series_prompts` 拆为 N 条短场景 |
| 风格统一 | 合并前 3 行做 `shared_style_block`，再逐张扩写 | 保留；拆解阶段已要求角色/画风一致 |
| 张数 | 由行数决定 | 显式 3/4/5/6/7/8 |
| 可选风格 | 无 | 「风格锚点（可选）」Textbox |
| 扩写模式 | auto / force / disable | 保留 |
| 宽高比 | 16:9 / 9:16 / 1:1 | 保留 |
| 生图 | 逐张 `sn-image-generate`，共享负向 prompt | 同左；**全系列共用随机 seed** 增强一致性 |

参考脚本：`outputs/cervical-spine-series/generate_series.py`（手工 `00-style-guide.txt` + 分文件 prompt），Studio 用流水线自动化同等模式。

## 推荐流程

```
用户：主题（1 句）+ N + [风格锚点] + 宽高比 + 扩写模式
  ↓
① 拆解系列场景（LLM）→ N 条短描述（20–60 字/条）
  ↓
② 系列风格统一（LLM）→ shared_style_block（已有）
  ↓
③ 扩写 Prompt（逐张，注入共享风格块）（已有）
  ↓
④ 生成图像 × N（同一 seed、同一负向、同一宽高比）
```

`disable` 扩写模式：仍执行①拆解（否则无 N 条输入）；跳过②③，直接用短描述生图。

## 左栏 UX（线框）

```
┌─ 系列批量 ─────────────────────┐
│ 系列主题 *          [单行 4 行] │
│ 张数                [3▼4 5 6 7 8]│
│ 风格锚点（可选）    [单行 2 行] │
│ 宽高比 | 扩写模式   [Row]       │
│ ▶ 参数说明（折叠）              │
│ [ 批量生成 ]                    │
└────────────────────────────────┘
```

右栏不变：阶段条 → Gallery(3 列) → 会话历史 → 扩写 Accordion → 输出路径。

## 输出目录（会话历史仅认此结构）

每次系列批量在 **`outputs/studio/series/<YYYYMMDD_HHMMSS>/`** 下落盘，例如：

```
outputs/studio/series/20260518_155613/
  series-lines.txt          # N 条拆解场景（一行一条）
  shared-style-block.txt    # 共享视觉风格块（扩写非 disable 时）
  expanded-prompt.txt         # 最后一张的扩写摘要
  expanded-prompt-01.txt …    # 逐张扩写
  01.png … 0N.png             # 生成图（同 seed）
  manifest.json               # [{index, path, prompt}, …]
```

**会话历史（`kind=image_series`）规则：**

- 只展示 `jobs.json` 中 `series_dir` / `output_paths` 能解析到上述目录的任务；缩略图为该目录下 **`01.png`**（或 `manifest.json` 首项）。
- 加载 `jobs.json` 时会**丢弃**仍指向旧路径的已完成 `image_series` 记录（如 `outputs/studio/series_<ts>/`、无 `series-lines.txt` / `manifest.json` 的目录）。
- 无 jobs 记录时，回退扫描仅遍历 `outputs/studio/series/<timestamp>/`，忽略 `series_*` 平铺目录与 `cervical-spine-series` 等离线脚本路径。

## 与 SKILL / Agent 的关系

- 生图仍走 `sn-image-base` / `sn_agent_runner.py`（`sn-image-generate`），不新增独立 skill 包。
- 远期可抽 `sn-image-series` SKILL：导出 style bible + manifest，供离线批跑（对齐 `cervical-spine-series`）。

## 产品增强建议（后续）

1. **参考图风格锚**：上传 1 张参考图 → VLM 提取风格块，替代/补充文字锚点（复用 imitate caption 路径）。
2. **系列模板**：科普步骤 / 漫画分镜 / 封面+内页，预置 N 与拆解 prompt 模板。
3. **并行生图**：N 张独立 job 或 worker 池（注意 API 限流）。
4. **预览拆解**：提交前展示 N 条短描述，可编辑后再生成。
5. **导出 ZIP + manifest.json**：一键下载系列包。

## 验收（手动）

1. `python -c "from sn_studio.ui.app import build_app; build_app()"` 无异常。
2. 打开 Studio → 图像 → **系列批量**：仅见主题/张数/风格锚点/宽高比/扩写模式。
3. 主题「颈椎健康科普插画」、张数 4、扩写 force → 阶段含「拆解系列场景」→ Gallery 4 张。
4. 文生图 / 信息图 / 风格模仿 Tab 控件与提交不受影响。
