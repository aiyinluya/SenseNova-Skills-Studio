# 图像 Studio 左右分栏布局（OpenSpec）

> **状态**：已实现（含 2026-05-18 UI 反馈修订）  
> **版本**：0.2.0 · 2026-05-18  
> **关联**：[ui-ux.md](./ui-ux.md) · [ux-flows.md](./ux-flows.md) · [interaction-refactor.md](./interaction-refactor.md) · [async-jobs.md](./async-jobs.md) · [prompt-pipeline-unified.md](./prompt-pipeline-unified.md) · [ui-collapsible-prompt.md](./ui-collapsible-prompt.md)  
> **实现入口**：`sn_studio/ui/app.py`（图像 Tab）、新建 `sn_studio/ui/components/image_workspace.py`

---

## 执行摘要（给决策者）

| 问题 | 结论 |
|------|------|
| 图像生成是否应采用左右分栏？ | **是（推荐）**，置信度 **88%** |
| 左栏 / 右栏职责 | **左 = 输入与控制**；**右 = 预览、历史条、流水线反馈** |
| 与当前差异 | 现为 **自上而下**（表单 → 按钮 → Gallery → 状态 → Accordion），长 Prompt 与多行 help 导致 **预览区下推、迭代需大量滚动** |
| 技术栈约束 | 保持 **Gradio 5.x**；不引入 React 壳（ADR-001 延续） |
| MVP 范围 | 仅 **🖼️ 图像** 五个子 Tab 共用 `ImageWorkspace` 壳；其他 Tab 维持现状 |

**不采用左右分栏的场景（本 spec 明确为非目标）**：设置、搜索表格、PPT 向导、深度研究目录树——这些以表单/表格为主，垂直流更合适。

---

## 1. Goals & Non-Goals

### 1.1 Goals

1. **对齐主流生图工具心智模型**：左侧调参、右侧看结果，减少学习成本。
2. **缩短「改 Prompt → 再看图」闭环**：预览区在首屏右侧固定可见区域，视口高度内可见 Gallery + 当前阶段状态。
3. **统一五类图像子 Tab 布局骨架**：文生图 / 信息图 / 系列 / 风格模仿 / 简历图 仅换左栏字段，右栏交互一致。
4. **保留既有异步契约**：`gr.Timer` 轮询、`poll_pipeline_tick`、折叠扩写 Prompt、顶部 Toast，行为不退化。
5. **可验收的分阶段交付**：MVP 布局 → 历史条 → 键盘/无障碍抛光。

### 1.2 Non-Goals

- 不重写后端 `image.submit_image_job` 或 `prompt_pipeline` 业务逻辑。
- 不做 Midjourney 式 Discord 集成、不做节点图编辑器（ComfyUI 级）。
- 不在 v1 实现 WebSocket 进度百分比（见 ADR / interaction-refactor Out of scope）。
- 不将全站 8 个顶层 Tab 改为左右分栏（仅图像域）。
- 不做原生移动端 App（Gradio 响应式仅保证「可纵向堆叠降级」）。

---

## 2. 现状发现（Current UI）

### 2.1 技术栈

- **框架**：Gradio 5.12+，`python -m sn_studio`，默认 `http://127.0.0.1:7860`
- **主题**：`gr.themes.Base()`，主色 `#0ea5e9`（`help_copy.HELP_CSS`）
- **入口**：`sn_studio/ui/app.py` → `build_app()`

### 2.2 全局壳层（保持不变）

```
┌─────────────────────────────────────────────────────────────┐
│  # SenseNova Skills Studio + 副标题                          │
│  🟢/🟡/🔴 配置横幅 (config_banner)                           │
│  Toast 条 (action_toast)                                     │
├─────────────────────────────────────────────────────────────┤
│  [⚙️设置][🖼️图像][📊PPT][📈数据][🔬研究][🔍搜索][📋历史][🔄更新] │  ← gr.Tabs 顶层
└─────────────────────────────────────────────────────────────┘
```

### 2.3 图像 Tab 现状：**垂直堆叠（Top-Bottom）**

每个子 Tab（以文生图为例，`app.py` L196–246）顺序为：

1. `help_md` 说明  
2. Prompt `Textbox`  
3. `gr.Row`：宽高比 | Seed | 扩写模式  
4. 多条 `help_md`  
5. 负向词  
6. **主按钮「生成」**  
7. **`Gallery`（height=360）**  
8. **状态 `Textbox`**  
9. **`Accordion` 扩写 Prompt**  

