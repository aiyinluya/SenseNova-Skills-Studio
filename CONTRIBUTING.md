# 贡献指南

感谢关注 SenseNova Skills Studio。

## 提交前请确认

- [ ] **不要**提交 `.env`、API Key 或 `outputs/` 下个人生成文件  
- [ ] 可选密钥行勿留空赋值（如 `SN_IMAGE_GEN_API_KEY=`），见 `.env.example` 说明  
- [ ] 改动 `sn_studio/` 时补充或更新 `sn_studio/tests/` 中的测试（如适用）  
- [ ] UI/产品行为变更请同步 `openspec/` 相关文档  

## 开发环境

```powershell
cd REPO_ROOT
powershell -ExecutionPolicy Bypass -File .\scripts\install_studio.ps1
copy .env.example .env
# 填入 SN_API_KEY
python -m sn_studio
```

```powershell
python -m unittest discover -s sn_studio/tests -v
python -c "from sn_studio.ui.app import build_app; build_app()"
```

## 范围说明

- **`skills/`**：尽量保持与上游 skill 契约一致；结构性修改请说明对 Studio `runner` 的影响。  
- **`sn_studio/`**：Studio 专属代码，欢迎 PR。  
- **`openspec/`**：产品/架构约定，行为变更请一并更新。  

## Pull Request

1. Fork 仓库并基于 `main` 创建分支。  
2. 提交信息建议：`feat(studio): …` / `fix(studio): …` / `docs: …`  
3. PR 描述中说明：变更动机、如何验证、是否影响既有 skill 调用。  

Issue 与讨论请使用 GitHub Issues。
