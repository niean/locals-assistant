<!-- SUMMARY: Hermes Assistant 项目概览：技术栈、入口、核心流程 -->
# 项目概览

## 一句话

Hermes Assistant — 面向内部运维人员的 Hermes cron 任务管理平台，通过 Web 界面展示任务执行状态与历史，技术上采用 Python 后端 + 纯前端 SPA 架构。

## 技术栈

- 后端：Python 3（stdlib http.server），无第三方依赖
- 前端：HTML5 + CSS3 + ES6 Modules（零依赖，无构建步骤）
- CSS 架构：ITCSS 分层 + BEM 命名（目标架构）
- JS 规范：Airbnb Style Guide（目标架构）
- 运行时：macOS launchd 守护进程，端口 8090
- 数据源：读取 `~/.hermes/cron/output/` 目录下的 Markdown 文件 + `~/.hermes/cron/jobs.json` 配置

## 入口与根状态

- 入口：`index.html`（前端 SPA）+ `server.py`（后端 API 服务器）
- 启动：`scripts/start-http-exec.sh` 由 launchd 调起，检查端口可用性后启动 server.py
- 根状态：前端 JavaScript 维护 jobs 列表数据，通过 API 轮询刷新（每 5 分钟自动刷新）

## 核心流程

1. 服务启动：launchd → scripts/start-http-exec.sh → server.py 监听 8090 端口
2. 数据加载：server.py 读取 ~/.hermes/cron/jobs.json 获取任务配置，扫描 output/ 目录获取执行记录
3. 页面渲染：前端 fetch /api/jobs → 渲染任务卡片列表 → 展示今日统计
4. 详情查看：点击任务卡片 → fetch /api/runs/{job_id} → 展示执行历史表格
5. 自动刷新：定时器每 5 分钟重新拉取数据更新界面

## 文档与规则

操作约束见 `.harness/framework/FRAMEWORK.md`，知识库加载策略见 `.harness/PROJECT.md`。
