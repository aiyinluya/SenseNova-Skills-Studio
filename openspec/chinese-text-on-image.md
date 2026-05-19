# 图片中文可读性规范（chinese-text-on-image）

> 实现：`sn_studio/services/prompt_pipeline.chinese_image_text_appendix()`  
> 关联：[prompt-pipeline-unified.md](./prompt-pipeline-unified.md)

## 问题

文生图模型常出现：中文乱码、字号过小、英文标签替代中文、笔画糊成一团。Studio 在 **扩写 system prompt** 与 **默认负向 prompt** 两层约束，不新增付费 API。

## 扩写附录（注入所有 expand / rewrite 类 system prompt 末尾）

函数 `chinese_image_text_appendix()` 返回固定段落，要点：

1. 图中需出现的中文必须用引号列出原文，一字不差来自用户输入。
2. 为每处中文指定足够大的标题/正文层级（如「主标题至少占画面宽度 60%」）。
3. 字体：黑体/思源黑体类无衬线，高对比，禁止艺术字导致笔画粘连。
4. 禁止无用户要求时混用英文标签替代中文。
5. 禁止乱码、缺笔画、拼音代替汉字、过小脚注字。

## 默认负向 Prompt（`DEFAULT_NEGATIVE_PROMPT_CHINESE`）

与用户负向合并（逗号拼接），包含：

- garbled text, illegible Chinese, wrong glyphs, broken characters
- watermark, logo overlay
- blurry text, tiny unreadable fonts
- random English text labels (unless user requested)

## 按模块

| 模块 | 注入点 |
|------|--------|
| generate | `_expand_generate_prompt` system |
| infographic | `infographic_pipeline._expand_prompt` 合并的 expand-system-prompt.md |
| series | 共享风格扩写 + 每行扩写 system |
| imitate | caption 改写 `rewrite_sys` |
| resume | `resume.md` + 附录 |

## 验收

- 单元测试：`chinese_image_text_appendix()` 非空且含「清晰可读」类关键词。
- 集成：对短 prompt「咖啡手冲四步骤」走 `force` 扩写后，`expanded_prompt` 或 `expand-system-prompt.md` 含附录关键词（需 API 时可在 CI 跳过）。

## 非目标

- OCR 后处理校验（无本地 OCR 栈）
- 自动重绘不合格文字（imitate SKILL 的 VLM 布局评审不在 Studio 首版实现）
