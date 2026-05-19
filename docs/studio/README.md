# Studio 文档索引

| 文档 | 读者 | 说明 |
|------|------|------|
| [`README_CN_STUDIO.md`](../../README_CN_STUDIO.md) | 用户 | 安装、启动、Tab 说明、故障排除 |
| [`openspec/project.md`](../../openspec/project.md) | 产品 / 开发 | 愿景、约束、成功标准 |
| [`openspec/architecture.md`](../../openspec/architecture.md) | 开发 | 分层与子进程约定 |
| [`openspec/ui-ux.md`](../../openspec/ui-ux.md) | 设计 / 开发 | 界面与交互 |
| [`../promo/sensenova-skills-promo.md`](../promo/sensenova-skills-promo.md) | 对外宣传 | 推广长文 |

## 仓库结构（Studio 相关）

```text
REPO_ROOT/
├── skills/                 # sn-* 技能包（Studio 通过子进程调用，不修改 SKILL 逻辑）
├── sn_studio/              # Studio Python 包
│   ├── core/               # config, paths, jobs, runner
│   ├── services/           # 图像 / PPT / Excel / 研究 / 搜索等业务封装
│   ├── ui/                 # Gradio 界面与组件
│   └── tests/              # 单元测试
├── openspec/               # 产品与架构规格（OpenSpec）
├── scripts/                # install_studio.ps1、smoke_studio.py
├── tests/                  # 仓库级集成测试
├── docs/
│   ├── studio/             # 本索引
│   └── promo/              # 推广文章与配图
├── outputs/                # 本地产物（Git 忽略，见 outputs/README.md）
├── pyproject.toml          # 包名 sn-skills-studio，入口 sn-studio / python -m sn_studio
├── requirements-studio.txt
└── .env.example
```