**问题归纳**：

| 痛点 | 影响 |
|------|------|
| 预览在视口下方 | 生成完成后需滚动才能对比图与 Prompt |
| Help 块分散在控件间 | 左栏信息密度低、纵向过长 |
| 无会话内「上一张」快捷条 | 迭代对比依赖 Gallery 默认行为或任务历史 Tab |
| 五子 Tab 重复相同垂直模式 | 一致但未利用宽屏 |

### 2.4 已有可复用组件

| 路径 | 职责 |
|------|------|
| `sn_studio/ui/components/prompt_preview.py` | 扩写 Accordion |
| `sn_studio/ui/components/job_status.py` | 提交、轮询、`poll_pipeline_tick` |
| `sn_studio/ui/components/help_copy.py` | 中文 help、`HELP_CSS` |
| `sn_studio/services/image.py` | `submit_image_job` |
| `sn_studio/core/jobs.py` | 任务持久化；`session_history_gallery()` 供会话条启动恢复 |

---

## 3. 主流产品布局对标（Benchmark）

| 产品 | 控制区位置 | 预览/画廊 | 历史/变体 | 参数密度 | 与 Studio 相似度 |
|------|------------|-----------|-----------|----------|------------------|
| **Stable Diffusion WebUI (A1111)** | 左栏多 Tab（txt2img/img2img） | 右上主预览 + 下画廊 | 代数/网格在右 | 极高（折叠区多） | 高（本地、参数多） |
| **ComfyUI** | 左：节点库；中：画布；右：队列/预览 | 画布中央 | 右侧队列 | 极高（节点） | 中（过于专业） |
| **Leonardo.ai** | 左或左下 Prompt + 模型 | 中央/右大预览 | 底部/侧历史条 | 中 | 高 |
| **Adobe Firefly (Web)** | 左 Prompt + 风格 | 右大画布 | 底部条带 | 低~中 | 高 |
| **Ideogram** | 顶/左 Prompt | 中瀑布流 | 无限滚动 feed | 低 | 中 |
| **Midjourney (Discord)** | 底/侧命令（非传统 GUI） | 频道流 | 线程变体 | 低（命令式） | 低 |
| **可灵 / 即梦 (Kling/Jimeng)** | **左侧** Prompt + 比例/风格 | **右侧** 大图 + 底部缩略图 | 时间线缩略图 | 中 | **很高** |
| **Runway / 部分 API 台** | 左配置 | 右预览 | 版本列表 | 中 | 高 |

**行业共识（2024–2026 Web 生图）**：

- **宽屏（≥1280px）**：`控制面板 | 预览画布` 左右分栏占主导（A1111、可灵、Firefly、Leonardo）。
- **Prompt 紧贴主按钮**，且与预览 **同屏可见** 时，迭代效率最高。
- **历史/变体** 多为预览区 **下方横向缩略图** 或 **右侧窄条**，而非独立页面（Studio 另有「任务历史」Tab 作补充）。

---

## 4. 左右分栏：本产品专项分析

### 4.1 用户工作流（Jobs To Be Done）

```
配置 API → 选子模式 → 写 Prompt/内容 → 调参 → 生成
    → 看预览 → （可选）看扩写 Prompt → 改 Prompt 再生成 → 导出/打开文件夹
```

Studio 用户画像（推断，与 README 一致）：

- **本地 Windows + 浏览器**，显示器以 1080p~2K 为主，宽屏可用。
- **技能流水线重**（评估→扩写→生图），状态反馈比「纯文生图」更关键。
- **中英 Prompt 混用**，扩写结果需核对（`chinese-text-on-image`）。

### 4.2 左右分栏 Pros / Cons

| Pros | Cons |
|------|------|
| 预览常驻右侧，符合可灵/ A1111 习惯 | Gradio `Row` 在窄屏需手动 `Column` 降级 |
| 左栏可 `Accordion` 收纳高级参数，控制首屏高度 | 左栏过宽会挤压预览（需 `min-width` CSS） |
| 五子 Tab 共享右栏组件，减少重复 wiring | 子 Tab 字段差异大（如参考图上传），左栏需插槽 |
| 与「任务历史」Tab 分工清晰：会话内 vs 全局 | 双栏 + 顶层 Tab 嵌套，新手可能觉得层级多 |

