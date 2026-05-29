<!-- SUMMARY: Hermes Assistant 模块分层、目录结构与边界约束 -->
# 架构与模块边界

## 分层（目标架构）

- 表现层（`css/` + `js/components/`）：ITCSS+BEM CSS 架构，ES6 Module 组件。主要视图：JobList（任务列表）、JobCard（任务卡片）、RunHistory（执行历史）、StatsBar（统计栏）
- 服务层（`js/services/`）：API 调用封装、数据转换。核心：ApiService（HTTP 请求）、JobService（任务数据处理）、PollingService（定时刷新）
- 工具层（`js/utils/`）：日期格式化、DOM 操作、常量定义
- 后端 API 层（`server.py`）：HTTP 服务器、路由分发、数据解析（Markdown → JSON）
- 数据层（`~/.hermes/cron/`）：jobs.json 配置 + output/ 执行记录（外部系统产生，本项目只读）

## 模块边界

- UI 组件只通过 Service 层获取数据，不直接调用 fetch 或操作 DOM 之外的全局状态
- Service 层封装所有 API 调用，返回格式化后的业务对象
- 后端 server.py 仅负责文件解析与 HTTP 响应，不修改 Hermes 数据
- 前端不直接读取文件系统，所有数据通过 /api/* 端点获取
- CSS 组件样式自包含，通过 BEM 命名避免全局污染
- 后端 API 数据格式变更需同步更新前端 Service 层

## 关键约束

- server.py 仅监听 localhost:8090，不对外暴露
- 数据目录 ~/.hermes/cron/ 为只读，本项目不写入
- 前端无路由（单页面，无 SPA 路由框架），所有内容在同一页面展示
- Markdown 文件解析容错：格式异常时跳过该条记录，不中断服务
