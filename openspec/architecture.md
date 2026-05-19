# 系统架构

## 分层

```
┌─────────────────────────────────────────────────────────┐
│  ui/app.py          Gradio Blocks（中文标签、多 Tab）      │
├─────────────────────────────────────────────────────────┤
│  services/*         领域服务：组装参数、调用 runner        │
├─────────────────────────────────────────────────────────┤
│  core/jobs.py       任务注册、线程池、状态持久化            │
│  core/runner.py     子进程封装、JSON 行解析、环境注入       │
│  core/config.py     .env 读写、校验、脱敏                   │
│  core/paths.py      仓库根、skills、outputs 路径解析      │
├─────────────────────────────────────────────────────────┤
│  skills/ (既有)     sn_agent_runner, *_search.py, ...    │
└─────────────────────────────────────────────────────────┘
```

## 路径解析

1. `SN_SKILLS_ROOT` 环境变量（可选）
2. 自 `sn_studio` 包向上查找含 `skills/sn-image-base` 的目录
3. 回退：`Path.cwd()` 若含 `skills/`

`.env` 优先：`{repo_root}/.env`

## 子进程调用约定

| 能力 | 入口 | 工作目录 |
|------|------|----------|
| 图像 API | `skills/sn-image-base/scripts/sn_agent_runner.py` | repo_root |
| 图像 doctor | `skills/sn-image-doctor/scripts/check_environment.py` | repo_root |
| PPT doctor | `python -m ppt_doctor` | `skills/sn-ppt-doctor` |
| PPT stage | `skills/sn-ppt-standard/scripts/run_stage.py` | repo_root |
| 搜索 | `skills/sn-search-*/scripts/<provider>_search.py` | 脚本所在目录 |
| MD→HTML | `skills/sn-md-to-html-report/scripts/render_report.py` | repo_root |
| Caption | `skills/sn-da-image-caption/scripts/caption.py` | repo_root |

环境：子进程继承 `os.environ`，且在启动前 `load_dotenv(repo_root/.env)`。

## 任务模型

```python
Job(
  id: str,           # uuid
  kind: str,         # image_generate | search | ...
  status: pending|running|done|failed,
  created_at: iso,
  finished_at: iso | None,
  params: dict,
  result: dict | None,
  log: str,
  output_paths: list[str],
)
```

持久化：`outputs/.studio_jobs/jobs.json`（最近 200 条）

执行：`ThreadPoolExecutor(max_workers=2)`，`submit` 后 UI 通过 `gr.Timer` 或按钮刷新列表。

## 图像生成数据流

```
UI prompt → services.image.generate()
  → runner.run_agent(["sn-image-generate", "--prompt", ..., "-o", "json"])
  → 解析 stdout 最后一行 JSON
  → jobs.mark_done(save_path)
  → UI Gallery 显示图片
```

## PPT 务实封装

Studio **不** 复刻 OpenClaw 多轮 Agent 循环，而是：

1. UI 收集参数 → `services.ppt.create_deck_dir()` 写 JSON
2. 用户点击「Preflight」→ `run_stage.py preflight --deck-dir <abs>`
3. 后续阶段同理单步触发；日志进入 Job

## 深度研究务实封装

1. `services.research.init_report_dir(topic)` → `research/<slug>_<ts>/request.md`
2. UI 轮询目录树 JSON（哪些文件已存在）
3. 用户提供 `report.md` 后一键 HTML 导出

## 依赖

- **Studio**：gradio, python-dotenv, httpx, pandas, openpyxl（Excel 探查）
- **Skills**：各 skill 自带 requirements；doctor 会检查 sn-image-base
