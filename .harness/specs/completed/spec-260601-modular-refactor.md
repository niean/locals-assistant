# Modular Refactor Design Spec

- 创建时间: 2026-06-01 15:00
- 状态: active
- 任务来源: 将 index.html 中内联的 CSS 和 JS 按照 ITCSS + ES6 Modules 规范完整拆分为独立模块文件

## Goal

将 1024 行的单体 index.html 拆分为 HTML 骨架 + ITCSS 分层 CSS + ES6 Modules JS，实现关注点分离、单一职责、可独立维护。

## Architecture

采用浏览器原生模块加载（无构建步骤）：
- CSS 通过多个 `<link rel="stylesheet">` 按 ITCSS 顺序加载
- JS 通过 `<script type="module" src="js/main.js">` 加载，内部使用 ES6 import/export
- server.py 添加 Starlette `StaticFiles` mount 支持 css/、js/ 目录的静态文件服务

## Components

### CSS 分层（ITCSS）

```
css/
  settings/variables.css      -- CSS Custom Properties（颜色、字号、间距、圆角）
  generic/reset.css           -- box-sizing reset + body 基础样式
  components/tab-nav.css      -- .tab-btn, .tab-content, .subtab-content
  components/stat-card.css    -- .stat-card, .stats-bar
  components/status-panel.css -- .status-panel, .indicator, .status-grid
  components/sessions.css     -- .sessions-table, .source-badge, .id-cell, .title-cell
  components/job-card.css     -- .job-section, .job-header, .job-meta, .runs-table
  components/badges.css       -- .status-badge, .status-dot
  components/modal.css        -- .modal-overlay, .modal, .modal-header, .modal-body
  components/buttons.css      -- .refresh-btn, .prompt-btn, .icon-btn
  utilities/text.css          -- .response-text, .timestamp, .order-link, .empty-state, .last-update
```

### JS 模块

```
js/
  main.js                    -- 应用入口：初始化、事件绑定、auto-refresh
  utils/constants.js         -- API_BASE, REFRESH_INTERVAL
  utils/helpers.js           -- escapeHtml, linkify, formatNumber, toggleResponse
  services/api.js            -- 所有 fetch 封装（loadJobs, loadRuns, loadSessions 等）
  components/overview.js     -- renderOverview, loadStatus
  components/jobs.js         -- renderJobs, renderRuns, showPrompt
  components/sessions.js     -- renderSessions, renderSessionTable, showSessionMessages, rename, disconnect
  components/tools.js        -- renderSkills, renderSkillTable, loadMcp, loadPlugins, showSkillContent
  components/navigation.js   -- switchTab, switchSubTab, getTabFromHash, hash listener
```

### server.py 变更

- 职责：添加 StaticFiles mount，替代手动 homepage 路由
- 接口：`Mount("/", StaticFiles(directory=STATIC_DIR, html=True))`
- 依赖：starlette.staticfiles.StaticFiles

### index.html（重构后）

- 职责：纯 HTML 骨架 + 资源引用（`<link>` + `<script type="module">`）
- 约束：不包含任何内联 `<style>` 或 `<script>` 块（`<script src>` 引用除外）
- 预计行数：约 90-110 行

## Data Flow

1. 浏览器加载 index.html -> 并行请求 css/ 和 js/main.js
2. main.js import 各模块 -> 初始化 tab 路由 + 调用 loadAll()
3. api.js 封装的 fetch 调用 /api/* -> 返回 JSON
4. 各 component 模块接收数据 -> 渲染 DOM
5. setInterval 定时调用 loadAll() 实现自动刷新

## Error Handling

- api.js 中所有 fetch 统一 try/catch，失败时返回 null 或空数据
- 各 component 渲染前检查数据有效性，无效时展示 .empty-state 提示
- 模块加载失败时浏览器控制台报错（ES Module 原生行为），不影响已加载模块

## Constraints

- 零构建步骤：不引入 webpack/vite/rollup
- 浏览器兼容：Safari 15+、Chrome 90+（支持 ES Modules）
- 首屏加载：本地环境，多文件并行加载延迟可忽略
- 向后兼容：API 接口不变，只重构前端文件组织
- BEM 命名：保持现有 class 名不变（已基本符合 BEM 风格），仅提取到独立文件
- CSS 变量：将硬编码颜色/字号提取为 Custom Properties，方便后续主题化
- CSS 加载顺序：index.html 中 `<link>` 标签按 ITCSS 层级顺序排列（settings -> generic -> components -> utilities）
- ITCSS 省略层：tools/ 和 objects/ 层当前无内容，不创建空文件
- 全局状态归属：main.js 持有全局状态（refresh timer ID），各 component 模块为纯渲染函数，不持有跨模块状态
- 路由优先级：server.py 中 API 路由在 StaticFiles mount 之前声明，确保 /api/* 优先匹配

## Acceptance Criteria

- [ ] index.html 不包含任何内联 `<style>` 或超过 10 行的 `<script>` 块
- [ ] CSS 按 ITCSS 分层组织，每个文件单一职责
- [ ] JS 使用 ES6 Module import/export，每个文件不超过 150 行
- [ ] 所有现有功能正常工作（Overview/Cron/Sessions/Tools 四个 tab）
- [ ] server.py 支持 css/、js/ 静态文件服务
- [ ] `python3 -c "import py_compile; py_compile.compile('server.py', doraise=True)"` 通过
- [ ] 浏览器控制台无 JS 错误
