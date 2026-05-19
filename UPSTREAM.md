# 上游仓库说明

本仓库在 **[OpenSenseNova/SenseNova-Skills](https://github.com/OpenSenseNova/SenseNova-Skills)** 基础上维护，并新增 **SenseNova Skills Studio**（`sn_studio/`）本地图形适配工具及相关文档、规格说明。

| 项目 | 链接 |
|------|------|
| **官方上游** | https://github.com/OpenSenseNova/SenseNova-Skills |
| **Agent Skills 规范** | https://agentskills.io/ |
| **商汤日日新 API Key** | https://platform.sensenova.cn/console/keys |

## 与上游的关系

- **`skills/`**：与官方 sn-\* 技能包同源；Studio 通过子进程调用，不替代 SKILL 编排逻辑。  
- **`sn_studio/`、`openspec/`、`scripts/install_studio.ps1` 等**：本仓库扩展内容，用于无 Agent 环境下的本地面板。  
- 若仅需官方技能、不需要 Studio，请直接使用上游仓库与 [`INSTALL_CN.md`](INSTALL_CN.md)。

## 同步上游（可选）

已配置 `upstream` 远程时：

```powershell
git fetch upstream
git checkout main
git merge upstream/main
# 解决冲突后 push 到你自己的 origin
```

首次将官方设为上游：

```powershell
git remote add upstream https://github.com/OpenSenseNova/SenseNova-Skills.git
```