### 4.3 备选方案对比

| 方案 | 描述 | 评分 | 说明 |
|------|------|------|------|
| **A. 左右分栏（推荐）** | 左 38~42% 控制，右 58~62% 预览 | ★★★★★ | 见第 5 节线框 |
| B. 保持上下，仅 Sticky 预览 | CSS `position:sticky` 吸顶 Gallery | ★★★ | Gradio 对 sticky 支持不稳定 |
| C. 右左镜像（预览在左） | 与部分设计工具一致 | ★★ | 与生图品类主流相反，不推荐 |
| D. 三栏（历史|控制|预览） | 仿 IDE | ★★ | 信息过载，Gradio 维护成本高 |
| E. 独立 React 前端 | 完全定制 | ★★★★（长期） | 违背 ADR-001 短期目标 |

### 4.4 最终推荐

**采用方案 A：图像子 Tab 内左右分栏**，置信度 **88%**。

**理由（产品 + UX）**：

1. 与 **可灵/即梦、A1111、Firefly** 一致，降低首次使用成本。  
2. Studio 图像 Tab **纵向过长** 是当前可观测问题（代码结构决定）。  
3. **扩写流水线** 使状态区需常驻；右栏「阶段条 + Gallery」比塞在左栏底部更自然。  
4. Gradio 5 的 `gr.Row` + `scale` + 自定义 CSS 足以 MVP，无需换栈。

**保留上下布局的例外**：视口宽度 **< 960px** 时自动切换为 **上（控制）下（预览）**（见 7.3）。

---

## 5. 信息架构（IA）

### 5.1 层级

```
Studio
└── 顶层 Tab
    └── 🖼️ 图像
        └── 子 Tab（文生图 | 信息图 | 系列 | 模仿 | 简历）
            └── ImageWorkspace（新）
                ├── 左栏 ImageControlPanel（子 Tab 定制字段）
                └── 右栏 ImagePreviewPane（共用）
```

### 5.2 右栏信息优先级（Z-order / 视觉权重）

1. **主 Gallery**（当前任务输出）— 最大  
2. **阶段条**（`stage_indicator` Markdown，单行流水线摘要）— 中  
3. **本会话历史缩略条** — 72–96px 横向条带（`interactive=False`，无上传区）；**点击**缩略图在**主 Gallery** 加载大图与扩写 Prompt；启动时从 `outputs/.studio_jobs/jobs.json`（必要时回退扫描 `outputs/studio/`）恢复  
4. **工具条**：打开输出目录 — 小  
5. **扩写 Prompt Accordion** — 默认折叠；文本区 **max-height 240px + 纵向滚动**

**明确不在右栏展示（2026-05-18 产品决定）**：

- ~~「状态日志」折叠区~~（原 `log_box` 仅隐藏保留，供轮询兼容）  
- ~~「流水线阶段」独立 Textbox~~（阶段信息仅出现在顶部阶段条 + Toast）

### 5.3 左栏信息优先级

1. **主输入**（Prompt / 内容 / 多行系列 / 参考图）  
2. **主 CTA「生成」**（`variant="primary"`，左栏底部 sticky 或紧跟主输入）  
3. **核心参数行**：宽高比、扩写模式（所有子 Tab 共有）  
4. **高级参数 Accordion**：Seed、负向词、信息图轮次等  
5. **上下文 Help**：收成 **「参数说明」单 Accordion**（默认折叠），避免打散在控件间

---

## 6. 线框与区域规格（Wireframes）

### 6.1 桌面宽屏（≥1280px）— 文生图

