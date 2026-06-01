<!-- SUMMARY: Hermes Assistant 模块分层、目录结构与边界约束 -->
# 架构与模块边界

## 分层（当前架构）

- 表现层（`css/` + `js/components/`）：ITCSS+BEM CSS 架构，ES6 Module 组件。主要视图：Overview（系统状态）、Jobs（任务卡片+执行历史）、Sessions（会话列表+详情）、Tools（Skills/MCP/Plugins）
- 服务层（`js/services/`）：API 调用封装（fetchJson/postJson）。统一错误处理，返回 Promise
- 工具层（`js/utils/`）：常量定义（API_BASE、REFRESH_INTERVAL）、DOM 操作工具（escapeHtml、linkify、formatNumber）
- 后端 API 层（`server.py`）：Starlette HTTP 服务器、Route 路由分发、StaticFiles 静态资源、数据解析（Markdown -> JSON、SQLite -> JSON）
- 数据层（`~/.hermes/`）：jobs.json 配置 + output/ 执行记录 + state.db 会话数据 + config.yaml 系统配置（外部系统产生，本项目只读）

## 模块边界

- UI 组件只通过 Service 层获取数据，不直接调用 fetch 或操作 DOM 之外的全局状态
- Service 层封装所有 API 调用，返回格式化后的业务对象
- 后端 server.py 仅负责文件解析与 HTTP 响应，不修改 Hermes 数据
- 前端不直接读取文件系统，所有数据通过 /api/* 端点获取
- CSS 组件样式自包含，通过 BEM 命名避免全局污染；颜色/字号使用 CSS Custom Properties
- 后端 API 数据格式变更需同步更新前端 Service 层
- JS 模块通过 ES6 import/export 通信，inline onclick 通过 window 暴露全局函数

## 关键约束

- server.py 仅监听 localhost:8090，不对外暴露
- 数据目录 ~/.hermes/ 为只读，本项目不写入
- 前端使用 hash 路由（#cron, #sessions, #tools），无 SPA 路由框架
- CSS/JS 零构建步骤，浏览器原生加载 ES Modules
- Markdown 文件解析容错：格式异常时跳过该条记录，不中断服务
- StaticFiles mount 必须位于路由列表末尾（catch-all），API 路由优先匹配
