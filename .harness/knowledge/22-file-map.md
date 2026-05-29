<!-- SUMMARY: Hermes Assistant 功能与文件映射 -->
# 功能与文件映射

## 应用入口与全局

- 前端入口：`index.html`（HTML 结构 + 内联 CSS/JS，待重构为模块化）
- 后端入口：`server.py`（HTTP 服务器 + API 路由 + 数据解析）
- 启动脚本：`start-http.sh`（launchd 守护进程启动入口）
- 站点图标：`favicon.svg`

## 后端 API（server.py）

- HTTP 服务器：HTTPServer + ThreadingMixIn
- 路由分发：do_GET 方法中按路径匹配
- /api/jobs 处理：读取 jobs.json + 扫描 output/ + 合并统计
- /api/runs/{job_id} 处理：解析指定任务的 Markdown 执行记录
- 静态文件服务：/ 路径返回 index.html

## 前端 UI（index.html，当前内联，目标拆分为模块）

- 页面布局：header（标题+刷新按钮）+ main（任务列表）+ footer（版本信息）
- 任务卡片：展示任务名称、调度表达式、状态、今日统计
- 执行历史表格：时间戳、响应内容、状态标签
- 统计栏：今日总执行数、delivered 数、silent 数
- 自动刷新：setInterval 定时拉取

## 目标架构文件（规划中）

- `css/settings/_variables.css` — CSS 变量定义
- `css/generic/_reset.css` — 样式重置
- `css/components/_job-card.css` — 任务卡片组件样式
- `css/components/_run-history.css` — 执行历史组件样式
- `css/components/_stats-bar.css` — 统计栏组件样式
- `js/main.js` — 应用入口，初始化与事件绑定
- `js/services/api-service.js` — API 调用封装
- `js/services/polling-service.js` — 轮询管理
- `js/components/job-card.js` — 任务卡片组件
- `js/components/run-history.js` — 执行历史组件
- `js/components/stats-bar.js` — 统计栏组件
- `js/utils/constants.js` — 常量定义
- `js/utils/dom-helpers.js` — DOM 操作工具
- `js/utils/formatters.js` — 日期/文本格式化

## 配置与资源

- 数据源（外部，只读）：`~/.hermes/cron/jobs.json`、`~/.hermes/cron/output/`
- 日志输出：`~/Library/Logs/assistant-http/server.log`
- 进程管理：macOS launchd plist（系统级配置）
