# outputs/（本地目录，不纳入 Git）

Studio 与 sn-* 技能运行时的默认产物根目录，已在 `.gitignore` 中忽略。

| 路径 | 说明 |
|------|------|
| `studio/` | 图像、Excel 探查等 Studio 输出 |
| `studio/series/<YYYYMMDD_HHMMSS>/` | 系列批量（含 `series-lines.txt`、`manifest.json`） |
| `.studio_jobs/jobs.json` | 任务状态与会话历史索引 |

首次运行相关 Tab 后目录会自动创建。