```
┌──────────────────────────────────────────────────────────────────────────┐
│ 🟢 API 就绪                                    Toast: ⏳ 文生图 · 已提交   │
├─────────────────────────────┬────────────────────────────────────────────┤
│ 子 Tab: [文生图][信息图]…    │                                            │
├─────────────────────────────┼────────────────────────────────────────────┤
│  LEFT ~40% (min 360px)      │  RIGHT ~60% (flex)                         │
│ ┌─────────────────────────┐ │  ┌────────────────────────────────────────┐ │
│ │ 画面描述               │ │  │  阶段: 评估中 → 扩写 Prompt → 生成图像    │ │
│ │ [....................] │ │  │  ████████░░░░  (可选进度条 MVP+1)       │ │
│ │ [....................] │ │  ├────────────────────────────────────────┤ │
│ ├─────────────────────────┤ │  │                                        │ │
│ │ 宽高比 ▼  扩写模式 ▼    │ │  │           MAIN GALLERY                 │ │
│ ├─────────────────────────┤ │  │         (height ~340px, contain)     │ │
│ │ ▶ 高级参数              │ │  │                                        │ │
│ │   Seed  负向描述        │ │  │                                        │ │
│ ├─────────────────────────┤ │  ├────────────────────────────────────────┤ │
│ │ ▶ 参数说明 (help)       │ │  │ [thumb][thumb][thumb]  ← 会话历史条     │ │
│ ├─────────────────────────┤ │  ├────────────────────────────────────────┤ │
│ │      [  生成  ]         │ │  │ ▶ 扩写后的 Prompt (折叠)                │ │
│ └─────────────────────────┘ │  │ ▶ 扩写后的 Prompt (折叠, 可滚动)           │ │
│                             │  │ [打开输出文件夹]                          │ │
└─────────────────────────────┴────────────────────────────────────────────┘
```

### 6.2 风格模仿（左栏差异）

- 左栏上部：`gr.Image` 参考图（高度上限 200px）+ 新内容 Textbox。  
- 右栏不变。

### 6.3 系列批量

- 左栏：`系列主题` + `张数` + 可选 `风格锚点`；宽高比与扩写模式同其他 Tab。  
- 右栏 Gallery `columns=3`，`height=340`（系列批量同默认；多图时 grid-wrap 内滚动）。

### 6.4 窄屏降级（< 960px）

```
┌─────────────────────┐
│ 控制区（全宽）       │
│ Prompt + 参数 + 生成 │
├─────────────────────┤
│ 阶段条 + Gallery     │
│ 历史条 + Accordion   │
└─────────────────────┘
```

实现：`gr.Row` 外包 `elem_id="sn-image-workspace"`，CSS `@media (max-width: 960px)` 改为 `flex-direction: column`。

### 6.5 尺寸 Token（布局）

| Token | 值 | 说明 |
|-------|-----|------|
| `--sn-layout-left-ratio` | `0.40` | 左栏 `scale=4` |
| `--sn-layout-right-ratio` | `0.60` | 右栏 `scale=6` |
| `--sn-left-min-width` | `360px` | CSS min-width |
| `--sn-gallery-max-height` | `360px` | 桌面主预览（CSS） |
| `--sn-gallery-min-height-narrow` | `280px` | 窄屏 |
| `--sn-thumb-size` | `72px` | 会话历史缩略图 |
| `--sn-stage-bar-height` | `32px` | 阶段条 |

---

## 7. 组件层次与 API（开发向）

### 7.1 新建模块 `image_workspace.py`

```python
def build_image_workspace(
    *,
    control_builders: Callable[[], list[gr.components.Component]],
    submit_fn,
    submit_inputs: list,
    job_state: gr.State,
    poll_timer: gr.Timer,
    action_toast: gr.Markdown,
    detail: str,
    gallery_columns: int = 2,
    gallery_height: int = 340,
) -> tuple[gr.Gallery, ...]:
    """
    返回 (gallery, log_box, expanded_tb, stages_tb) 供外层 _wire_pipeline_image_job。
    内部创建 Row[左 control | 右 preview]。
    """
```

**职责拆分**：

| 组件 | 文件 | 说明 |
|------|------|------|
| `ImageWorkspace` 壳 | `image_workspace.py` | Row 布局 + 阶段条 + 工具条 |
| `build_prompt_preview_block` | `prompt_preview.py` | 不变，嵌入右栏底部 |
| `build_stage_indicator` | `image_workspace.py`（或 `job_status.py`） | 从 `poll_pipeline_tick` 解析阶段 → Markdown/HTML |
| `build_session_thumbs` | `image_workspace.py` | MVP+1：读当前 job 前序输出路径 |
| 子 Tab 字段 | `app.py` | 仅声明左栏控件列表 |

### 7.2 左栏 Accordion 分组（文生图）

