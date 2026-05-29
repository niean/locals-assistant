<!-- SUMMARY: Hermes Assistant 项目术语定义 -->
# 术语表

- Hermes：作业帮内部 cron 任务调度系统，负责定时执行任务并输出结果文件
- Assistant：Hermes 的管理平台（本项目），提供 Web 界面展示任务执行状态
- Job：Hermes 中注册的一个定时任务，包含调度表达式和启用状态
- Run：一次任务执行记录，由 Hermes 生成为 Markdown 文件
- Delivered：执行状态 — 任务正常完成并产生有效输出
- Silent：执行状态 — 任务完成但无有效输出（静默执行，标记 `[SILENT]`）
- Error：执行状态 — 任务执行失败或输出异常
- jobs.json：Hermes 任务配置文件，包含所有注册任务的元数据
- output/：Hermes 执行结果输出目录，按 job_id 分子目录存储 Markdown 文件
- CM 订单号：作业帮内部订单系统 ID，格式为 CM + 数字，可在 op.zuoyebang.cc 查看详情
- launchd：macOS 系统守护进程管理器，用于自动启动 assistant HTTP 服务
- ODIN：作业帮内部运营系统（op.zuoyebang.cc），CM 订单的管理后台
