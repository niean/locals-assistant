<!-- SUMMARY: Hermes Assistant 功能与文件映射 -->
# 功能与文件映射

## 应用入口与全局

- 前端入口：`index.html`（纯 HTML 骨架，引用外部 CSS/JS）
- 后端入口：`server.py`（Starlette HTTP 服务器 + API 路由 + StaticFiles）
- 启动脚本：`start-http.sh`（launchd 守护进程启动入口）
- 站点图标：`favicon.svg`

## 后端 API（server.py）

- HTTP 服务器：Starlette + uvicorn
- 路由分发：Route 列表按路径匹配（API 路由优先于 StaticFiles）
- /api/jobs 处理：读取 jobs.json + 扫描 output/ + 合并统计
- /api/runs/{job_id} 处理：解析指定任务的 Markdown 执行记录
- /api/status：系统状态概览（Gateway、平台、会话统计）
- /api/sessions：活跃/不活跃会话列表
- /api/sessions/{id}/messages：会话消息详情
- /api/sessions/{id}/disconnect：断开会话（POST）
- /api/sessions/{id}/rename：重命名会话（POST）
- /api/prompt/{job_id}：获取 cron 任务 prompt 内容
- /api/skills：技能列表（custom + other）
- /api/skills/{path}/content：技能文件内容
- /api/plugins：插件列表
- /api/mcp：MCP 服务器列表
- 静态文件：Mount("/", StaticFiles) 服务 index.html、css/、js/

## 前端 CSS（ITCSS 分层）

```
css/
  settings/variables.css    -- CSS Custom Properties（颜色、字号、间距、阴影）
  generic/reset.css         -- box-sizing reset + body 基础样式
  components/tab-nav.css    -- 顶部 Tab 导航 + Sub-tab
  components/stat-card.css  -- 统计卡片网格
  components/status-panel.css -- 状态面板（含 indicator 指示灯）
  components/sessions.css   -- 会话表格 + source-badge
  components/job-card.css   -- Cron 任务卡片 + runs-table
  components/badges.css     -- status-badge + status-dot
  components/modal.css      -- 全局 Modal 弹窗
  components/buttons.css    -- header、prompt-btn、icon-btn
  utilities/text.css        -- 文本工具类（response、timestamp、order-link）
```

## 前端 JS（ES6 Modules）

```
js/
  main.js                   -- 应用入口：初始化导航、loadAll、auto-refresh、window 暴露
  utils/constants.js        -- API_BASE、REFRESH_INTERVAL 常量
  utils/helpers.js          -- escapeHtml、linkify、formatNumber、toggleResponse
  services/api.js           -- fetchJson、postJson 封装
  components/navigation.js  -- switchTab、switchSubTab、getTabFromHash、hashchange
  components/overview.js    -- loadStatus、renderOverview（Overview tab）
  components/jobs.js        -- loadJobs、renderJobs、renderRuns、showPrompt（Cron Jobs tab）
  components/sessions.js    -- loadSessions、renderSessions、rename、disconnect（Sessions tab）
  components/tools.js       -- loadSkills、loadMcp、loadPlugins、showSkillContent（Tools tab）
  components/modal.js       -- openModal、closePromptModal（共享 Modal 控制）
```

## 配置与资源

- 数据源（外部，只读）：`~/.hermes/cron/jobs.json`、`~/.hermes/cron/output/`、`~/.hermes/state.db`
- 配置文件：`~/.hermes/config.yaml`（读取 model/platforms/mcp_servers）
- 日志输出：`~/Library/Logs/assistant-http/server.log`
- 进程管理：macOS launchd plist（com.niean.assistant-dashboard）