| 分组 | 控件 | 默认 |
|------|------|------|
| 主区 | `画面描述` Textbox | 展开 |
| 常用 | `宽高比`, `扩写模式` Row | 展开 |
| 高级参数 | `Seed`, `负向描述` | **折叠** |
| 参数说明 | 原 `HELP_*` 合并 Markdown | **折叠** |

### 7.3 右栏组件绑定（与 async-jobs 一致）

| 事件 | 更新组件 |
|------|----------|
| `button.click` | `job_state`, 清空 gallery/expanded, 激活 `poll_timer`, Toast |
| `poll_timer.tick` | `gallery`, `expanded_tb`, **stage_indicator**, 会话历史条 |
| `done` | Gallery 路径、`stage_indicator` = ✅、历史条追加、Accordion 可展开 |
| `failed` | Gallery 保持、`stage_indicator` = ❌ |

### 7.4 `app.py` 迁移模式（每个子 Tab）

**Before**（垂直）：

```python
with gr.Tab("文生图"):
    gen_prompt = gr.Textbox(...)
    ...
    gen_btn = gr.Button(...)
    gen_gallery = gr.Gallery(...)
```

**After**（伪代码）：

```python
with gr.Tab("文生图"):
    def _build_controls():
        gen_prompt = gr.Textbox(...)
        ...
        return [gen_prompt, gen_ratio, ...], gen_btn

    gallery, log, exp, stages = build_image_workspace(
        control_builder=_build_controls,
        ...
    )
```

`_wire_pipeline_image_job` **签名不变**，仅 Gallery 等引用来自 `build_image_workspace` 返回值。

---

## 8. 交互流程（Interaction Flows）

### 8.1 首次访问（图像 Tab）

1. 用户见 🟡/🔴 横幅 → 引导去「设置」（若未配置）。  
2. 进入「文生图」→ 左 Prompt 占位符 + 右空状态插画（ **空状态** 文案：「生成后在此显示预览」）。  
3. 不强制教程；**参数说明 Accordion** 内含简短指引。

### 8.2 重复用户（迭代）

1. 左栏改 Prompt → 点击生成（**≤200ms** Toast）。  
2. 右栏阶段条滚动更新（评估中→…→生成图像）。  
3. 完成后 Gallery 自动填充；缩略历史条追加（MVP+1）。  
4. 用户展开「扩写后的 Prompt」核对 → 复制 → 再生成。  
5. **主按钮位置**：左栏底部固定（生成后无需滚动找按钮）。

### 8.3 错误态

| 场景 | 右栏表现 | 左栏 |
|------|----------|------|
| API 未配置 | 阶段条 ❌ + 链接「去设置」 | 生成按钮 disabled 或点击后提示 |
| 生成失败 | 保留上一张 Gallery（可选） | 输入保留 |
| 超时 | ❌ 超时文案 + job_id | 同 |

### 8.4 加载 / 进度

- **MVP**：阶段条文字 + 现有 `poll_pipeline_tick` 日志。  
- **MVP+1**：`gr.Progress()` 或阶段条内 `%`（若 job 暴露 `progress` 字段）。  
- 生成中 **禁用生成按钮**（`interactive=False`）防止重复提交（受 `max_workers=2` 约束）。

---

## 9. 响应式、无障碍、快捷键

### 9.1 响应式

| 断点 | 布局 |
|------|------|
| ≥1280px | 左右 40/60 |
| 960–1279px | 左右 45/55，Gallery 高度 360 |
| <960px | 上下堆叠 |

### 9.2 无障碍

- Gallery 图片带 `alt`（文件名或 job kind）。  
- 阶段条 `aria-live="polite"`（Gradio Markdown 尽量实现）。  
- 主按钮 `variant="primary"` + 逻辑焦点顺序：Prompt → 参数 → 生成 → Gallery。  
- 对比度：状态色沿用 🟢🟡🔴，错误 `#dc2626`。

### 9.3 键盘快捷键（MVP+2）

| 快捷键 | 行为 |
|--------|------|
| `Ctrl+Enter` | 触发生成（左栏聚焦时） |
| `Ctrl+Shift+C` | 展开/聚焦扩写 Prompt |
| `Ctrl+O` | 打开当前 job 输出目录 |

---

## 10. 视觉设计 Token

沿用 `help_copy.HELP_CSS`，扩展：

```css
/* help_copy.HELP_CSS */
#sn-image-workspace { gap: 1rem; align-items: flex-start; }
.sn-image-left { min-width: 360px; max-width: 480px; flex: 0 1 auto; }
.sn-image-left .accordion { flex: 0 0 auto; min-height: unset; }
.sn-image-right { flex: 1; }
.sn-stage-bar { font-size: 0.9rem; padding: 0.5rem; border-left: 3px solid #0ea5e9; }
.sn-gallery-main .grid-wrap { max-height: 360px; } /* object-fit: contain on images */
.sn-expanded-prompt textarea { max-height: 240px; overflow-y: auto; }
```

| 类别 | Token | 值 |
|------|-------|-----|
| 主色 | `--sn-primary` | `#0ea5e9` |
| 字号 | 标题 / 正文 / 辅助 | 1.25rem / 0.95rem / 0.85rem |
| 间距 | `xs/sm/md/lg` | 4/8/16/24px |
| 圆角 | 卡片 / 按钮 | 8px / 6px |
| 阴影 | Gallery 容器 | `0 1px 3px rgba(0,0,0,.08)` |

---

## 11. 产品交互逻辑

### 11.1 用户故事

| ID | 故事 | 验收 |
|----|------|------|
| US-1 | 作为用户，我想在右侧固定位置看到最新生成图 | 生成完成后 Gallery 位于右栏可视区 |
| US-2 | 作为用户，我想左侧改 Prompt 并一键再生成 | 按钮在左栏底部，≤ 2 次点击 |
| US-3 | 作为用户，我想知道当前流水线阶段 | 阶段条实时更新 |
| US-4 | 作为用户，我想核对扩写结果但不占主屏 | Accordion 默认折叠 |
| US-5 | 作为用户，我想快速打开输出文件夹 | 右栏工具条 ≤1 次点击 |

### 11.2 主/次操作

| 级别 | 操作 | 位置 |
|------|------|------|
| Primary | 生成 / 批量生成 / 模仿生成 | 左栏底部 |
| Secondary | 打开输出文件夹 | 右栏工具条 |
| Tertiary | 查看扩写 Prompt | 右栏 Accordion |
| Quaternary | 任务历史 Tab | 顶层导航 |

### 11.3 生成任务状态机（复用 async-jobs）

```
idle → (click) → pending → running → done | failed
```

**UI 映射增强**：

- `running`：右栏阶段条 + 可选禁用生成按钮。  
- `done`：Gallery + 缩略历史追加 + Toast「✅ 完成」。  
- `failed`：阶段条 ❌ + 保留输入。

### 11.4 空状态（右栏）

- 文案：「尚无生成结果 · 在左侧输入描述后点击生成」  
- 可选：灰色占位框 16:9。

### 11.5 Onboarding

- 首次进入图像 Tab：Toast「左侧输入，右侧预览」。  
- 不阻断操作；`localStorage` 或 `jobs.json` 记录 `onboarding_seen`（MVP+2）。

---

## 12. 从现状迁移

### 12.1 布局迁移

| 步骤 | 内容 |
|------|------|
| 1 | 新建 `image_workspace.py`，实现 `build_image_workspace` |
| 2 | 文生图 Tab 试点 → 验证轮询/Gallery 正常 |
| 3 | 其余 4 个子 Tab 迁移 |
| 4 | Help 文本迁入「参数说明」Accordion |
| 5 | 更新 `ui-ux.md` 屏幕地图 |

### 12.2 兼容性

- `jobs.json` 结构不变。  
- `outputs/studio/` 路径不变。  
- 对外 API（`submit_image_job`）不变。

---

## 13. 分阶段实施（Phased Delivery）

### Phase 0 — 设计冻结（本文档）

- [x] 对标与线框  
- [ ] 设计评审（产品 + 开发）  

### Phase 1 — MVP（左右分栏 + 文生图试点）

- [x] `image_workspace.py` + CSS  
- [x] 五图像子 Tab 迁移  
- [x] 右栏 `stage_indicator`；移除可见「状态日志」「流水线阶段」  
- [x] 桌面左右 / 窄屏上下  
- **验收**：文生图生成 → 右栏见 Gallery；全程无手动滚动（1080p）

### Phase 2 — 全子 Tab + Help 收敛

- [x] 五子 Tab 共用壳  
- [x] Help 合并为 Accordion（自然高度，不纵向拉伸）  
- [x] 生成按钮禁用逻辑  

### Phase 3 — 抛光

- [x] 本会话缩略历史条 + 点击回看  
- [x] 打开文件夹按钮  
- [x] 「任务历史」Tab：Dataframe/缩略图 **单击或双击** 加载详情  
- [ ] 键盘快捷键  
- [ ] 无障碍审计  

### Phase 4 — 可选增强（Out of MVP）

- [ ] 拖拽调整左右比例  
- [ ] 预览灯箱（Lightbox）  
- [x] 与「任务历史」联动：选中/双击条目 → 加载预览与扩写 Prompt  

---

## 14. 验收标准（Acceptance Criteria）

| ID | 标准 |
|----|------|
| AC-1 | 五图像子 Tab 在 ≥1280px 下均为左右分栏 |
| AC-2 | 生成完成后 2s 内 Gallery 自动填充（沿用 async-jobs） |
| AC-3 | 首屏（1080p）可见主按钮 + Gallery 区域 ≥50% |
| AC-4 | 窄屏 <960px 自动上下布局，功能不退化 |
| AC-5 | 扩写 Accordion 默认折叠；完成后可展开复制 |
| AC-6 | 不破坏 `jobs.json` 与现有测试 |
| AC-7 | `python -c "from sn_studio.ui.app import build_app; build_app()"` 通过 |

---

## 15. 需修改文件清单

| 文件 | 变更类型 |
|------|----------|
| `sn_studio/ui/components/image_workspace.py` | **新建** |
| `sn_studio/ui/app.py` | 重构五图像子 Tab |
| `sn_studio/ui/components/help_copy.py` | 扩展 CSS、合并 Help |
| `sn_studio/ui/components/job_status.py` | 可选：`stage_indicator` 解析 |
| `openspec/ui-ux.md` | 屏幕地图更新 |
| `openspec/decisions.md` | 新增 ADR-009 |
| `README_CN_STUDIO.md` | OpenSpec 索引 |

**不改**：`services/image.py`、`core/jobs.py`（除非 Phase 3+ 历史条）。

---

## 16. 开放问题（Open Questions）

1. **左栏宽度用户可调？** — Phase 4 再议。  
2. **多 job 并行 UI？** — 当前 `max_workers=2`，仅 Toast 区分；队列 UI 后续。  
3. **是否引入风格预设下拉？** — 依赖 sn-image-base 能力，独立 spec。  

---

## 附录 A：竞品截图位（占位）

> 开发/设计评审时可补充 Figma 或截图链接。

## 附录 B：Gradio 实现注意事项

- `gr.Row(equal_height=False)` + `#sn-image-workspace { align-items: flex-start }`，避免左栏 Accordion 被拉高。  
- 左栏 `.accordion { flex: 0 0 auto }` 保持折叠区紧凑高度。  
- 扩写 Prompt：`elem_classes=["sn-expanded-prompt"]` + CSS `max-height: 240px; overflow-y: auto`。  
- 历史回看：Gradio **无原生 Gallery/Dataframe 双击事件**；采用 `select`（单击）+ 任务表 `dblclick` 转发为 `click`（`HISTORY_DBLCLICK_JS`）。  
- 主 Gallery `height` 桌面建议 **340**（`DEFAULT_GALLERY_HEIGHT`）；`object_fit=contain` + `allow_preview=True`（点击 lightbox 看全尺寸）；CSS `.sn-result-preview` 限制 `max-height` 约 320–360px，避免原生分辨率撑满视口。  
- 避免嵌套超过 3 层 Tabs（现有结构已 2 层，不再加深）。

---

## 附录 C：2026-05-18 UI 反馈修订记录

| 反馈 | 处理 |
|------|------|
| 左栏「高级参数」「参数说明」Accordion 纵向拉伸 | `equal_height=False` + 左栏 flex/CSS |
| 移除右栏「状态日志」「流水线阶段」 | `log_box` 隐藏；`stages_tb` 删除 |
| 扩写 Prompt 长文需滚动条 | `.sn-expanded-prompt textarea` max-height |
| 历史任务双击展示 | 图像 Tab 会话条 `select`；任务历史 Tab 表/缩略图 select + JS 双击 |
| 「结果预览」默认图过大、需大量滚动 | `height=340`、`object_fit=contain`、`.sn-result-preview` CSS；五 Tab 统一默认高度；点击放大 |
